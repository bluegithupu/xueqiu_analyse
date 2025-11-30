"""OpenAI 调用与分析"""
import os
from pathlib import Path

import httpx
import yaml
from openai import OpenAI

from .prompts import ANALYSIS_PROMPT


def load_config() -> dict:
    """加载配置"""
    config_path = Path("config/settings.yaml")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_client() -> OpenAI:
    """初始化 OpenAI 客户端"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量")
    http_client = httpx.Client(proxy=None)
    return OpenAI(api_key=api_key, http_client=http_client)


def analyse_user(context: str) -> str:
    """单次调用生成完整报告"""
    config = load_config()
    openai_cfg = config.get("openai", {})
    
    client = create_client()
    prompt = ANALYSIS_PROMPT.format(context=context)
    
    response = client.chat.completions.create(
        model=openai_cfg.get("model", "gpt-5-nano"),
        messages=[{"role": "user", "content": prompt}],
        temperature=openai_cfg.get("temperature", 0.3),
        max_tokens=openai_cfg.get("max_tokens", 8192),
    )
    return response.choices[0].message.content
