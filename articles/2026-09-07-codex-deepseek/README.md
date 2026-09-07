# Codex 桌面版接入 DeepSeek V4：本篇专属资料

<!-- 版本：v1.0.0 | 更新时间：2026-09-07 | 状态：配置隔离验证及配套自检通过 -->

作者：才哥AGI。文章标识：`codex-deepseek`。

[独立下载本篇 ZIP](https://raw.githubusercontent.com/dxawdc/caige-wechat-articles/main/downloads/codex-deepseek_v1.0.0.zip)。解压后进入 `codex-deepseek_v1.0.0` 文件夹。

## 先运行不联网的自检

Python 3.11+，以下自检只使用标准库：

```powershell
python 运行自检_v1.0.0.py
```

预期：配置检查器的六个用例通过，本地模拟 Responses 请求通过；桌面练习初始三个测试失败，人工参考答案三个测试通过；费用情景 Flash 为 3.9/1.95 元、Pro 为 11.7/5.85 元。完整结果写入 `本地自检输出/`。自检在临时目录执行练习，不修改包内原始练习。

## 本包文件

| 文件 | 作用 |
|---|---|
| `检查配置_v1.0.0.py` | 只读检查 TOML、地址、模型、凭据来源和模型目录；不打印 Key |
| `验证Responses_v1.0.0.py` | 默认只做本地模拟；明确传入 `--online` 才请求 DeepSeek 官方 API |
| `配置结构示例_v1.0.0.toml` | 环境变量鉴权的结构示意，路径必须改，不能直接覆盖用户配置 |
| `桌面练习/` | 故意含三个问题的订单汇总函数、目标测试和桌面任务提示 |
| `参考答案/orders.py` | 人工参考实现，不能当作真实 DeepSeek 输出 |
| `价格情景_v1.0.0.json` | 2026-09-07 官方单价与假设用量，非真实任务账单 |
| `图片/` | 六张图解 PNG 及对应 HTML 源文件；不是软件操作截图 |
| `验证记录/` | 本次隔离配置和配套工具的实际验证范围 |
| `官方来源_v1.0.0.json` | 官方来源链接、核验日期及下载内容校验值，不分发整页正文 |
| `物料清单_v1.0.0.json` | 本篇文件列表、字节数及 SHA-256 |

## 自己检查实际配置

```powershell
python 检查配置_v1.0.0.py --config "$env:USERPROFILE\.codex\config.toml"
```

有自定义 `CODEX_HOME` 时改成实际路径。通过仅代表静态关系符合本教程，不验证 Key 有效性，也不证明另一个桌面进程读到了环境变量。

## 自己执行真实接口验证

```powershell
python 验证Responses_v1.0.0.py --online --model deepseek-v4-flash
```

这一命令会发送一次可能计费的线上请求。Key 从 `DEEPSEEK_API_KEY` 读取，缺失时不回显输入；本包不含真实 Key。返回状态 `completed` 且 `markerReceived=true`，才是本脚本的通过条件。普通文本探测不能证明图片、工具或桌面端整套流程可用。

## 官方配置入口

采用 [DeepSeek 官方 Codex 接入说明](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/)中的当前脚本。本包不自动安装、不修改正在使用的 Codex 配置，不携带未经更新的第三方安装器。先备份已有 `config.toml` 与 `models.json`；当前 Windows 官方脚本的恢复选项会恢复配置并删除模型目录文件，需要单独保存自己的自定义模型目录。

本次实际验证了官方 Windows 脚本 1.2.0 在隔离目录的安装、模型切换和恢复，以及 Codex 引擎 0.153.4 读取生成的模型目录。未提供真实 DeepSeek Key，未完成线上 DeepSeek 对话、桌面工具链或视觉能力测试。不要把占位凭据、自测通过或人工答案描述为真实模型联调成功。

版本说明：v1.0.0 首次提供本篇专属配置检查、接口探测、桌面验收练习、图解和来源记录。
