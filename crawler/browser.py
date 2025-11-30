"""基于 Playwright 的雪球爬虫"""
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator

from playwright.sync_api import sync_playwright, Page


class XueqiuBrowser:
    """使用 Playwright 浏览器爬取雪球"""
    
    BASE_URL = "https://xueqiu.com"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._page = None
    
    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()
        return self
    
    def __exit__(self, *args):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def get_user_profile(self, user_id: str) -> dict:
        """获取用户资料"""
        self._page.goto(f"{self.BASE_URL}/u/{user_id}")
        self._page.wait_for_load_state("networkidle")
        self._close_popups()
        
        # 从页面提取用户信息
        profile = self._page.evaluate("""() => {
            const h2 = document.querySelector('h2');
            const nickname = h2 ? h2.innerText.trim() : '';
            
            const stats = document.querySelectorAll('[href*="#/follow"], [href*="#/fans"]');
            let followers = 0, following = 0;
            stats.forEach(s => {
                const text = s.innerText;
                const num = parseInt(text.match(/\\d+/)?.[0] || '0');
                if (text.includes('关注')) following = num;
                if (text.includes('粉丝')) followers = num;
            });
            
            const postsLink = document.querySelector('[href="#/"]');
            const postsCount = postsLink ? parseInt(postsLink.innerText.match(/\\d+/)?.[0] || '0') : 0;
            
            return { nickname, followers, following, posts_count: postsCount };
        }""")
        
        profile["id"] = user_id
        return profile
    
    def iter_user_posts(self, user_id: str, max_pages: int = None) -> Iterator[dict]:
        """迭代用户文章"""
        self._page.goto(f"{self.BASE_URL}/u/{user_id}")
        self._page.wait_for_load_state("networkidle")
        self._close_popups()
        
        page = 1
        seen_ids = set()
        
        while True:
            if max_pages and page > max_pages:
                break
            
            posts = self._extract_posts()
            new_posts = [p for p in posts if p["id"] not in seen_ids]
            
            if not new_posts:
                break
            
            for post in new_posts:
                seen_ids.add(post["id"])
                yield post
            
            # 滚动加载更多
            if not self._scroll_to_load_more():
                break
            
            page += 1
            time.sleep(1)
    
    def _close_popups(self):
        """关闭弹窗"""
        try:
            skip = self._page.locator('text=跳过').first
            if skip.is_visible(timeout=2000):
                skip.click()
                time.sleep(0.5)
        except Exception:
            pass
        
        try:
            close = self._page.locator('[class*="close"]').first
            if close.is_visible(timeout=1000):
                close.click()
        except Exception:
            pass
    
    def _extract_posts(self) -> list[dict]:
        """从页面提取文章"""
        return self._page.evaluate("""() => {
            const articles = Array.from(document.querySelectorAll('article'));
            return articles.map(a => {
                const links = a.querySelectorAll('a');
                let postUrl = '', postId = '';
                for (let link of links) {
                    const match = link.href.match(/\\/(\\d+)\\/(\\d+)/);
                    if (match) {
                        postUrl = link.href;
                        postId = match[2];
                        break;
                    }
                }
                
                const timeLink = a.querySelector('a[href*="/"]:nth-of-type(2)');
                const timeText = timeLink ? timeLink.innerText : '';
                
                const content = a.innerText;
                const lines = content.split('\\n').filter(l => l.trim());
                const nickname = lines[0] || '';
                const text = lines.slice(1).join('\\n');
                
                return {
                    id: postId,
                    url: postUrl,
                    nickname: nickname,
                    created_at_text: timeText,
                    content_text: text.substring(0, 2000),
                    raw_text: content
                };
            }).filter(p => p.id);
        }""")
    
    def _scroll_to_load_more(self) -> bool:
        """滚动加载更多"""
        old_count = self._page.evaluate("document.querySelectorAll('article').length")
        
        self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        
        new_count = self._page.evaluate("document.querySelectorAll('article').length")
        return new_count > old_count


def crawl_user_with_browser(
    user_id: str,
    out_root: str = "./data",
    max_pages: int = None,
    headless: bool = True,
) -> dict:
    """使用浏览器抓取用户文章"""
    out_root = Path(out_root)
    stats = {"new_count": 0, "skip_count": 0}
    
    with XueqiuBrowser(headless=headless) as browser:
        # 获取用户信息
        profile = browser.get_user_profile(user_id)
        nickname = profile.get("nickname", user_id)
        
        # 创建目录
        user_dir = out_root / _safe_filename(nickname)
        posts_dir = user_dir / "posts"
        posts_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存用户信息
        (user_dir / "profile.json").write_text(
            json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        
        # 抓取文章
        for post in browser.iter_user_posts(user_id, max_pages):
            filename = _make_filename(post)
            filepath = posts_dir / filename
            
            if filepath.exists():
                stats["skip_count"] += 1
                continue
            
            md_content = _render_markdown(post)
            filepath.write_text(md_content, encoding="utf-8")
            stats["new_count"] += 1
            print(f"[{stats['new_count']}] {filename}")
    
    return stats


def _safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    return name.strip(". ") or "unnamed"


def _make_filename(post: dict) -> str:
    created = post.get("created_at_text", "")
    # 解析日期 "11-28 13:38" 格式
    match = re.search(r"(\d{1,2})-(\d{1,2})", created)
    if match:
        month, day = match.groups()
        year = datetime.now().year
        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    else:
        date_str = "unknown"
    
    post_id = post.get("id", "0")
    content = post.get("content_text", "")[:20].replace("\n", " ").strip()
    slug = _safe_filename(content)[:30] or "post"
    
    return f"{date_str}_{post_id}_{slug}.md"


def _render_markdown(post: dict) -> str:
    frontmatter = f"""---
id: {post.get('id')}
url: "{post.get('url', '')}"
created_at: "{post.get('created_at_text', '')}"
---

"""
    return frontmatter + post.get("content_text", "")
