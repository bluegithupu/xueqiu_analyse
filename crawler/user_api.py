"""雪球用户 API 封装"""
import re
from datetime import datetime
from typing import Iterator

from .client import XueqiuClient


class UserNotFoundError(Exception):
    """用户不存在"""
    pass


def get_user_profile(user_id_or_nick):
    """获取用户基本信息"""
    client = XueqiuClient()
    
    if isinstance(user_id_or_nick, int) or str(user_id_or_nick).isdigit():
        user_id = str(user_id_or_nick)
        data = client.get_json(f"/v4/user/profile/{user_id}")
        if not data or "error_description" in data:
            raise UserNotFoundError(f"用户不存在: {user_id_or_nick}")
        user = data.get("user", data)
    else:
        user = _search_user_by_nick(client, user_id_or_nick)
    
    return {
        "id": user.get("id"),
        "nickname": user.get("screen_name", ""),
        "description": user.get("description", ""),
        "followers_count": user.get("followers_count", 0),
        "status_count": user.get("status_count", 0),
    }


def _search_user_by_nick(client, nick):
    """通过昵称搜索用户，返回完整用户信息"""
    data = client.get_json("/query/v1/search/user.json", {"q": nick, "page": 1, "size": 10})
    users = data.get("list", [])
    for user in users:
        if user.get("screen_name") == nick:
            return user
    raise UserNotFoundError(f"找不到昵称为 '{nick}' 的用户")


def iter_user_posts(user_id, max_pages=None):
    """迭代用户文章列表"""
    client = XueqiuClient()
    page_size = client.settings.get("crawl", {}).get("page_size", 20)
    page = 1
    
    while True:
        if max_pages and page > max_pages:
            break
        
        params = {"user_id": user_id, "page": page, "count": page_size}
        data = client.get_json("/statuses/user_timeline.json", params)
        statuses = data.get("statuses", [])
        
        if not statuses:
            break
        
        for status in statuses:
            post = _parse_post(status)
            if post:
                yield post
        
        if len(statuses) < page_size:
            break
        page += 1


def _parse_post(status):
    """解析文章数据"""
    if not status:
        return None
    
    post_id = status.get("id")
    user = status.get("user", {})
    
    created_at = status.get("created_at")
    if isinstance(created_at, int):
        created_at = datetime.fromtimestamp(created_at / 1000).isoformat()
    
    text = status.get("text", "") or status.get("description", "")
    content_text = _clean_html(text)
    title = status.get("title", "")
    is_long = status.get("mark") == 1 or bool(title)
    symbols = _extract_symbols(text)
    
    return {
        "id": post_id,
        "user_id": user.get("id"),
        "nickname": user.get("screen_name", ""),
        "title": title,
        "content_text": content_text,
        "created_at": created_at,
        "url": f"https://xueqiu.com/{user.get('id')}/{post_id}",
        "type": "long_post" if is_long else "short_status",
        "like_count": status.get("like_count", 0),
        "comment_count": status.get("reply_count", 0),
        "repost_count": status.get("retweet_count", 0),
        "symbols": symbols,
    }


def _clean_html(html):
    """清洗 HTML，提取纯文本"""
    if not html:
        return ""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&amp;", "&").replace('"', '"')
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _extract_symbols(text):
    """提取股票代码"""
    if not text:
        return []
    symbols = set()
    for match in re.finditer(r"\$([^$]+)\(([A-Za-z0-9]+)\)\$", text):
        symbols.add(match.group(2))
    for match in re.finditer(r"\$([^$()]+)\$", text):
        name = match.group(1).strip()
        if name:
            symbols.add(name)
    for match in re.finditer(r"\b(SH|SZ|HK)\d{5,6}\b", text, re.IGNORECASE):
        symbols.add(match.group(0).upper())
    return sorted(symbols)
