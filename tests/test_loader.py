"""loader 模块单元测试"""
import tempfile
from pathlib import Path

import pytest

from analysis.loader import load_user_posts, build_context, Post


@pytest.fixture
def sample_posts_dir(tmp_path):
    """创建测试用文章目录"""
    posts_dir = tmp_path / "test_user" / "posts"
    posts_dir.mkdir(parents=True)
    
    md1 = """---
id: 123
title: "测试标题"
created_at: "2024-01-01T10:00:00"
url: "https://xueqiu.com/123/123"
---

这是测试内容。
"""
    (posts_dir / "2024-01-01_123_测试.md").write_text(md1, encoding="utf-8")
    
    md2 = """---
id: 456
title: ~
created_at: "2024-01-02T10:00:00"
url: "https://xueqiu.com/123/456"
---

第二篇内容。
"""
    (posts_dir / "2024-01-02_456_test.md").write_text(md2, encoding="utf-8")
    return tmp_path


def test_load_user_posts(sample_posts_dir):
    posts = load_user_posts("test_user", sample_posts_dir)
    assert len(posts) == 2
    assert posts[0].id == 123
    assert posts[0].title == "测试标题"
    assert "测试内容" in posts[0].content


def test_load_user_posts_not_found():
    with pytest.raises(FileNotFoundError):
        load_user_posts("nonexistent", Path("/tmp"))


def test_build_context(sample_posts_dir):
    posts = load_user_posts("test_user", sample_posts_dir)
    context = build_context(posts)
    assert "[文档:" in context
    assert "测试内容" in context
    assert "第二篇内容" in context
    assert "---" in context
