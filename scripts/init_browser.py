#!/usr/bin/env python
"""初始化浏览器会话 - 手动完成一次滑动验证后 cookies 会被保存"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    print("启动浏览器，请在页面中完成滑动验证...")
    print("验证通过后 cookies 会被自动保存，之后可使用 headless 模式")
    print()
    
    with sync_playwright() as p:
        user_data_dir = Path.home() / ".xueqiu_browser"
        user_data_dir.mkdir(exist_ok=True)
        
        context = p.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://xueqiu.com")
        
        print("请在浏览器中：")
        print("1. 完成滑动验证")
        print("2. 浏览几个页面确认正常")
        print("3. 按 Enter 键关闭浏览器并保存会话")
        print()
        
        input("按 Enter 键完成初始化...")
        
        context.close()
        print("会话已保存！现在可以使用 crawl_browser.py 了")


if __name__ == "__main__":
    main()
