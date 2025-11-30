"""雪球 HTTP 客户端封装"""
import json
import random
import time
from pathlib import Path

import requests
import yaml


class CookiesExpiredError(Exception):
    """Cookies 失效异常"""
    pass


class XueqiuClient:
    """雪球 HTTP 客户端，封装 requests.Session"""
    
    BASE_URL = "https://xueqiu.com"
    LOGIN_PATHS = ("/login", "/user/login")
    
    _instance = None
    
    def __new__(cls, config_dir: str = "config"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_dir: str = "config"):
        if self._initialized:
            return
        self._initialized = True
        
        self.config_dir = Path(config_dir)
        self._session = requests.Session()
        self._last_request_time = 0
        
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 加载 settings.yaml
        settings_path = self.config_dir / "settings.yaml"
        if settings_path.exists():
            with open(settings_path, "r", encoding="utf-8") as f:
                self.settings = yaml.safe_load(f)
        else:
            self.settings = self._default_settings()
        
        # 加载 cookies.json
        cookies_path = self.config_dir / "cookies.json"
        if not cookies_path.exists():
            raise FileNotFoundError(
                f"Cookies 文件不存在: {cookies_path}\n"
                f"请复制 cookies.json.example 为 cookies.json 并填入有效的 cookies"
            )
        
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        
        # 移除说明字段
        cookies.pop("cookies_说明", None)
        
        # 设置 cookies 和 headers
        for name, value in cookies.items():
            self._session.cookies.set(name, value, domain=".xueqiu.com")
        
        self._session.headers.update({
            "User-Agent": self.settings.get("http", {}).get("user_agent", ""),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": self.BASE_URL,
            "Origin": self.BASE_URL,
        })
    
    @staticmethod
    def _default_settings():
        return {
            "http": {"user_agent": "Mozilla/5.0", "timeout": 30},
            "rate_limit": {"min_interval": 1.0, "max_interval": 2.0},
            "retry": {"max_attempts": 3, "base_delay": 1.0},
        }
    
    def _wait_for_rate_limit(self):
        """等待限速间隔"""
        rl = self.settings.get("rate_limit", {})
        min_interval = rl.get("min_interval", 1.0)
        max_interval = rl.get("max_interval", 2.0)
        
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            wait = random.uniform(min_interval, max_interval) - elapsed
            if wait > 0:
                time.sleep(wait)
    
    def _check_cookies_expired(self, response: requests.Response):
        """检测 cookies 是否失效"""
        if any(path in response.url for path in self.LOGIN_PATHS):
            raise CookiesExpiredError(
                "Cookies 已失效，请更新 config/cookies.json"
            )
    
    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """带重试的请求"""
        retry_cfg = self.settings.get("retry", {})
        max_attempts = retry_cfg.get("max_attempts", 3)
        base_delay = retry_cfg.get("base_delay", 1.0)
        timeout = self.settings.get("http", {}).get("timeout", 30)
        
        kwargs.setdefault("timeout", timeout)
        
        last_exc = None
        for attempt in range(max_attempts + 1):
            self._wait_for_rate_limit()
            
            try:
                resp = self._session.request(method, url, **kwargs)
                self._last_request_time = time.time()
                
                self._check_cookies_expired(resp)
                
                if resp.status_code >= 500:
                    raise requests.HTTPError(f"Server error: {resp.status_code}")
                
                return resp
            except (requests.RequestException, requests.HTTPError) as e:
                last_exc = e
                if attempt < max_attempts:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        
        raise last_exc
    
    def get_json(self, url: str, params: dict = None) -> dict | list:
        """发送 GET 请求，返回 JSON"""
        if not url.startswith("http"):
            url = self.BASE_URL + url
        
        resp = self._request_with_retry("GET", url, params=params)
        resp.raise_for_status()
        
        try:
            return resp.json()
        except json.JSONDecodeError:
            raise ValueError(f"响应不是有效 JSON: {resp.text[:200]}")
    
    def get_html(self, url: str, params: dict = None) -> str:
        """发送 GET 请求，返回 HTML"""
        if not url.startswith("http"):
            url = self.BASE_URL + url
        
        resp = self._request_with_retry("GET", url, params=params)
        resp.raise_for_status()
        return resp.text
    
    @classmethod
    def reset_instance(cls):
        """重置单例（用于测试）"""
        cls._instance = None
