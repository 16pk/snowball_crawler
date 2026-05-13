"""
Cookie 管理模块
"""
import json
from pathlib import Path
from typing import Optional, Dict


class CookieManager:
    """
    Cookie 管理器
    
    获取 Cookie 方法:
    1. 打开浏览器 (Chrome/Firefox/Edge)
    2. 访问 https://xueqiu.com 并登录账号
    3. 按 F12 打开开发者工具
    4. 刷新页面，在 Network 标签中找到任意请求 (如 xueqiu.com)
    5. 点击请求，在 Request Headers 中找到 Cookie 字段
    6. 复制整个 Cookie 值，或者单独复制 xq_a_token 值
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 Cookie 管理器
        
        Args:
            config: 配置字典，包含 cookie 相关配置
        """
        self.config = config or {}
        self._cookies: Dict[str, str] = {}
        self._load_cookies()
    
    def _load_cookies(self):
        """从配置加载 Cookie"""
        cookie_config = self.config.get('cookie', {})
        
        # 尝试从 raw_cookie 加载
        raw_cookie = cookie_config.get('raw_cookie', '')
        if raw_cookie:
            self._parse_raw_cookie(raw_cookie)
            return
        
        # 从各个字段加载
        xq_a_token = cookie_config.get('xq_a_token', '')
        if xq_a_token:
            self._cookies['xq_a_token'] = xq_a_token
        
        xq_r_token = cookie_config.get('xq_r_token', '')
        if xq_r_token:
            self._cookies['xq_r_token'] = xq_r_token
        
        # 其他可能的 cookie 字段
        for key, value in cookie_config.items():
            if key not in ['xq_a_token', 'xq_r_token', 'raw_cookie'] and value:
                self._cookies[key] = value
    
    def _parse_raw_cookie(self, raw_cookie: str):
        """
        解析原始 Cookie 字符串
        
        Args:
            raw_cookie: 原始 Cookie 字符串，格式如 "key1=value1; key2=value2; ..."
        """
        if not raw_cookie:
            return
        
        # 移除可能的 "Cookie: " 前缀
        if raw_cookie.startswith('Cookie: '):
            raw_cookie = raw_cookie[8:]
        
        # 解析 Cookie
        for item in raw_cookie.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                self._cookies[key.strip()] = value.strip()
    
    def get_cookies(self) -> Dict[str, str]:
        """获取 Cookie 字典"""
        return self._cookies.copy()
    
    def get_cookie_string(self) -> str:
        """
        获取 Cookie 字符串格式
        
        Returns:
            Cookie 字符串，格式如 "key1=value1; key2=value2"
        """
        return '; '.join(f"{k}={v}" for k, v in self._cookies.items())
    
    def is_valid(self) -> bool:
        """
        检查 Cookie 是否有效
        
        Returns:
            True 如果至少有 xq_a_token
        """
        return 'xq_a_token' in self._cookies and len(self._cookies['xq_a_token']) > 0
    
    def update_from_browser(self, raw_cookie: str):
        """
        从浏览器复制的 Cookie 更新
        
        Args:
            raw_cookie: 从浏览器复制的 Cookie 字符串
        """
        self._cookies.clear()
        self._parse_raw_cookie(raw_cookie)
    
    def save_to_file(self, filepath: str):
        """
        保存 Cookie 到文件
        
        Args:
            filepath: 保存路径
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._cookies, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """
        从文件加载 Cookie
        
        Args:
            filepath: 文件路径
        """
        path = Path(filepath)
        if not path.exists():
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            self._cookies = json.load(f)
    
    def __repr__(self):
        if self.is_valid():
            token_preview = self._cookies['xq_a_token'][:10] + '...'
            return f"CookieManager(xq_a_token={token_preview})"
        return "CookieManager(invalid)"