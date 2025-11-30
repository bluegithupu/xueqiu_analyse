#
 本文档描述一个完全基于本地文件系统、使用 Markdown 存储数据，并通过 OpenAI 客户端进行综合分析的实现计划。

 ## 一、目标概述
 
 - 抓取雪球某个用户的所有公开文章/动态文本。
 - 将每篇内容转换为 Markdown 文件，按 `./data/{用户昵称}/posts/xxx.md` 组织。
 - 基于本地 Markdown 文件，调用 OpenAI，对该用户的投资风格、投资方法和主要持仓观点进行分析，总结出一份「投资画像报告」。
 
 ## 二、整体架构（无数据库）
 
 数据流：
 
 1. 雪球 -> 爬虫（crawler）-> 原始数据（HTML/JSON）
 2. 解析并转为 Markdown -> 存入 `./data/{昵称}/posts/*.md`
 3. 分析模块从本地 Markdown 读取文本 -> 调用 OpenAI -> 生成画像与报告 Markdown
 
 模块划分：
 
 - `crawler`：负责请求雪球接口/页面，抓取一个用户的全部内容。
 - `storage (文件系统)`：负责把一条条内容转换为 Markdown 文件并写入 `./data/{昵称}/posts/`。
 - `analysis`：从 Markdown 文件读取内容，做文本清洗、分块和多阶段 AI 分析。
 - `reports`：生成最终的用户画像报告（Markdown），存放在 `./reports/`。
 
 ## 三、目录结构设计
 
 项目根目录（简化版）：
 
 - `Plan.md`：当前规划文档。
 - `requirements.txt`：Python 依赖（`requests`、`PyYAML`、`openai` 等）。
 - `config/`
   - `cookies.json`：雪球 cookies（只在本地使用，应 .gitignore）。
   - `settings.yaml`：基础配置，如 UA、请求间隔、OpenAI 模型名等。
 - `data/`
   - `{nickname}/`
     - `posts/`：该用户的所有文章/动态 Markdown。
     - `analysis/`：分析中间结果、缓存（JSON）。
 - `reports/`
   - `{nickname}_{日期}.md`：最终用户画像报告。
 - `crawler/`
   - `client.py`：HTTP 客户端封装（Session、cookies、headers、限速）。
   - `user_api.py`：面向「用户」的抓取接口封装。
   - `tasks.py`：抓取任务入口函数。
 - `analysis/`
   - `prompts.py`：OpenAI 提示词模板。
   - `chunk_summarizer.py`：分块总结。
   - `global_analyser.py`：全局风格/方法分析。
   - `report_builder.py`：报告生成。
   - `pipeline.py`：将整个分析流程串联起来。
 - `scripts/`
   - `crawl_user.py`：命令行入口，按用户抓取数据到 Markdown。
   - `analyse_user.py`：命令行入口，从本地 Markdown 做分析并生成画像报告。
 
 ## 四、Markdown 存储规范
 
 ### 4.1 目录和文件命名
 
 - 对于昵称为 `{nickname}` 的用户：
   - 所有单篇内容存放在：`./data/{nickname}/posts/`
 - 单篇文件命名格式：
   - `{created_at}_{post_id}_{slug}.md`
   - 示例：`2024-11-30_123456789_白酒长期价值.md`
   - 其中：
     - `created_at`：`YYYY-MM-DD` 格式。
     - `post_id`：雪球这一条内容的唯一 ID。
     - `slug`：由标题简单清洗得到，只保留中英文和数字，空格替换为 `_`。
 
 ### 4.2 单篇内容的 Markdown 结构
 
 每篇内容一份 `.md` 文件，采用 YAML frontmatter + 正文结构：
 
 ```md
 ---
 id: 123456789
 user_id: 987654321
 nickname: 价值投资老王
 created_at: 2024-11-30T10:23:45+08:00
 url: https://xueqiu.com/123456789/123456789
 type: long_post          # long_post / short_status / comment 等
 title: 白酒板块的长期价值
 like_count: 120
 comment_count: 45
 repost_count: 8
 symbols:
   - 600519
   - 000858
 raw_tags: [白酒, 消费, 价值投资]
 ---
 
 # 白酒板块的长期价值
 
 （这里是文章正文，已从 HTML 抽取为纯文本，可保留段落和列表）
 
 1. 行业格局分析……
 2. 估值水平……
 3. 持仓思路与风险……
 ```
 
 说明：
 
 - frontmatter 保存结构化元数据，便于分析程序使用 YAML 解析。
 - 正文部分是 AI 直接阅读的内容，保持尽量干净的 Markdown 文本。
 
 ## 五、爬虫设计（crawler）
 
 ### 5.1 技术选型
 
 - 使用 `requests` + `Session` 进行 HTTP 请求。
 - 不做自动登录，直接从浏览器复制雪球 cookies 到 `config/cookies.json`。
 - 若有 JSON API 优先走 JSON；没有则用 HTML 解析（`lxml` 或 `BeautifulSoup`）。
 
 ### 5.2 模块职责
 
 - `crawler/client.py`
   - 负责：
     - 读取 `config/cookies.json`、UA 和基础配置。
     - 管理 `requests.Session`。
     - 提供 `get_json(url, params)`、`get_html(url, params)` 等方法。
     - 统一限速（例如请求间隔 1–2 秒）、重试策略、超时处理。
 
 - `crawler/user_api.py`
   - 负责：
     - `get_user_profile(user_id_or_nick) -> dict`
     - `iter_user_posts(user_id_or_nick, max_pages=None) -> Iterator[dict]`
   - 返回的单条 post `dict` 至少包含：
     - `id`、`user_id`、`nickname`
     - `title`（若有）
     - `content_html` 或已清洗的 `content_text`
     - `created_at`
     - 点赞/评论/转发计数
     - 提到的股票代码列表（若接口/正文中可解析）
 
 - `crawler/tasks.py`
   - 核心函数：`crawl_user_to_markdown(nickname_or_id: str, out_root="./data")`
   - 流程：
     1. 解析/确认该用户的昵称与 ID。
     2. 创建目录 `./data/{nickname}/posts/`。
     3. 使用 `iter_user_posts` 遍历用户所有内容。
     4. 对每条内容：
        - 抽取元数据与正文。
        - 根据规则生成文件名。
        - 渲染为 Markdown 模板并写入文件。
        - 若文件已存在则跳过，实现增量抓取。
 
 ### 5.3 防封与错误处理
 
 - 在 `client.py` 中实现基础限速（例如每次请求后 `sleep` 一小段时间）。
 - 对 4xx/5xx 或网络异常做有限次数重试（指数退避）。
 - 若检测到 cookies 失效或被重定向到登录页：
   - 抛出明确异常，提示用户更新 `cookies.json`。
 
 ### 5.4 增量抓取状态（文件系统方式）
 
 不使用数据库，使用 JSON 文件记录抓取进度：
 
 - 每个用户一个：`./data/{nickname}/crawl_state.json`
 - 结构示例：
 
 ```json
 {
   "last_crawled_post_id": "123456789",
   "last_crawled_at": "2024-11-30T10:23:45+08:00"
 }
 ```
 
 - 启动 `crawl_user_to_markdown` 时：
   - 若存在该文件，则只抓取时间更新后的新内容。
   - 完成后更新该状态文件，便于断点续爬和周期性刷新。
 
 ## 六、AI 分析设计（analysis）
 
 ### 6.1 技术选型
 
 - 使用官方 `openai` Python 客户端。
 - 使用环境变量 `OPENAI_API_KEY` 读取密钥，不写入代码仓库。
 - 模型名称、温度等参数写在 `config/settings.yaml` 中，便于调整。
 
 ### 6.2 分析总体流程
 
 1. **读取数据**  
    - 给定用户昵称 `{nickname}`。
    - 列出 `./data/{nickname}/posts/*.md`，解析 YAML frontmatter 和正文。
    - 按 `created_at` 排序，得到一系列有序文章。
 
 2. **文本分块**  
    - 按时间顺序将多篇文章合并为若干 chunk。
    - 控制单个 chunk 的字数 / token 数在安全范围（例如 2000–3000 汉字）。
    - 每个 chunk 包含若干篇文章的正文和必要的元信息（时间、标题等）。
 
 3. **分块初级总结**（第一轮 OpenAI 调用）  
    - 对每个 chunk 调用模型：
      - 输出：
        - `chunk_summary`：该时段的大致投资观点。
        - `style_signals`：投资风格信号（价值/成长/短线/趋势 等标签）。
        - `methods_signals`：投资方法信号（看估值 / 看技术形态 / 关注基本面 等）。
        - `stock_mentions`：提到的股票代码和上下文简要说明。
    - 中间结果写入：`./data/{nickname}/analysis/chunks.json`。
 
 4. **全局风格与方法归纳**（第二轮 OpenAI 调用）  
    - 读取 `chunks.json`，压缩为更紧凑的描述。
    - 让模型基于全部 chunk 级别的总结，输出：
      - 整体投资风格（可多标签）。
      - 选股和交易方法的归纳描述。
      - 风险偏好和仓位管理特征。
      - 行业/主题偏好。
    - 写入：`./data/{nickname}/analysis/profile.json`。
 
 5. **主要持仓/观点提炼**  
    - 基于 `chunks.json` 中的 `stock_mentions`：
      - 统计出现最频繁、时间跨度较长的股票和行业。
      - 结合模型，判断哪些是“核心关注/核心持仓”。
      - 对每个核心标的，提炼该用户的核心观点与逻辑。
 
 6. **报告生成**  
    - 模块 `report_builder.py`：
      - 读取 `profile.json` 和部分代表性原文片段。
      - 使用统一的 Prompt 生成一份 Markdown 报告。
      - 输出路径：`./reports/{nickname}_{yyyyMMdd}.md`。
 
 ### 6.3 模块职责划分
 
 - `analysis/prompts.py`：存放所有提示词模板。
 - `analysis/chunk_summarizer.py`：负责分块与第一轮总结。
 - `analysis/global_analyser.py`：汇总 chunk 结果，生成全局画像。
 - `analysis/report_builder.py`：根据结构化结果生成 Markdown 报告。
 - `analysis/pipeline.py`：对外暴露 `analyse_user(nickname) -> report_path`。
 
 ## 七、报告结构设计
 
 最终报告（Markdown）建议结构：
 
 1. 简介与摘要
 2. 投资风格画像
 3. 投资方法与决策逻辑
 4. 主要持仓与行业观点
 5. 典型操作案例（成功/失败各若干）
 6. 风险偏好与潜在风险提示
 7. 附录：数据时间范围与样本数量
 
 ## 八、实现顺序与里程碑
 
 1. **实现爬虫基础设施**  
    - 完成 `crawler/client.py`：Session、cookies、限速、基础请求方法。
    - 完成 `crawler/user_api.py` 的最小版本：能列出某用户的若干篇文章。
 
 2. **Markdown 写入逻辑**  
    - 实现 `crawler/tasks.py` 中的 `crawl_user_to_markdown`：
      - 根据单条 post `dict` 渲染 Markdown 模板。
      - 写入 `./data/{nickname}/posts/`。
      - 实现幂等与增量抓取。
 
 3. **最小可用分析流水线**  
    - 先实现一个极简版本：
      - 把全部 Markdown 直接拼成一个大字符串。
      - 用一个 Prompt 让模型输出一个粗糙的用户画像报告。
      - 验证 OpenAI 调用链路和整体效果。
 
 4. **迭代为多阶段分析**  
    - 引入分块策略 `chunk_summarizer`。
    - 增加 `chunks.json` 和 `profile.json` 中间结果存储。
    - 完善报告模板与输出结构。
 
 5. **优化与扩展**  
    - 根据实际调用成本与准确度调整分块大小和提示词。
    - 如有需要，增加对评论、组合、持仓变化记录等信息的抓取和分析。
 
 上述即为当前版本的「雪球用户文章抓取 + 文件系统存储 + OpenAI 分析」的完整计划。