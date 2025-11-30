# 雪球专栏 API WAF 拦截问题

## 问题描述

雪球专栏 API `/statuses/original/timeline.json` 被阿里云 WAF（Web Application Firewall）拦截，无法直接通过 HTTP 客户端访问。

### 影响范围

- **受影响 API**: `/statuses/original/timeline.json`
- **正常 API**: `/statuses/user_timeline.json`（timeline 动态列表）
- **当前方案**: 使用 timeline API + 过滤 `type=long_post` 替代

## 技术分析

### 1. WAF 拦截特征

请求专栏 API 时返回阿里云 WAF 验证页面：

```html
<textarea id="renderData" style="display:none">{"_waf_bd8ce2ce37":"..."}</textarea>
<!doctype html><html><head>
<meta name="aliyun_waf_aa" content="...">
<meta name="aliyun_waf_oo" content="...">
<meta name="aliyun_waf_00" content="...">
<script src="/u21pn7x6/r8lw5pzu/psk8uqfi"></script>
```

### 2. 浏览器正常访问的原因

浏览器访问专栏页面时，请求 URL 带有动态签名参数：

```
/statuses/original/timeline.json?user_id=8106514687&page=1&md5__1038=2287582d28...
```

关键参数：
- `md5__1038`: 动态生成的 WAF 签名，由页面 JavaScript 计算

### 3. 浏览器 Cookies 差异

浏览器成功访问时的 cookies 包含 WAF 相关字段：

| Cookie | 说明 |
|--------|------|
| `ssxmod_itna` | WAF 会话令牌 |
| `ssxmod_itna2` | WAF 会话令牌（备用） |
| `.thumbcache_*` | WAF 指纹缓存 |
| `smidV2` | 设备指纹 |

我们的 `cookies.json` 缺少这些动态生成的 WAF cookies。

## 尝试过的方案

### 方案 1: 直接 requests 请求 ❌

```python
client.get_json("/statuses/original/timeline.json", params)
```

**结果**: 被 WAF 拦截，返回 HTML 验证页面

### 方案 2: Playwright 浏览器 + 持久化上下文 ❌

```python
context = playwright.chromium.launch_persistent_context(user_data_dir)
page.evaluate("fetch('/statuses/original/timeline.json')")
```

**结果**: 页面加载正常，但 fetch 调用仍被 WAF 拦截

### 方案 3: Playwright 浏览器 + 注入 cookies ❌

```python
context.add_cookies(cookies_from_json)
page.goto(column_url)
page.evaluate("fetch(...)")
```

**结果**: 缺少 WAF 动态 cookies，API 调用被拦截

### 方案 4: 从页面 DOM 解析 ❌

```python
page.evaluate("document.querySelectorAll('h3 a')")
```

**结果**: 专栏页面使用 Vue.js 动态渲染，headless 模式下内容未完全加载

## 可能的解决方案

### 方案 A: 逆向 WAF 签名算法

1. 分析 `/u21pn7x6/r8lw5pzu/psk8uqfi` 脚本
2. 理解 `md5__1038` 参数生成逻辑
3. 在 Python 中实现签名计算

**难度**: 高  
**风险**: WAF 算法可能定期更新

### 方案 B: 使用 Selenium/Playwright 非 headless 模式

1. 启动真实浏览器窗口
2. 等待 JavaScript 完全执行
3. 从渲染后的 DOM 提取数据

**难度**: 中  
**缺点**: 速度慢，资源消耗大

### 方案 C: 定期导出完整 cookies

1. 扩展 `init_browser.py` 导出所有 cookies（包括 WAF 相关）
2. 在 requests 中使用完整 cookies
3. 用户需要定期手动更新

**难度**: 低  
**缺点**: 需要人工介入，cookies 可能快速过期

### 方案 D: 使用代理服务

1. 使用支持 JavaScript 渲染的代理服务（如 ScrapingBee, Browserless）
2. 或自建 Puppeteer/Playwright 服务

**难度**: 中  
**缺点**: 成本，依赖外部服务

### 方案 E: 监听浏览器网络请求

1. 使用 Playwright 拦截网络请求
2. 等待专栏 API 自然被调用
3. 从响应中提取数据

```python
page.on("response", lambda r: handle_response(r) if "original/timeline" in r.url else None)
page.goto(column_url)
```

**难度**: 中  
**可行性**: 高（页面加载时会自动调用 API）

## 当前临时方案

使用 timeline API + 过滤长文：

```python
# iter_user_posts(user_id, mode="column")
filter_long_only = (mode == "column")
for post in timeline_api():
    if filter_long_only and post.type != "long_post":
        continue
    yield post
```

**局限性**:
- 需要遍历所有动态才能过滤出长文
- 对于发布大量短动态的用户效率较低

## 参考信息

- 专栏页面: `https://xueqiu.com/{user_id}/column`
- 专栏 API: `/statuses/original/timeline.json?user_id={id}&page={page}`
- Timeline API: `/statuses/user_timeline.json?user_id={id}&page={page}`
- WAF 类型: 阿里云 Web Application Firewall

---

*文档创建: 2025-11-30*  
*状态: 待解决*
