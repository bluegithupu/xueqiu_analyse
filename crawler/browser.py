"""基于 Playwright 的雪球爬虫"""
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator

from playwright.sync_api import sync_playwright, Page, Response
from playwright_stealth import Stealth


# 浏览器数据目录（用于保存 WAF 验证状态）
BROWSER_DATA_DIR = Path(__file__).parent.parent / "browser_data"


class XueqiuBrowser:
    """使用 Playwright 浏览器爬取雪球"""
    
    BASE_URL = "https://xueqiu.com"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._context = None
        self._page = None
    
    def __enter__(self):
        BROWSER_DATA_DIR.mkdir(exist_ok=True)
        # 使用 stealth 模式 + 持久化上下文绕过 WAF
        self._stealth_ctx = Stealth().use_sync(sync_playwright())
        self._playwright = self._stealth_ctx.__enter__()
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_DATA_DIR),
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
            viewport={"width": 1280, "height": 800},
        )
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self._load_cookies()
        return self
    
    def _load_cookies(self):
        """从配置加载 cookies"""
        cookies_path = Path("config/cookies.json")
        if cookies_path.exists():
            data = json.loads(cookies_path.read_text(encoding="utf-8"))
            data.pop("cookies_说明", None)
            cookies = [{"name": k, "value": v, "domain": ".xueqiu.com", "path": "/"} for k, v in data.items()]
            self._context.add_cookies(cookies)
    
    def __exit__(self, *args):
        if self._context:
            self._context.close()
        if hasattr(self, '_stealth_ctx'):
            self._stealth_ctx.__exit__(None, None, None)
    
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
    
    def iter_column_posts(self, user_id: str, max_pages: int = None) -> Iterator[dict]:
        """迭代用户专栏文章（通过监听网络请求绕过 WAF）"""
        captured_data = []
        
        def handle_response(response: Response):
            if "original/timeline.json" in response.url and response.status == 200:
                try:
                    body = response.body()
                    text = body.decode('utf-8', errors='ignore')
                    if text.startswith('{'):
                        data = json.loads(text)
                        if data.get("list"):
                            captured_data.append(data)
                except Exception:
                    pass
        
        self._page.on("response", handle_response)
        
        try:
            self._page.goto(f"{self.BASE_URL}/{user_id}/column", timeout=30000)
            self._page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)
            
            page_num = 1
            while True:
                if max_pages and page_num > max_pages:
                    break
                
                if not captured_data:
                    time.sleep(2)
                if not captured_data:
                    break
                
                data = captured_data.pop(0)
                posts = data.get("list", [])
                if not posts:
                    break
                
                for item in posts:
                    yield self._parse_column_item(item, user_id)
                
                if len(posts) < 20:
                    break
                
                page_num += 1
                self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
        finally:
            self._page.remove_listener("response", handle_response)
    
    def _parse_column_item(self, item: dict, user_id: str) -> dict:
        """解析专栏 API 返回的文章"""
        post_id = item.get("id")
        created_at = item.get("created_at")
        if isinstance(created_at, int):
            created_at = datetime.fromtimestamp(created_at / 1000).isoformat()
        
        text = item.get("description", "")
        text = self._clean_html(text)
        
        return {
            "id": str(post_id),
            "user_id": user_id,
            "title": item.get("title", ""),
            "content_text": text,
            "created_at": created_at,
            "url": f"https://xueqiu.com{item.get('target', '')}",
            "type": "long_post",
            "view_count": item.get("view_count", 0),
        }
    
    def get_post_full_content(self, user_id: str, post_id: str) -> str:
        """获取文章全文（从专栏页面点击进入详情）"""
        full_text = []
        
        def handle_response(response: Response):
            url = response.url
            # 监听文章详情相关 API
            if response.status == 200 and ("expand" in url or "show.json" in url):
                try:
                    body = response.body()
                    text = body.decode('utf-8', errors='ignore')
                    if text.startswith('{'):
                        data = json.loads(text)
                        status = data.get("status", {})
                        content = status.get("text") or status.get("description", "")
                        if content and len(content) > 200:
                            full_text.append(content)
                except Exception:
                    pass
        
        self._page.on("response", handle_response)
        
        try:
            # 点击文章链接
            link = self._page.locator(f'a[href*="/{post_id}"]').first
            if link.is_visible(timeout=3000):
                link.click()
                
                # 等待页面加载，如果遇到 WAF 验证需要更多时间
                self._page.wait_for_load_state("networkidle", timeout=20000)
                
                # 检查是否需要滑动验证
                if "滑动验证" in self._page.content():
                    print("  [!] 检测到滑动验证，请手动完成...")
                    # 等待用户完成验证
                    self._page.wait_for_selector("article, .article__bd", timeout=60000)
                
                time.sleep(2)
                
                # 如果没捕获到 API 响应，尝试从 DOM 提取
                if not full_text:
                    content = self._page.evaluate("""() => {
                        const el = document.querySelector('.article__bd__detail') ||
                                   document.querySelector('.article__bd') ||
                                   document.querySelector('article');
                        return el ? el.innerText : '';
                    }""")
                    if content and len(content) > 200:
                        full_text.append(content)
                
                # 返回专栏页面
                self._page.go_back()
                self._page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as e:
            print(f"  [!] 获取全文失败: {e}")
        finally:
            self._page.remove_listener("response", handle_response)
        
        return self._clean_html(full_text[0]) if full_text else ""
    
    def _clean_html(self, html: str) -> str:
        """清理 HTML 标签"""
        if not html:
            return ""
        text = re.sub(r"<br\s*/?>", "\n", html)
        text = re.sub(r"</p>", "\n\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&amp;", "&").replace("&quot;", '"')
        return re.sub(r"\n{3,}", "\n\n", text).strip()
    
    def iter_user_posts(self, user_id: str, max_pages: int = None) -> Iterator[dict]:
        """迭代用户文章（滚动加载）"""
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
