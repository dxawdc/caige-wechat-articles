"""Collect Eastmoney board history through a phone browser on the same hotspot LAN.

Run this on the PC, then open the printed LAN URL on the phone. The phone
fetches Eastmoney's public JSON endpoint; this server validates and stores the
30 original daily series before writing the checked combined CSV.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import secrets
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from prepare_data import API, AS_OF, CALENDAR_SOURCE, DATA, FIRST, OUT, calendar, import_csvs, themes, validate

RAW = DATA / "原始日线"
PAIRS = themes()
NAMES = dict(PAIRS)
DAYS = calendar()
DAY_SET = set(DAYS)
TOKEN = secrets.token_urlsafe(24)
LOCK = threading.Lock()

PAGE = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>A股 30 板块日线采集</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:720px;margin:28px auto;padding:0 18px;background:#f6f7fa;color:#17212f}h1{font-size:24px}button{font:inherit;border:0;border-radius:10px;background:#1b65cc;color:white;padding:12px 22px}button:disabled{opacity:.5}pre{white-space:pre-wrap;background:white;border-radius:12px;padding:16px;max-height:62vh;overflow:auto}small{color:#59677c}</style>
<h1>A股 30 板块日线采集</h1>
<p>保持此页面打开。点击开始后，手机将逐个读取东方财富历史日线，并传回同一热点下的电脑。完成时显示“30/30，已校验”。</p>
<button id="start">开始采集</button> <span id="count"></span>
<pre id="log">等待开始。</pre>
<small>来源：东方财富 BK 概念板块日 K；范围：__FIRST__ 至 __AS_OF__；不复权。</small>
<script>
const boards = __BOARDS__;
const token = __TOKEN__;
const endpoint = __API__;
const log = document.querySelector('#log');
const count = document.querySelector('#count');
const start = document.querySelector('#start');
function note(message){ log.textContent += '\n' + message; log.scrollTop = log.scrollHeight; }
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function call(path, body){
  const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json','X-Collector-Token':token}, body:JSON.stringify(body)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || '电脑端拒绝了数据');
  return result;
}
async function collect(code, name){
  const params = new URLSearchParams({secid:'90.'+code,klt:'101',fqt:'0',beg:'__BEG__',end:'__END__',lmt:'2000',fields1:'f1,f2,f3,f4,f5,f6',fields2:'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'});
  for(let attempt=1;attempt<=4;attempt++){
    try{
      const response = await fetch(endpoint+'?'+params.toString(), {cache:'no-store'});
      if(!response.ok) throw new Error('东方财富 HTTP '+response.status);
      const data = await response.json();
      const result = await call('/ingest',{code,data});
      note(name+' '+code+'：'+result.rows+' 日 ✓');
      return;
    }catch(error){
      note(name+' 第 '+attempt+' 次失败：'+error.message);
      if(attempt===4) throw error;
      await sleep(attempt*2500);
    }
  }
}
start.onclick = async () => {
  start.disabled = true; log.textContent = '开始采集…';
  try{
    let status = await (await fetch('/status')).json();
    for(const [code,name] of boards){
      if(!status.saved.includes(code)) await collect(code,name);
      status = await (await fetch('/status')).json();
      count.textContent = status.saved.length+'/30';
      await sleep(700);
    }
    const result = await call('/finalize',{});
    note('完成：30/30，已校验 '+result.rows+' 条日线。电脑可开始制作视频。');
  }catch(error){ note('采集中断：'+error.message+'。保持网络后可再次点击开始，已保存板块会跳过。'); }
  start.disabled = false;
};
</script></html>"""


def checked_lines(code: str, payload: dict) -> list[dict[str, str]]:
    if code not in NAMES or payload.get("rc") != 0:
        raise ValueError(f"板块或接口状态错误：{code}")
    board = payload.get("data") or {}
    if board.get("code") != code or not isinstance(board.get("klines"), list):
        raise ValueError(f"板块代码或日线格式错误：{code}")
    result = []
    seen = set()
    for line in board["klines"]:
        fields = line.split(",")
        if len(fields) < 3 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fields[0]):
            raise ValueError(f"日线格式错误：{code}")
        day = fields[0]
        if day not in DAY_SET or day in seen:
            raise ValueError(f"日期越界或重复：{code} {day}")
        close = float(fields[2])
        if not math.isfinite(close) or close <= 0:
            raise ValueError(f"收盘点位错误：{code} {day}")
        seen.add(day)
        result.append({"date": day, "code": code, "close": f"{close:.6f}"})
    result.sort(key=lambda row: row["date"])
    if not result or result[-1]["date"] != AS_OF:
        raise ValueError(f"未更新至 {AS_OF}：{code}")
    expected = [day for day in DAYS if result[0]["date"] <= day <= AS_OF]
    if [row["date"] for row in result] != expected:
        raise ValueError(f"交易日不连续：{code}，实有 {len(result)}，应有 {len(expected)}")
    return result


def save_board(code: str, payload: dict) -> int:
    rows = checked_lines(code, payload)
    RAW.mkdir(parents=True, exist_ok=True)
    target = RAW / f"{code}.csv"
    temp = target.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("date", "code", "close"))
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(target)
    return len(rows)


def saved_codes() -> list[str]:
    return [code for code, _ in PAIRS if (RAW / f"{code}.csv").exists()]


def finalize() -> int:
    if len(saved_codes()) != 30:
        raise ValueError(f"仅有 {len(saved_codes())}/30 个板块")
    rows = validate(import_csvs(RAW), NAMES, DAYS)
    DATA.mkdir(exist_ok=True)
    temp = OUT.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("date", "code", "name", "close"))
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(OUT)
    (DATA / "行情元数据.json").write_text(json.dumps({
        "source": API,
        "source_type": "Eastmoney daily K-line fetched in phone browser over hotspot",
        "adjustment": "unadjusted (fqt=0)",
        "calendar_source": str(CALENDAR_SOURCE),
        "first_reference_date": FIRST,
        "last_verified_date": AS_OF,
        "trading_days": len(DAYS),
        "boards": len(PAIRS),
        "rows": len(rows),
        "captured_at": date.today().isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(rows)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/status":
            self.send_json(200, {"saved": saved_codes(), "complete": OUT.exists()})
        elif route == "/":
            body = (PAGE.replace("__BOARDS__", json.dumps(PAIRS, ensure_ascii=False))
                    .replace("__TOKEN__", json.dumps(TOKEN))
                    .replace("__API__", json.dumps(API))
                    .replace("__FIRST__", FIRST).replace("__AS_OF__", AS_OF)
                    .replace("__BEG__", FIRST.replace("-", ""))
                    .replace("__END__", AS_OF.replace("-", ""))).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.headers.get("X-Collector-Token") != TOKEN:
            self.send_json(403, {"error": "无效采集会话"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2_000_000:
                raise ValueError("请求长度错误")
            request = json.loads(self.rfile.read(length))
            with LOCK:
                route = urlparse(self.path).path
                if route == "/ingest":
                    code = request["code"]
                    count = save_board(code, request["data"])
                    self.send_json(200, {"code": code, "rows": count})
                elif route == "/finalize":
                    self.send_json(200, {"rows": finalize()})
                else:
                    self.send_error(404)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="Hotspot-facing PC address")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Phone collector ready: http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
