# xueqiu_analyse

雪球用户内容抓取与 AI 分析工具。

## 功能

- **内容抓取**：抓取雪球用户的专栏文章或全部动态
- **WAF 绕过**：使用 Playwright + Stealth 模式绕过阿里云 WAF
- **AI 分析**：基于 OpenAI 对用户投资风格进行分析

## 安装

```bash
pip install -r requirements.txt
playwright install chromium
```

## 使用方式

### 1. 配置 Cookies

首次使用需要配置雪球登录 cookies：

```bash
python scripts/init_browser.py
```

按提示在浏览器中登录雪球，完成后 cookies 会保存到 `config/cookies.json`。

### 2. 抓取用户内容

```bash
# 使用浏览器模式抓取专栏（推荐，可绕过 WAF）
python scripts/crawl_user.py <用户名或ID> -b

# 使用 HTTP API 抓取（可能被 WAF 拦截）
python scripts/crawl_user.py <用户名或ID> -m column   # 仅专栏
python scripts/crawl_user.py <用户名或ID> -m timeline # 全部动态
```

参数说明：
- `-b, --browser`：使用浏览器模式（绕过 WAF）
- `-m, --mode`：抓取模式，`column`=专栏，`timeline`=全部
- `-o, --output`：输出目录，默认 `./data`
- `-v, --verbose`：详细输出

### 3. AI 分析

```bash
python scripts/analyse_user.py <用户名>
```

分析报告保存到 `reports/` 目录。

## 运行原理

### WAF 绕过

雪球专栏 API `/statuses/original/timeline.json` 受阿里云 WAF 保护，直接 HTTP 请求会被拦截。

解决方案：
1. **playwright-stealth**：隐藏浏览器自动化特征
2. **持久化上下文**：保存 WAF 验证状态到 `browser_data/`
3. **网络监听**：捕获页面自动发起的带签名的 API 请求

详见 [docs/waf-bypass-issue.md](docs/waf-bypass-issue.md)

### 数据流

```
用户昵称/ID
    ↓
获取用户资料 (user_api.py)
    ↓
抓取文章列表 (browser.py / user_api.py)
    ↓
保存为 Markdown (tasks.py)
    ↓
data/<用户名>/posts/*.md
    ↓
AI 分析 (analyser.py)
    ↓
reports/<用户名>_<日期>.md
```

## 目录结构

```
├── config/
│   ├── cookies.json      # 雪球登录 cookies
│   └── settings.yaml     # 配置文件
├── crawler/
│   ├── browser.py        # Playwright 浏览器爬虫
│   ├── client.py         # HTTP 客户端
│   ├── tasks.py          # 抓取任务
│   └── user_api.py       # 用户 API
├── analysis/
│   ├── analyser.py       # AI 分析器
│   └── prompts.py        # 分析提示词
├── data/                 # 抓取的用户数据
├── reports/              # AI 分析报告
└── scripts/              # 命令行工具
```

## 依赖

- Python 3.10+
- Playwright（浏览器自动化）
- playwright-stealth（反检测）
- httpx（HTTP 客户端）
- OpenAI（AI 分析）
