## 1. 基础设施

- [x] 1.1 更新 `requirements.txt`，添加 openai 依赖
- [x] 1.2 更新 `config/settings.yaml`，添加 OpenAI 配置（model、temperature、max_tokens）
- [x] 1.3 创建 `analysis/__init__.py`

## 2. 文章加载 (analysis/loader.py)

- [x] 2.1 实现 `load_user_posts()` 加载用户 Markdown 文件（解析 frontmatter + 正文）
- [x] 2.2 实现 `build_context()` 拼接所有文章为单个上下文（含文件路径标注）

## 3. 提示词模块 (analysis/prompts.py)

- [x] 3.1 实现 `ANALYSIS_PROMPT` 投资画像分析提示词（要求包含文档引用）

## 4. 分析器 (analysis/analyser.py)

- [x] 4.1 实现 `create_client()` 初始化 OpenAI 客户端
- [x] 4.2 实现 `analyse_user()` 单次调用生成完整报告

## 5. 报告生成 (analysis/report_builder.py)

- [x] 5.1 实现 `save_report()` 保存报告到 `reports/{nickname}_{date}.md`
- [x] 5.2 报告结构：简介、风格、方法、持仓、案例、风险、引用文档列表

## 6. 命令行入口

- [x] 6.1 创建 `scripts/analyse_user.py` CLI
- [x] 6.2 支持命令行参数（用户昵称）
- [x] 6.3 添加进度输出和错误处理

## 7. 测试与验证

- [x] 7.1 编写 loader 单元测试
- [x] 7.2 编写 analyser 单元测试（mock OpenAI）
- [x] 7.3 端到端测试：分析已抓取用户生成报告
