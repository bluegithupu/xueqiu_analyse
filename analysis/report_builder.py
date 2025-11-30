"""报告生成与保存"""
from datetime import datetime
from pathlib import Path


def save_report(nickname: str, content: str, reports_dir: Path = Path("reports")) -> Path:
    """保存报告到 reports/{nickname}_{date}.md"""
    reports_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{nickname}_{date_str}.md"
    report_path = reports_dir / filename
    
    header = f"# {nickname} 投资画像报告\n\n生成时间: {datetime.now().isoformat()}\n\n---\n\n"
    report_path.write_text(header + content, encoding="utf-8")
    return report_path
