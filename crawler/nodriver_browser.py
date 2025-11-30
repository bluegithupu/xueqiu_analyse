"""基于 nodriver 的雪球爬虫（绕过 WAF 滑动验证）"""
import asyncio
import json
import re
from datetime import datetime

import nodriver as uc


async def get_posts_full_content_async(user_id: str, post_ids: list[str]) -> dict[str, str]:
    """使用 nodriver 批量获取文章全文（绕过 WAF）"""
    browser = await uc.start()
    results = {}
    
    try:
        for post_id in post_ids:
            url = f"https://xueqiu.com/{user_id}/{post_id}"
            page = await browser.get(url)
            await asyncio.sleep(3)
            
            html = await page.get_content()
            
            # 从 JSON 提取 text 字段
            match = re.search(r'"text":"(.*?)"(?:,\s*"|\})', html)
            if match:
                text = match.group(1)
                try:
                    text = json.loads(f'"{text}"')
                except:
                    pass
                text = _clean_html(text)
                if len(text) > 100:
                    results[post_id] = text
    finally:
        browser.stop()
    
    return results


def get_post_full_content(user_id: str, post_id: str) -> str:
    """同步版本：获取单篇文章全文"""
    results = asyncio.run(get_posts_full_content_async(user_id, [post_id]))
    return results.get(post_id, "")


def get_posts_full_content(user_id: str, post_ids: list[str]) -> dict[str, str]:
    """同步版本：批量获取文章全文"""
    return asyncio.run(get_posts_full_content_async(user_id, post_ids))


def _clean_html(html: str) -> str:
    """清理 HTML"""
    if not html:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&amp;", "&").replace("&quot;", '"')
    return re.sub(r"\n{3,}", "\n\n", text).strip()


if __name__ == "__main__":
    # 测试
    content = get_post_full_content("8106514687", "360897715")
    print(f"内容长度: {len(content)}")
    print(content[:500])
