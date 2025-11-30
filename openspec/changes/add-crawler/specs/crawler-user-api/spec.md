## ADDED Requirements

### Requirement: 获取用户资料

系统 SHALL 提供 `get_user_profile(user_id_or_nick)` 函数，返回用户基本信息。

#### Scenario: 通过用户 ID 获取
- **WHEN** 传入有效的数字用户 ID
- **THEN** 返回包含 `id`、`nickname`、`description` 的 dict

#### Scenario: 通过昵称获取
- **WHEN** 传入用户昵称字符串
- **THEN** 返回该用户的资料 dict

#### Scenario: 用户不存在
- **WHEN** 传入不存在的用户 ID 或昵称
- **THEN** 抛出 `UserNotFoundError`

### Requirement: 迭代用户文章

系统 SHALL 提供 `iter_user_posts(user_id, max_pages=None)` 生成器，按时间倒序迭代用户的所有文章。

#### Scenario: 遍历全部文章
- **WHEN** 不设置 max_pages
- **THEN** 遍历用户的所有公开文章直到末页

#### Scenario: 限制页数
- **WHEN** 设置 max_pages=2
- **THEN** 最多返回 2 页的文章

#### Scenario: 用户无文章
- **WHEN** 用户没有发布任何文章
- **THEN** 生成器不产出任何元素

### Requirement: 文章数据结构

`iter_user_posts` 返回的每条文章 dict SHALL 包含以下字段：

- `id`: 文章唯一 ID
- `user_id`: 作者 ID
- `nickname`: 作者昵称
- `title`: 标题（若有）
- `content_text`: 纯文本正文
- `created_at`: 发布时间 ISO 格式
- `url`: 文章链接
- `type`: 内容类型（long_post / short_status）
- `like_count`: 点赞数
- `comment_count`: 评论数
- `repost_count`: 转发数
- `symbols`: 提到的股票代码列表

#### Scenario: 长文章
- **WHEN** 文章类型为长文
- **THEN** `type` 为 `long_post`，`title` 非空

#### Scenario: 短动态
- **WHEN** 内容类型为短动态
- **THEN** `type` 为 `short_status`，`title` 可为空

### Requirement: 内容解析

系统 SHALL 从 HTML 或 JSON 响应中提取纯文本正文，移除 HTML 标签和脚本。

#### Scenario: HTML 内容
- **WHEN** 原始内容包含 HTML 标签
- **THEN** `content_text` 为清洗后的纯文本，保留段落结构

#### Scenario: 股票代码提取
- **WHEN** 正文中提及股票（如 $贵州茅台$ 或 SH600519）
- **THEN** `symbols` 列表包含对应代码
