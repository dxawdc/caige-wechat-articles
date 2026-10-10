# 平台接入与维护

初次整理日期：2026-10-10。执行任务时重新核对变化，不把本文额度作为永久合同。

## 免费用途与成本

- GitHub Free 支持公开/私有仓库。新项目由用户决定可见性，默认不要公开既有私有内容。
- Vercel Hobby 面向个人非商业用途；商业、广告、收费等场景先核对 fair use，不能默认免费兼容。默认网址可以先用，域名注册费单算。
- Supabase Free 当前为 500 MB 数据库、1 GB Storage、5 GB egress + 5 GB cached egress、最多 2 个活跃项目；一周不活跃项目会暂停。数据库、文件存储、流量是不同计量项，别把 API 请求不限量理解为容量无限。
- Cloudflare DNS 可用 Free 方案；代理、Workers、R2、Images 是不同产品，使用时分别核对额度，不能用 DNS 免费证明其他产品无限。
- AI 工具订阅和域名购买另计。免费托管不保证所有地区的访问质量。

官方入口：
- https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories
- https://vercel.com/docs/plans/hobby
- https://vercel.com/docs/limits/fair-use-guidelines
- https://supabase.com/pricing
- https://developers.cloudflare.com/dns/

## Supabase

先辨认新空库还是已有生产项目。数据库区域考虑访问者和函数所在区域。建立受版本管理的完整 schema 与权限，不把业务项目的历史 SQL 按文件名盲跑。

入口可能更新，按当前控制台给用户定位：SQL Editor 执行审核后的脚本；Table Editor 验证数据/导入 CSV；Storage 管理桶；Authentication → Users 创建第一位管理员账户；Connect 或 Settings → API Keys 获取连接信息。

需要应用角色表时，游客及普通用户不得自行插入或修改管理员记录。仅一个管理员的小站可以用服务端用户 ID 白名单；RLS 策略与该方案必须一致，避免接口认可管理员而数据库策略无权，或反过来。

直接访问 Data API 时同时检查 schema 暴露设置、表级 GRANT 和 RLS。缺权限不能通过全面开放来掩盖。公开资料使用发布状态；管理数据与公开字段分离。

新的 publishable key 可以进入公开客户端，但并不替代 RLS。secret key 仅受信服务端使用，并绕过 RLS；旧 service_role 具有同类风险。高权限数据库客户端不混用登录会话。

Supabase Auth 登录验证通过服务端可信方法进行，例如 SDK 的 getUser(accessToken)；不能只读取未校验 JWT 内容。Auth 的 user_metadata 可由用户改变，不能用于授权。会话退出/过期应有明确 UI 与拒绝行为。

小数据 CSV 导入先验证字段、中文编码、日期、布尔类型和唯一性。大数据分批并记录成功/失败，采用可重试且有唯一键约束的策略。图库压缩、分页、索引与缓存按实际规模选择，不虚构承载量。

官方入口：
- https://supabase.com/changelog.md （失败时 https://supabase.com/changelog）
- https://supabase.com/docs/guides/getting-started/api-keys
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://supabase.com/docs/guides/api/securing-your-api
- https://supabase.com/docs/guides/auth/managing-user-data
- https://supabase.com/docs/reference/javascript/auth-getuser
- https://supabase.com/docs/guides/storage/security/access-control
- https://supabase.com/docs/guides/database/import-data
- https://supabase.com/docs/guides/platform/backups

## GitHub 与 Vercel

先检查远端仓库和分支，保护无关改动。仅选择任务相关文件提交，检查完整 diff 与秘密泄露。已接入 Vercel 的生产分支可能自动部署，推送前辨认这一后果。

从 Vercel 导入确切仓库，核对 Root Directory、Framework Preset、Install/Build Command 和 Output Directory；根据项目实际填写。Node 函数部署和 Cloudflare Worker 是不同运行方式，不互换入口。

配置 Production 与 Preview 环境变量。Preview 优先使用测试数据，别用预览验收删除生产记录。环境变量修改后需要新部署读取，不把配置保存视为已更新运行实例。

首次上线先查默认域名。检查 HTTP 状态、页面标识、静态资源、公开接口及后台权限。SPA fallback 返回 HTML 200 不能算 API 成功；同时核对 content-type 和实际 JSON。

官方入口：
- https://vercel.com/docs/git
- https://vercel.com/docs/deployments
- https://vercel.com/docs/environment-variables
- https://vercel.com/docs/functions

## Cloudflare 可选域名

无域名跳过，交付默认地址。已有域名先查当前 DNS 和已有服务，再添加 zone 或复用已有 zone。采用 Full setup 时将注册商 NS 改为 Cloudflare 对该域名提供的值，不抄其他域名的 NS。

Vercel 项目先添加自定义域名，再根据其当前推荐配置 DNS；需要 TXT 验证时按实际显示执行，不硬编码旧 A/CNAME 值。首次默认 DNS only，分别验证域名、HTTPS 和页面响应。根域名与 www 选规范地址并配置跳转。

Vercel 官方不推荐在前面叠加反向代理。若用户实际需要代理，说明额外缓存和防护兼容问题；核对证书与完整 TLS 路径，不默认启用宽泛缓存。DNS only 不提供 Cloudflare 代理层缓存和 HTTP 防护。

图片代理仅当有真实需求再实现，固定允许源站和路径，不做可转发任意 URL 的开放代理；私人文件不能当公共封面缓存。

官方入口：
- https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/
- https://developers.cloudflare.com/dns/proxy-status/
- https://vercel.com/docs/domains/working-with-domains/add-a-domain
- https://vercel.com/kb/guide/cloudflare-with-vercel
