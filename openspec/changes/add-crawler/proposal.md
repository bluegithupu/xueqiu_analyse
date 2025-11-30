# Change: 添加雪球爬虫模块

## Why

项目需要从雪球抓取用户公开内容作为分析数据源。爬虫是整个分析流程的第一步，负责获取原始数据并转换为本地 Markdown 文件。

## What Changes

- 新增 `crawler/client.py`：HTTP 客户端封装，含 cookies 管理、限速、重试
- 新增 `crawler/user_api.py`：雪球用户 API 封装，获取用户资料和文章列表
- 新增 `crawler/tasks.py`：抓取任务入口，将内容转换并存储为 Markdown
- 新增配置文件支持：`config/cookies.json`、`config/settings.yaml`
- 新增数据目录结构：`data/{nickname}/posts/*.md`

## Impact

- Affected specs: `crawler-client`, `crawler-user-api`, `crawler-tasks`
- Affected code: 新增 `crawler/` 目录及其模块
- Dependencies: requests, PyYAML
