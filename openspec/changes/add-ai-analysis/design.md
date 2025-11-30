## Context

爬虫已将雪球用户文章存储为 Markdown 文件，需要通过 OpenAI API 单次调用生成投资画像报告。

### 约束
- 使用官方 `openai` Python 客户端
- API Key 通过 `OPENAI_API_KEY` 环境变量读取
- 模型参数可配置（settings.yaml）
- 报告包含文档引用链接

## Goals / Non-Goals

**Goals:**
- 单次调用生成完整投资画像报告
- 报告包含原始文档引用链接
- 生成结构化的 Markdown 报告

**Non-Goals:**
- 不实现实时分析
- 不实现多用户并行分析
- 不实现自定义模型微调

## Decisions

### 1. 单次调用策略
- **Decision**: 将所有文章一次性拼接，单次调用 OpenAI 生成完整报告
- **Why**: 简化流程，保持上下文完整性，利用大模型长上下文能力

### 2. 模型选择
- **Decision**: 默认使用 gpt-4o（128k context），可配置切换
- **Why**: 长上下文支持，适合处理大量文章

### 3. 文档引用
- **Decision**: 报告中包含原始 Markdown 文件的相对路径链接
- **Why**: 便于追溯观点来源，提高报告可信度

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Token 限制 | 使用 gpt-4o 128k 上下文；超限时提示用户 |
| API 调用成本 | 单次调用减少请求数；支持配置模型 |
| 分析质量 | 精细化提示词；包含原文引用便于验证 |

## Migration Plan

N/A - 新增模块，无需迁移

## Open Questions

- 是否需要支持多种报告模板?（暂不实现）
