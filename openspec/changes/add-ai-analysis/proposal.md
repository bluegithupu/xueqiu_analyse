# Change: 添加 AI 分析模块

## Why

爬虫模块已完成，用户抓取的 Markdown 文件存储在 `data/{nickname}/posts/` 目录。需要实现 AI 分析模块，通过 OpenAI API 单次调用生成投资画像报告。

## What Changes

- 新增 `analysis/` 模块，包含：
  - `loader.py`: 文章加载与上下文拼接
  - `prompts.py`: 提示词模板
  - `analyser.py`: OpenAI 调用与分析
  - `report_builder.py`: 报告保存
- 新增 `scripts/analyse_user.py` CLI 入口
- 更新 `config/settings.yaml` 添加 OpenAI 相关配置
- 更新 `requirements.txt` 添加 openai 依赖
- 报告特性：
  - 包含原始 Markdown 文档的引用链接
  - 输出路径: `reports/{nickname}_{date}.md`

## Impact

- Affected specs: ai-analysis (新增)
- Affected code: 新增 `analysis/` 模块、`scripts/analyse_user.py`
- Dependencies: 需要 OpenAI API Key（环境变量 `OPENAI_API_KEY`）
