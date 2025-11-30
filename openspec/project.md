# Project Context

## Purpose
雪球用户投资分析工具：抓取雪球用户公开文章/动态，存储为本地 Markdown，通过 OpenAI 生成投资画像报告。

## Tech Stack
- Python 3.10+
- requests (HTTP 客户端)
- PyYAML (配置解析)
- lxml / BeautifulSoup (HTML 解析)
- openai (AI 分析)

## Project Conventions

### Code Style
- 精简代码，避免冗余
- 类型注解
- 函数单一职责

### Architecture Patterns
- 模块化：crawler / analysis / reports
- 无数据库，纯文件系统存储
- Markdown + YAML frontmatter 格式

### Testing Strategy
- 单元测试覆盖核心逻辑
- 集成测试验证端到端流程

### Git Workflow
- main 分支保持稳定
- 功能分支开发

## Domain Context
- 雪球：国内投资社区平台
- 目标：分析用户投资风格、方法、持仓观点
- 数据来源：用户公开文章、动态

## Important Constraints
- 不自动登录，手动复制 cookies
- 请求限速防封
- OpenAI API Key 通过环境变量配置

## External Dependencies
- 雪球 API/页面
- OpenAI API
