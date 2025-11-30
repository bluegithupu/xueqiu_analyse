# 专栏文章全文获取问题

## 问题描述

当前抓取的专栏文章只包含**概览/摘要**，没有获取到文章的完整内容。

### 示例

```markdown
---
id: "360897715"
title: "介绍下我的公司，成都川糖"
...
---

# 介绍下我的公司，成都川糖

（内容为空或只有摘要）
```

### 原因分析

专栏列表 API `/statuses/original/timeline.json` 返回的 `description` 字段只是文章摘要，完整内容需要访问文章详情页面。

## 解决方案

### 方案 A: 调用文章详情 API

```
GET /statuses/expand.json?id={post_id}
```

返回完整的 `text` 或 `description` 字段。

**难度**: 低  
**风险**: 可能也被 WAF 拦截

### 方案 B: 访问文章页面提取内容

1. 使用 Playwright 访问 `https://xueqiu.com/{user_id}/{post_id}`
2. 等待页面渲染完成
3. 从 DOM 提取文章内容

**难度**: 中  
**优点**: 绕过 WAF，获取渲染后的完整内容

### 方案 C: 监听文章详情 API

类似专栏列表的解决方案：
1. 访问文章页面
2. 监听网络请求捕获详情 API 响应

**难度**: 中  
**可行性**: 高

## 解决方案

使用 **nodriver** 成功绕过 WAF 滑动验证。

### 方案对比

| 工具 | WAF 滑动验证 | 说明 |
|------|-------------|------|
| playwright-stealth | ❌ 被拦截 | 仍被检测为自动化 |
| **nodriver** | ✅ 绕过 | 无 selenium/webdriver，直接 CDP 通信 |

### nodriver 介绍

- undetected-chromedriver 的继任者
- 不依赖 selenium/webdriver
- 直接使用 CDP (Chrome DevTools Protocol)
- 专门针对 WAF 和反爬虫检测优化

### 实现

```python
# crawler/nodriver_browser.py
import nodriver as uc

async with XueqiuNodriver() as browser:
    # 获取文章全文（无需手动验证）
    full_text = await browser.get_post_full_content(user_id, post_id)
```

### 测试结果

```
页面长度: 143435
>>> 正常页面 <<<
文章长度: 416 字符（完整全文）
```

---

*文档创建: 2025-11-30*  
*状态: 已解决（使用 nodriver）*
