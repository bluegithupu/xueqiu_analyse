#!/usr/bin/env python3
"""用户投资画像分析 CLI"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.loader import load_user_posts, build_context
from analysis.analyser import analyse_user
from analysis.report_builder import save_report


def main():
    parser = argparse.ArgumentParser(description="分析雪球用户投资画像")
    parser.add_argument("nickname", help="用户昵称")
    parser.add_argument("--data-dir", default="data", help="数据目录 (default: data)")
    args = parser.parse_args()
    
    print(f"[1/4] 加载 {args.nickname} 的文章...")
    try:
        posts = load_user_posts(args.nickname, Path(args.data_dir))
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    
    print(f"[2/4] 发现 {len(posts)} 篇文章，拼接上下文...")
    context = build_context(posts)
    
    # 保存中间上下文
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    context_file = tmp_dir / f"{args.nickname}_context.md"
    context_file.write_text(context, encoding="utf-8")
    print(f"      上下文已保存: {context_file}")
    
    print(f"[3/4] 调用 OpenAI 分析中...")
    try:
        report_content = analyse_user(context)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"API 调用失败: {e}")
        sys.exit(1)
    
    print("[4/4] 保存报告...")
    report_path = save_report(args.nickname, report_content)
    print(f"完成! 报告已保存到: {report_path}")


if __name__ == "__main__":
    main()
