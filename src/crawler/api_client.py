"""
雪球网 API 客户端
"""
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..utils.cookie import CookieManager
from ..utils.logger import get_logger


logger = get_logger(__name__)


class XueqiuAPIError(Exception):
    """API 请求异常"""
    pass


class XueqiuAPIClient:
    """
    雪球网 API 客户端
    
    主要 API 端点:
    - 股票信息：https://stock.xueqiu.com/v5/stock/quote.json?symbol={code}
    - 股票帖子列表：https://xueqiu.com/statuses/hot.json?id={stock_id}&page={page}
    - 用户帖子列表：https://xueqiu.com/u/{user_id}
    - 帖子详情：https://xueqiu.com/statuses/{post_id}.json
    """
    
    # API 端点
    BASE_URL = "https://xueqiu.com"
    STOCK_QUOTE_URL = "https://stock.xueqiu.com/v5/stock/quote.json"
    STOCK_INFO_URL = "https://stock.xueqiu.com/v5/stock/profile.json"
    HOT_LIST_URL = "https://xueqiu.com/statuses/hot.json"
    USER_TIMELINE_URL = "https://xueqiu.com/statuses/user_timeline.json"
    STATUS_DETAIL_URL = "https://xueqiu.com/statuses/{id}.json"
    SEARCH_STOCK_URL = "https://xueqiu.com/query/v1/symbol/search/generic.json"
    
    def __init__(self, cookie_manager: CookieManager, config: Optional[Dict] = None):
        """
        初始化 API 客户端
        
        Args:
            cookie_manager: Cookie 管理器
            config: 配置字典
        """
        self.cookie_manager = cookie_manager
        self.config = config or {}
        self.request_config = self.config.get('request', {})
        
        self.session = requests.Session()
        self._update_session_cookies()
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://xueqiu.com/',
        }
    
    def _update_session_cookies(self):
        """更新 Session 的 Cookie"""
        cookies = self.cookie_manager.get_cookies()
        for key, value in cookies.items():
            self.session.cookies.set(key, value, domain='.xueqiu.com')
    
    def _get_headers(self, extra_headers: Optional[Dict] = None) -> Dict:
        """获取请求头"""
        headers = self.headers.copy()
        if extra_headers:
            headers.update(extra_headers)
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException)
    )
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            url: 请求 URL
            **kwargs: 其他参数
        
        Returns:
            requests.Response 对象
        
        Raises:
            XueqiuAPIError: 请求失败
        """
        # 更新 Cookie
        self._update_session_cookies()
        
        # 设置默认参数
        kwargs.setdefault('headers', self._get_headers())
        kwargs.setdefault('timeout', self.request_config.get('timeout', 30))
        
        # 请求延迟
        delay = self.request_config.get('delay', 1.0)
        if delay > 0:
            time.sleep(delay)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # 检查是否是 JSON 响应
            if 'application/json' in response.headers.get('Content-Type', ''):
                data = response.json()
                if isinstance(data, dict) and data.get('error_code') not in [None, 0, '0']:
                    logger.warning(f"API 返回错误：{data}")
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"请求失败：{url}, 错误：{e}")
            raise XueqiuAPIError(f"请求失败：{e}")
    
    def search_stock(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索股票
        
        Args:
            query: 股票名称或代码
        
        Returns:
            股票列表
        """
        url = self.SEARCH_STOCK_URL
        params = {
            'q': query,
            'size': 20,
            'type': 'stock'
        }
        
        response = self._request('GET', url, params=params)
        data = response.json()
        
        if 'data' in data:
            return data['data']
        return []
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票行情
        
        Args:
            symbol: 股票代码 (如 SH600519, SZ000001)
        
        Returns:
            股票行情数据
        """
        params = {
            'symbol': symbol,
            'extend': 'detail'
        }
        
        response = self._request('GET', self.STOCK_QUOTE_URL, params=params)
        data = response.json()
        
        if 'data' in data and 'quote' in data['data']:
            return data['data']['quote']
        return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票信息
        
        Args:
            symbol: 股票代码
        
        Returns:
            股票信息
        """
        params = {
            'symbol': symbol
        }
        
        response = self._request('GET', self.STOCK_INFO_URL, params=params)
        data = response.json()
        
        if 'data' in data:
            return data['data']
        return None
    
    def get_stock_posts(
        self,
        stock_id: str,
        page: int = 1,
        count: int = 20,
        since_id: Optional[str] = None,
        max_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取股票讨论贴列表
        
        Args:
            stock_id: 股票 ID (雪球内部 ID)
            page: 页码
            count: 每页数量
            since_id: 获取此 ID 之后的数据
            max_id: 获取此 ID 之前的数据
        
        Returns:
            帖子列表响应
        """
        params = {
            'id': stock_id,
            'page': page,
            'count': count
        }
        
        if since_id:
            params['since_id'] = since_id
        if max_id:
            params['max_id'] = max_id
        
        response = self._request('GET', self.HOT_LIST_URL, params=params)
        return response.json()
    
    def get_user_posts(
        self,
        user_id: str,
        page: int = 1,
        count: int = 20,
        since_id: Optional[str] = None,
        max_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户帖子列表
        
        Args:
            user_id: 用户 ID
            page: 页码
            count: 每页数量
            since_id: 获取此 ID 之后的数据
            max_id: 获取此 ID 之前的数据
        
        Returns:
            帖子列表响应
        """
        params = {
            'uid': user_id,
            'page': page,
            'count': count
        }
        
        if since_id:
            params['since_id'] = since_id
        if max_id:
            params['max_id'] = max_id
        
        response = self._request('GET', self.USER_TIMELINE_URL, params=params)
        return response.json()
    
    def get_post_detail(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        获取帖子详情
        
        Args:
            post_id: 帖子 ID
        
        Returns:
            帖子详情数据
        """
        url = self.STATUS_DETAIL_URL.format(id=post_id)
        response = self._request('GET', url)
        data = response.json()
        
        if 'tweet' in data:
            return data['tweet']
        return None
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        Args:
            user_id: 用户 ID
        
        Returns:
            用户信息
        """
        url = f"https://xueqiu.com/cubes/profile.json?user_id={user_id}"
        try:
            response = self._request('GET', url)
            data = response.json()
            return data
        except XueqiuAPIError:
            # 尝试其他方式
            return None
    
    def parse_timestamp(self, timestamp: int) -> datetime:
        """
        解析时间戳
        
        Args:
            timestamp: 毫秒时间戳
        
        Returns:
            datetime 对象
        """
        return datetime.fromtimestamp(timestamp / 1000)