# Design: add-crawl-mode

## 实现方案

专栏 API (`/statuses/original/timeline.json`) 被阿里云 WAF 拦截，改用 **timeline API + 过滤** 方案。

| 模式 | 实现 | 说明 |
|------|------|------|
| column | timeline API + 过滤 `type=long_post` | 仅长文（有标题或 mark>=1） |
| timeline | timeline API | 全部动态 |

## 长文判定

文章满足以下任一条件判定为长文（`type=long_post`）：
- `mark >= 1`
- 存在非空 `title`

## 实现策略

```python
iter_user_posts(user_id, mode="column")
    filter_long_only = (mode == "column")
    for post in timeline_api():
        if filter_long_only and post.type != "long_post":
            continue
        yield post
```

## WAF 问题说明

专栏 API 需要动态签名（`md5__1038` 参数），普通 requests 和 headless 浏览器均被拦截。
使用 timeline API + 过滤是最稳定可靠的方案。
