## 1. 基础设施

- [x] 1.1 创建 `requirements.txt`，添加 requests、PyYAML 依赖
- [x] 1.2 创建 `config/settings.yaml` 配置模板
- [x] 1.3 创建 `config/cookies.json.example` 示例文件
- [x] 1.4 更新 `.gitignore`，忽略 cookies.json 和 data/ 目录

## 2. HTTP 客户端 (crawler/client.py)

- [x] 2.1 实现配置加载（cookies、UA、超时、间隔）
- [x] 2.2 实现 `XueqiuClient` 类，封装 requests.Session
- [x] 2.3 实现 `get_json()` 方法，自动解析 JSON
- [x] 2.4 实现 `get_html()` 方法，返回 HTML 文本
- [x] 2.5 实现限速逻辑（请求间隔）
- [x] 2.6 实现重试策略（指数退避）
- [x] 2.7 实现 cookies 失效检测

## 3. 用户 API (crawler/user_api.py)

- [x] 3.1 实现 `get_user_profile()` 获取用户基本信息
- [x] 3.2 实现 `iter_user_posts()` 迭代用户文章列表
- [x] 3.3 实现分页处理逻辑
- [x] 3.4 实现内容解析（提取标题、正文、元数据）

## 4. 抓取任务 (crawler/tasks.py)

- [x] 4.1 实现 `crawl_user_to_markdown()` 主函数
- [x] 4.2 实现目录创建逻辑
- [x] 4.3 实现 Markdown 模板渲染（frontmatter + 正文）
- [x] 4.4 实现文件命名规则
- [x] 4.5 实现幂等写入（已存在则跳过）
- [x] 4.6 实现 `crawl_state.json` 读写
- [x] 4.7 实现增量抓取判断

## 5. 命令行入口

- [x] 5.1 创建 `scripts/crawl_user.py` CLI 入口
- [x] 5.2 支持命令行参数（用户 ID/昵称）
- [x] 5.3 添加进度输出

## 6. 测试与验证

- [x] 6.1 编写 client.py 单元测试
- [x] 6.2 编写 user_api.py 单元测试（mock 响应）
- [x] 6.3 端到端手动测试：抓取真实用户验证 (Blue7az, 120篇)
