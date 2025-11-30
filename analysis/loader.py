"""文章加载与上下文拼接"""
from pathlib import Path
from dataclasses import dataclass
import frontmatter


@dataclass
class Post:
    path: Path
    id: int
    title: str | None
    created_at: str
    url: str
    content: str


def load_user_posts(nickname: str, data_dir: Path = Path("data")) -> list[Post]:
    """加载用户所有文章"""
    posts_dir = data_dir / nickname / "posts"
    if not posts_dir.exists():
        raise FileNotFoundError(f"用户目录不存在: {posts_dir}")
    
    posts = []
    for md_file in sorted(posts_dir.glob("*.md")):
        post = frontmatter.load(md_file)
        posts.append(Post(
            path=md_file,
            id=post.metadata.get("id", 0),
            title=post.metadata.get("title"),
            created_at=post.metadata.get("created_at", ""),
            url=post.metadata.get("url", ""),
            content=post.content.strip(),
        ))
    return posts


def build_context(posts: list[Post]) -> str:
    """拼接所有文章为单个上下文"""
    parts = []
    for post in posts:
        header = f"[文档: {post.path.name}]"
        if post.title:
            header += f"\n标题: {post.title}"
        header += f"\n日期: {post.created_at}"
        header += f"\n链接: {post.url}"
        parts.append(f"{header}\n\n{post.content}")
    return "\n\n---\n\n".join(parts)
