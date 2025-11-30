# Tasks: add-crawl-mode

## Implementation Tasks

1. [x] **配置扩展**：在 `settings.yaml` 添加 `crawl.mode` 选项（默认 `column`）
2. [x] **API 层修改**：`iter_user_posts` 新增 `mode` 参数，根据模式选择 API 端点
3. [x] **任务层适配**：`crawl_user_to_markdown` 读取配置并传递 mode
4. [x] **脚本参数**：`crawl_user.py` 支持 `--mode` 命令行参数覆盖配置

## Validation

5. [x] **集成测试**：验证端到端抓取流程（column 模式仅抓取长文，timeline 抓取全部）

## Dependencies

- 无外部依赖
- 各任务可并行开发
