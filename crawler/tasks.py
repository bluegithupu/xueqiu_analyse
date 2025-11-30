"""抓取任务入口"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Callable

from .browser import XueqiuBrowser
from .client import CookiesExpiredError, XueqiuClient
from .nodriver_browser import get_posts_full_content as nodriver_batch_get
from .user_api import get_user_profile, iter_user_posts

logger = logging.getLogger(__name__)


def crawl_user_to_markdown(
    nickname_or_id: str | int,
    out_root: str = "./data",
    on_progress: Callable[[int, dict], None] = None,
    mode: str = None,
) -> dict:
    """将用户文章保存为 Markdown
    
    Args:
        mode: 抓取模式，None=从配置读取，column=专栏，timeline=全部
    """
    out_root = Path(out_root)
    stats = {"new_count": 0, "skip_count": 0, "error_count": 0}
    
    profile = get_user_profile(nickname_or_id)
    user_id = profile["id"]
    nickname = profile["nickname"]
    
    user_dir = out_root / _safe_filename(nickname)
    posts_dir = user_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    state = _read_state(user_dir)
    last_id = state.get("last_crawled_post_id")
    _save_profile(user_dir, profile)
    
    if mode is None:
        client = XueqiuClient()
        mode = client.settings.get("crawl", {}).get("mode", "column")
    
    try:
        for post in iter_user_posts(user_id, mode=mode):
            post_id = post["id"]
            
            if last_id and post_id <= last_id:
                logger.info("到达已抓取位置，停止")
                break
            
            try:
                filename = _make_filename(post)
                filepath = posts_dir / filename
                
                if filepath.exists():
                    stats["skip_count"] += 1
                    continue
                
                md_content = _render_markdown(post)
                filepath.write_text(md_content, encoding="utf-8")
                stats["new_count"] += 1
                
                if stats["new_count"] == 1:
                    state["last_crawled_post_id"] = post_id
                
                if on_progress:
                    on_progress(stats["new_count"], post)
                    
            except Exception as e:
                logger.error(f"处理文章 {post_id} 失败: {e}")
                stats["error_count"] += 1
                
    except CookiesExpiredError:
        logger.error("Cookies 已失效，保存当前进度")
        _save_state(user_dir, state)
        raise
    
    state["last_crawled_at"] = datetime.now().isoformat()
    _save_state(user_dir, state)
    return stats


def _safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    return name.strip(". ") or "unnamed"


def _make_filename(post: dict) -> str:
    created_at = post.get("created_at", "")
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            date_str = "unknown"
    else:
        date_str = "unknown"
    
    post_id = post.get("id", "0")
    title = post.get("title", "")
    if not title:
        content = post.get("content_text", "")
        title = content[:20].replace("\n", " ").strip()
    
    slug = _safe_filename(title)[:50]
    return f"{date_str}_{post_id}_{slug or 'post'}.md"


def _render_markdown(post: dict) -> str:
    frontmatter = {
        "id": post.get("id"),
        "user_id": post.get("user_id"),
        "nickname": post.get("nickname"),
        "created_at": post.get("created_at"),
        "url": post.get("url"),
        "type": post.get("type"),
        "title": post.get("title") or None,
        "like_count": post.get("like_count", 0),
        "comment_count": post.get("comment_count", 0),
        "repost_count": post.get("repost_count", 0),
        "symbols": post.get("symbols", []),
    }
    
    yaml_lines = ["---"]
    for key, value in frontmatter.items():
        if value is None:
            yaml_lines.append(f"{key}: ~")
        elif isinstance(value, list):
            yaml_lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        elif isinstance(value, str):
            yaml_lines.append(f'{key}: "{value.replace(chr(34), chr(92)+chr(34))}"')
        else:
            yaml_lines.append(f"{key}: {value}")
    yaml_lines.append("---")
    
    body_parts = []
    if post.get("title"):
        body_parts.append(f"# {post['title']}\n")
    body_parts.append(post.get("content_text", ""))
    
    return "\n".join(yaml_lines) + "\n\n" + "\n".join(body_parts)


def _read_state(user_dir: Path) -> dict:
    state_file = user_dir / "crawl_state.json"
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {}


def _save_state(user_dir: Path, state: dict):
    state_file = user_dir / "crawl_state.json"
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _save_profile(user_dir: Path, profile: dict):
    profile_file = user_dir / "profile.json"
    profile_file.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def crawl_user_column_browser(
    nickname_or_id: str | int,
    out_root: str = "./data",
    on_progress: Callable[[int, dict], None] = None,
) -> dict:
    """使用浏览器抓取用户专栏（绕过 WAF）"""
    out_root = Path(out_root)
    stats = {"new_count": 0, "skip_count": 0, "error_count": 0}
    
    profile = get_user_profile(nickname_or_id)
    user_id = str(profile["id"])
    nickname = profile["nickname"]
    
    user_dir = out_root / _safe_filename(nickname)
    posts_dir = user_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    state = _read_state(user_dir)
    last_id = state.get("last_crawled_post_id")
    _save_profile(user_dir, profile)
    
    with XueqiuBrowser(headless=False) as browser:
        # 先收集文章列表（会访问专栏页面）
        posts_to_fetch = []
        for post in browser.iter_column_posts(user_id):
            post_id = post["id"]
            
            if last_id and int(post_id) <= int(last_id):
                logger.info("到达已抓取位置，停止")
                break
            
            filename = _make_filename(post)
            filepath = posts_dir / filename
            
            if filepath.exists():
                stats["skip_count"] += 1
                continue
            
            posts_to_fetch.append((post, filepath))
        
    # 使用 nodriver 批量获取全文（绕过 WAF 滑动验证）
    if posts_to_fetch:
        post_ids = [post["id"] for post, _ in posts_to_fetch]
        logger.info(f"使用 nodriver 获取 {len(post_ids)} 篇文章全文...")
        full_contents = nodriver_batch_get(user_id, post_ids)
        
        for post, filepath in posts_to_fetch:
            post_id = post["id"]
            try:
                if post_id in full_contents:
                    post["content_text"] = full_contents[post_id]
                
                md_content = _render_markdown(post)
                filepath.write_text(md_content, encoding="utf-8")
                stats["new_count"] += 1
                
                if stats["new_count"] == 1:
                    state["last_crawled_post_id"] = post_id
                
                if on_progress:
                    on_progress(stats["new_count"], post)
                    
            except Exception as e:
                logger.error(f"处理文章 {post_id} 失败: {e}")
                stats["error_count"] += 1
    
    state["last_crawled_at"] = datetime.now().isoformat()
    _save_state(user_dir, state)
    return stats
