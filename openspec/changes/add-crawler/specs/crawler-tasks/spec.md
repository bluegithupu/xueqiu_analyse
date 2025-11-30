## ADDED Requirements

### Requirement: 抓取用户内容到 Markdown

系统 SHALL 提供 `crawl_user_to_markdown(nickname_or_id, out_root="./data")` 函数，将用户全部文章保存为 Markdown 文件。

#### Scenario: 首次抓取
- **WHEN** 目标用户目录不存在
- **THEN** 创建 `{out_root}/{nickname}/posts/` 目录，抓取并保存所有文章

#### Scenario: 增量抓取
- **WHEN** 目标用户已有抓取记录
- **THEN** 只抓取新发布的文章

### Requirement: Markdown 文件格式

每篇文章 SHALL 保存为独立的 `.md` 文件，包含 YAML frontmatter 和正文。

#### Scenario: 文件结构
- **WHEN** 保存一篇文章
- **THEN** 文件包含：
  - YAML frontmatter：id, user_id, nickname, created_at, url, type, title, like_count, comment_count, repost_count, symbols, raw_tags
  - 正文：Markdown 格式的文章内容

### Requirement: 文件命名规则

文件名 SHALL 遵循格式：`{YYYY-MM-DD}_{post_id}_{slug}.md`

#### Scenario: 正常命名
- **WHEN** 文章标题为「白酒板块的长期价值」，ID 为 123456，日期为 2024-11-30
- **THEN** 文件名为 `2024-11-30_123456_白酒板块的长期价值.md`

#### Scenario: 标题清洗
- **WHEN** 标题包含特殊字符（如 `/`、`\`、`:`）
- **THEN** 特殊字符被移除或替换，确保文件名合法

#### Scenario: 无标题
- **WHEN** 短动态没有标题
- **THEN** 使用正文前 20 字作为 slug

### Requirement: 幂等写入

系统 SHALL 在文件已存在时跳过写入，实现幂等操作。

#### Scenario: 文件已存在
- **WHEN** 目标 Markdown 文件已存在
- **THEN** 跳过该文章，不覆盖

### Requirement: 抓取状态管理

系统 SHALL 使用 `crawl_state.json` 文件记录抓取进度。

#### Scenario: 记录进度
- **WHEN** 完成一次抓取
- **THEN** 更新 `{out_root}/{nickname}/crawl_state.json`，包含 `last_crawled_post_id` 和 `last_crawled_at`

#### Scenario: 读取进度
- **WHEN** 启动抓取时状态文件存在
- **THEN** 从记录的位置继续，跳过已抓取的文章

### Requirement: 错误处理

系统 SHALL 在遇到错误时记录日志并继续处理下一篇文章。

#### Scenario: 单篇解析失败
- **WHEN** 某篇文章解析失败
- **THEN** 记录错误日志，继续处理其他文章

#### Scenario: Cookies 失效
- **WHEN** 检测到 cookies 失效
- **THEN** 停止抓取，提示用户更新 cookies，保存当前进度
