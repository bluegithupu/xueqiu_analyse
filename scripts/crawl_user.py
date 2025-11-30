#!/usr/bin/env python
"""抓取雪球用户内容的命令行工具"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler.client import CookiesExpiredError
from crawler.user_api import UserNotFoundError
from crawler.tasks import crawl_user_to_markdown


def main():
    parser = argparse.ArgumentParser(description="抓取雪球用户文章到 Markdown")
    parser.add_argument("user", help="用户 ID 或昵称")
    parser.add_argument("-o", "--output", default="./data", help="输出目录")
    parser.add_argument("-m", "--mode", choices=["column", "timeline"], help="抓取模式: column=专栏, timeline=全部")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    
    def on_progress(count: int, post: dict):
        title = post.get("title") or post.get("content_text", "")[:30]
        print(f"[{count}] {title}")
    
    try:
        mode_desc = args.mode or "配置默认"
        print(f"开始抓取用户: {args.user} (模式: {mode_desc})")
        stats = crawl_user_to_markdown(args.user, out_root=args.output, on_progress=on_progress, mode=args.mode)
        print(f"\n完成! 新增: {stats['new_count']}, 跳过: {stats['skip_count']}, 错误: {stats['error_count']}")
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except UserNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except CookiesExpiredError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n中断")
        sys.exit(130)


if __name__ == "__main__":
    main()
