# Proposal: add-crawl-mode

## Summary

新增爬虫模式配置，区分抓取内容类型：
- **默认模式（column）**：仅抓取用户专栏长文
- **全量模式（timeline）**：抓取用户所有动态

## Motivation

当前爬虫抓取用户全部动态，包含大量短状态（如评论、转发）。对于投资分析场景，专栏长文更有价值，短状态噪音较大。

## Scope

- 新增 `crawl.mode` 配置项
- 修改 `iter_user_posts` 支持按类型过滤
- 修改 `crawl_user_to_markdown` 传递模式参数

## Out of Scope

- 不修改存储结构
- 不影响已抓取数据

## Risks

- 雪球 API 可能需要额外调用获取长文列表（待验证）
