## ADDED Requirements

### Requirement: 用户文章加载

系统 SHALL 加载用户所有 Markdown 文章并拼接为完整上下文。

#### Scenario: 加载成功
- **WHEN** 给定用户昵称且 `data/{nickname}/posts/` 存在 Markdown 文件
- **THEN** 系统解析所有文章（frontmatter + 正文）
- **AND** 按时间顺序拼接为单个上下文
- **AND** 每篇文章标注文件路径用于后续引用

#### Scenario: 无文章处理
- **WHEN** 给定用户昵称但 `data/{nickname}/posts/` 为空
- **THEN** 系统抛出明确错误提示

---

### Requirement: 单次 AI 分析

系统 SHALL 将所有文章一次性发送给 OpenAI，生成完整投资画像报告。

#### Scenario: 分析成功
- **WHEN** 调用 `analyse_user(nickname)`
- **THEN** 系统加载用户所有文章
- **AND** 单次调用 OpenAI API 生成投资画像报告
- **AND** 报告包含：简介摘要、投资风格、投资方法、主要持仓、典型案例、风险提示
- **AND** 报告中包含原始 Markdown 文档的引用链接

#### Scenario: Token 超限
- **WHEN** 文章总量超过模型上下文限制
- **THEN** 系统抛出明确错误提示，建议用户减少文章数量或使用更大上下文模型

---

### Requirement: 报告文档引用

系统 SHALL 在报告中包含原始 Markdown 文档的引用链接。

#### Scenario: 引用格式
- **WHEN** 报告引用某篇文章观点
- **THEN** 使用相对路径链接格式 `[标题](../data/{nickname}/posts/xxx.md)`
- **AND** 在报告末尾附录列出所有引用文档

---

### Requirement: 报告保存

系统 SHALL 将生成的报告保存为 Markdown 文件。

#### Scenario: 保存成功
- **WHEN** 分析完成
- **THEN** 保存报告到 `reports/{nickname}_{YYYYMMDD}.md`
- **AND** 返回报告文件路径

---

### Requirement: OpenAI 配置管理

系统 SHALL 从环境变量和配置文件读取 OpenAI 相关设置。

#### Scenario: 配置加载
- **WHEN** 系统初始化
- **THEN** 从 `OPENAI_API_KEY` 环境变量读取 API Key
- **AND** 从 `config/settings.yaml` 读取模型名称、temperature、max_tokens

#### Scenario: API Key 缺失
- **WHEN** `OPENAI_API_KEY` 环境变量未设置
- **THEN** 系统抛出明确错误提示

---

### Requirement: 命令行入口

系统 SHALL 提供命令行工具执行用户分析。

#### Scenario: CLI 执行
- **WHEN** 执行 `python scripts/analyse_user.py <nickname>`
- **THEN** 系统对指定用户执行完整分析流程
- **AND** 输出进度信息
- **AND** 完成后打印报告路径
