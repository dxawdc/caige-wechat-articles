# -*- coding: utf-8 -*-
"""通过微信公众号官方 API 保存当前文章草稿；只输出脱敏状态，不发布或群发。

- 上传正文图片（media/uploadimg）→ 处理封面 → draft/add 或 draft/update；
- 回执落盘，记录 media_id 与图片 URL 映射；重跑时先按标题查重，命中则走 draft/update；
- 回读验证标题、作者、全文、代码与图片可达性；
- 若后台编辑器里已换过封面（thumb 与本地封面不一致），沿用草稿当前封面并备份到 输出/，
  不用本地旧封面覆盖用户的修改。
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from pathlib import Path
import io
import importlib.util
import json
import mimetypes
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from lxml import html
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent
ARTICLE_HTML = ROOT / "公众号正文_v1.0.0.html"
RECEIPT = ROOT / "公众号草稿回执_v1.0.0.json"
TITLE = "黄金白银这10年：从上金所到周大福柜台，我用公开数据把价格画明白了"
DIGEST = ("近10年黄金涨2.3倍、白银涨2.5倍；2026年1月底集体见顶后白银回撤超四成。"
          "我用公开接口采集上海黄金交易所、国际金银和6家金店近两年挂牌价，"
          "采集过程、清洗过程和9张图全部公开。")
SOURCE_URL = "https://github.com/dxawdc/caige-wechat-articles/tree/main/articles/2026-09-19-precious-metals"
AUTHOR = "才哥AGI"
COVER = ROOT / "配图" / "封面_v1.0.1.jpg"  # 作者在后台替换后的封面；本地缺失时自动沿用草稿封面


class WeChatApiError(RuntimeError):
    def __init__(self, stage: str, payload: dict):
        self.stage = stage
        self.errcode = payload.get("errcode")
        self.errmsg = payload.get("errmsg")
        super().__init__(f"{stage}: errcode={self.errcode} {self.errmsg}")


def load_credentials() -> tuple[str, str]:
    legacy_loader = Path(r"D:\公众号文章\公众号API接入_v1.0.0\验证公众号API_v1.0.0.py")
    spec = importlib.util.spec_from_file_location("caige_wechat_credential_loader", legacy_loader)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.load_credentials()


def fetch_token(appid: str, secret: str) -> str:
    body = json.dumps({"grant_type": "client_credential", "appid": appid,
                       "secret": secret, "force_refresh": False}).encode()
    request = urllib.request.Request("https://api.weixin.qq.com/cgi-bin/stable_token",
                                     data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.loads(response.read().decode("utf-8"))
    if "access_token" not in value:
        raise WeChatApiError("token", value)
    return value["access_token"]


def api_call(token: str, endpoint: str, *, payload: dict | None = None,
             file: tuple[str, bytes, str] | None = None, params: dict | None = None) -> dict:
    import http.client
    import time
    query = {"access_token": token, **(params or {})}
    url = f"https://api.weixin.qq.com/cgi-bin/{endpoint}?{urllib.parse.urlencode(query)}"
    if file is None:
        raw = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=raw,
                                         headers={"Content-Type": "application/json; charset=utf-8"})
    else:
        filename, data, content_type = file
        boundary = "----CaigeWechatDraftBoundary"
        raw = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; "
            f"filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode()
            + data + f"\r\n--{boundary}--\r\n".encode()
        )
        request = urllib.request.Request(url, data=raw,
                                         headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    last_error: Exception | None = None
    value = {}
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                value = json.loads(response.read().decode("utf-8"))
            last_error = None
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                OSError, http.client.IncompleteRead) as error:
            last_error = error
            if attempt < 2:
                time.sleep(1 + attempt)
    if last_error is not None:
        raise RuntimeError(f"{endpoint}: transport_error={type(last_error).__name__}") from last_error
    if value.get("errcode") not in (None, 0):
        raise WeChatApiError(endpoint, value)
    return value


def upload_payload(name: str, raw: bytes) -> tuple[str, bytes, str]:
    if name.lower().endswith(".gif"):
        return name, raw, "image/gif"  # 动图不能转 JPEG，失败时由调用方兜底
    if len(raw) < 1_950_000:
        return name, raw, mimetypes.guess_type(name)[0] or "image/png"
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im.thumbnail((4000, 4000), Image.Resampling.LANCZOS)
    for quality in (95, 90, 85, 80, 75):
        buffer = io.BytesIO()
        im.save(buffer, format="JPEG", quality=quality, optimize=True, subsampling=0)
        if buffer.tell() < 1_950_000:
            return Path(name).stem + ".jpg", buffer.getvalue(), "image/jpeg"
    raise RuntimeError("image_exceeds_upload_budget")


def upload_file(path: Path) -> tuple[str, bytes, str]:
    return upload_payload(path.name, path.read_bytes())


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def pixel_error(raw_a: bytes, raw_b: bytes) -> float:
    """两图缩到 320 宽后的平均像素差，<8 视为同一张图（微信会重新编码）。"""
    def load(raw: bytes) -> Image.Image:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        return im.resize((320, max(1, round(320 * im.height / im.width))), Image.Resampling.BILINEAR)
    image_a, image_b = load(raw_a), load(raw_b)
    if image_a.size != image_b.size:
        image_b = image_b.resize(image_a.size, Image.Resampling.BILINEAR)
    return sum(ImageStat.Stat(ImageChops.difference(image_a, image_b)).mean) / 3


def record(value: dict) -> None:
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(RECEIPT)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def main() -> None:
    stage = "prepare"
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.is_file() else {}
    try:
        document = html.fragment_fromstring(ARTICLE_HTML.read_text(encoding="utf-8"), create_parent="section")
        images = document.xpath(".//img")
        if not images:
            raise RuntimeError("no_article_images")
        article_hash = sha256(ARTICLE_HTML.read_bytes()).hexdigest()
        content_chars = len(html.tostring(document, encoding="unicode"))
        expected_text = normalize(document.text_content())
        expected_code = [p.text_content() for p in document.xpath(".//pre")]

        paths = []
        for im in images:
            path = (ROOT / urllib.parse.unquote(im.get("src", ""))).resolve()
            if ROOT not in path.parents or not path.is_file():
                raise RuntimeError(f"invalid_local_image: {im.get('src')}")
            paths.append(path)

        appid, secret = load_credentials()
        stage = "token"
        token = fetch_token(appid, secret)
        del secret

        stage = "check_existing_draft"
        if not receipt.get("media_id"):
            offset, candidates = 0, []
            while True:
                batch = api_call(token, "draft/batchget",
                                 payload={"offset": offset, "count": 20, "no_content": 0})
                items = batch.get("item", [])
                for item in items:
                    articles = item.get("content", {}).get("news_item", [])
                    if any(a.get("title") == TITLE for a in articles):
                        if len(articles) != 1 or articles[0].get("author") != AUTHOR \
                                or articles[0].get("content_source_url") != SOURCE_URL:
                            raise RuntimeError("existing_title_requires_manual_review")
                        candidates.append(item["media_id"])
                offset += len(items)
                if not items or offset >= batch.get("total_count", offset):
                    break
            if len(candidates) > 1:
                raise RuntimeError("multiple_existing_drafts")
            if candidates:
                receipt["media_id"] = candidates[0]

        cached = {item["file"]: item for item in receipt.get("content_images", [])}
        image_mapping = []
        stage = "upload_content_images"
        for index, (image, source) in enumerate(zip(images, paths), 1):
            path = source
            animated_gif = None
            digest = sha256(path.read_bytes()).hexdigest()
            previous = cached.get(path.name)
            if previous and previous.get("sha256") == digest and previous.get("url"):
                url = previous["url"]  # 图片未变直接复用，避免重复上传（含 4MB 动图）
            elif path.suffix.lower() == ".gif":
                static = path.with_name(path.stem + "_末帧.png")
                if not static.is_file():
                    raise RuntimeError(f"missing_gif_static_fallback: {static.name}")
                try:
                    url = api_call(token, "media/uploadimg", file=upload_file(path))["url"]
                except WeChatApiError as error:
                    # uploadimg 官方口径仅支持 jpg/png 且 ≤1MB，动图改传末帧静态图兜底
                    print(json.dumps({"stage": "gif_fallback_to_static", "gif": path.name,
                                      "api_errcode": error.errcode}, ensure_ascii=False), flush=True)
                    path, animated_gif = static, source.name
                    digest = sha256(path.read_bytes()).hexdigest()
                    url = api_call(token, "media/uploadimg", file=upload_file(path))["url"]
            else:
                url = api_call(token, "media/uploadimg", file=upload_file(path))["url"]
            image.set("src", url)
            entry = {"order": index, "file": path.name, "sha256": digest, "url": url}
            if animated_gif:
                entry["animated_gif"] = animated_gif
            image_mapping.append(entry)

        stage = "resolve_cover"
        # 先看草稿当前封面：若用户已在后台替换，则沿用，绝不用本地旧封面覆盖
        draft_now = None
        remote_url, remote_raw, thumb_now = "", b"", ""
        if receipt.get("media_id"):
            draft_now = api_call(token, "draft/get",
                                 payload={"media_id": receipt["media_id"]})["news_item"][0]
            thumb_now = draft_now.get("thumb_media_id") or ""
            remote_url = (draft_now.get("thumb_url") or "").replace("http://", "https://")
            if remote_url:
                remote_raw = download(remote_url)
                backup = ROOT / "输出" / "草稿当前封面_备份.jpg"
                backup.parent.mkdir(exist_ok=True)
                backup.write_bytes(remote_raw)
        local_cover_raw = COVER.read_bytes() if COVER.is_file() else b""
        cover_preserved = bool(remote_raw) and (not local_cover_raw
                                                or pixel_error(remote_raw, local_cover_raw) >= 8)
        if cover_preserved:
            if thumb_now:
                cover_id = thumb_now
            else:
                cover_id = api_call(token, "material/add_material",
                                    file=upload_payload("封面_沿用草稿.jpg", remote_raw),
                                    params={"type": "image"})["media_id"]
            expected_cover = remote_raw
            receipt["cover_preserved"] = {"thumb_url": remote_url, "media_id": cover_id,
                                          "sha256": sha256(remote_raw).hexdigest()}
            print(json.dumps({"stage": "cover_preserved_from_draft",
                              "thumb_url": remote_url[:80]}, ensure_ascii=False), flush=True)
        else:
            if not local_cover_raw:
                raise RuntimeError("local_cover_missing_and_draft_cover_absent")
            cover_digest = sha256(local_cover_raw).hexdigest()
            if receipt.get("cover", {}).get("sha256") == cover_digest and receipt.get("cover", {}).get("media_id"):
                cover_id = receipt["cover"]["media_id"]
            else:
                cover = api_call(token, "material/add_material", file=upload_file(COVER), params={"type": "image"})
                cover_id = cover["media_id"]
                receipt["cover"] = {"sha256": cover_digest, "media_id": cover_id}
            expected_cover = local_cover_raw

        content = html.tostring(document, encoding="unicode")
        article = {
            "article_type": "news",
            "title": TITLE,
            "author": AUTHOR,
            "digest": DIGEST,
            "content": content,
            "content_source_url": SOURCE_URL,
            "thumb_media_id": cover_id,
            "show_cover_pic": 0,
        }
        if draft_now is not None:
            # 后台已开启的评论等开关不因本次更新被重置
            for key in ("need_open_comment", "only_fans_can_comment"):
                if draft_now.get(key) is not None:
                    article[key] = draft_now[key]

        stage = "draft_add_or_update"
        if receipt.get("media_id"):
            media_id = receipt["media_id"]
            api_call(token, "draft/update", payload={"media_id": media_id, "index": 0, "articles": article})
            action = "updated_existing"
        else:
            receipt.update(create_requested=True, readback_verified=False, published=False, title=TITLE)
            record(receipt)
            result = api_call(token, "draft/add", payload={"articles": [article]})
            media_id = result["media_id"]
            action = "created_new"
        receipt.update(media_id=media_id, action=action, draft_saved=True, article_hash=article_hash,
                       content_chars=len(content), content_images=image_mapping, readback_verified=False)
        record(receipt)
        print(json.dumps({"stage": "draft_saved", "action": action,
                          "content_chars": receipt["content_chars"]}, ensure_ascii=False), flush=True)

        stage = "readback"
        saved = api_call(token, "draft/get", payload={"media_id": media_id})["news_item"][0]
        saved_document = html.fragment_fromstring(saved["content"], create_parent="section")
        saved_urls = [item.get("data-src") or item.get("src") for item in saved_document.xpath(".//img")]
        if saved.get("title") != TITLE or saved.get("author") != AUTHOR \
                or len(saved_urls) != len(paths) or not all(saved_urls):
            raise RuntimeError("readback_verification_failed")
        if normalize(saved_document.text_content()) != expected_text:
            raise RuntimeError("readback_full_text_mismatch")
        if [p.text_content().replace("\xa0", " ") for p in saved_document.xpath(".//pre")] \
                != [s.replace("\xa0", " ") for s in expected_code]:
            raise RuntimeError("readback_code_mismatch")
        saved_cover_url = (saved.get("thumb_url") or "").replace("http://", "https://")
        if not saved_cover_url:
            raise RuntimeError("readback_cover_missing")
        if pixel_error(download(saved_cover_url), expected_cover) >= 8:
            raise RuntimeError("readback_cover_changed")

        stage = "verify_remote_images"
        errors = []
        for index, (url, path) in enumerate(zip(saved_urls, paths)):
            parsed = urllib.parse.urlparse(url)
            if parsed.hostname not in ("mmbiz.qpic.cn", "mmbiz.qlogo.cn"):
                raise RuntimeError("unexpected_image_host")
            secure_url = urllib.parse.urlunparse(parsed._replace(scheme="https"))
            with urllib.request.urlopen(urllib.request.Request(secure_url, headers={"User-Agent": "Mozilla/5.0"}),
                                        timeout=30) as response:
                remote = Image.open(io.BytesIO(response.read())).convert("RGB")
            original = Image.open(path).convert("RGB")
            size = (320, max(1, round(320 * original.height / original.width)))
            error = sum(ImageStat.Stat(ImageChops.difference(original.resize(size),
                                                             remote.resize(size))).mean) / 3
            if error >= 8:
                raise RuntimeError("readback_image_pixels_mismatch")
            errors.append(round(error, 4))
            image_mapping[index]["readback_url"] = url

        receipt.update({
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "action": action,
            "media_id": media_id,
            "article_hash": article_hash,
            "title": TITLE,
            "author": AUTHOR,
            "content_chars": len(content),
            "content_images": image_mapping,
            "published": False,
            "readback_verified": True,
            "full_text_verified": True,
            "code_blocks_verified": len(expected_code),
            "image_mean_errors": errors,
            "cover_verified": True,
            "cover_preserved": cover_preserved,
        })
        record(receipt)
        print(json.dumps({"status": "success", "action": action, "title": TITLE,
                          "images": len(paths), "content_chars": len(content),
                          "cover": "preserved_from_draft" if cover_preserved else "local",
                          "published": False, "readback_verified": True}, ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"status": "failed", "stage": stage,
                          "error_type": type(error).__name__,
                          "api_errcode": getattr(error, "errcode", None),
                          "errmsg": getattr(error, "errmsg", None),
                          "published": False}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
