"""
帖子详情爬虫模块
"""
from typing import Optional, List, Dict, Any

from .api_client import XueqiuAPIClient
from ..models.post import Post
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PostCrawler:
    """
    帖子详情爬虫
    
    功能:
    - 获取单个帖子详情
    - 获取帖子的回复列表
    """
    
    def __init__(self, api_client: XueqiuAPIClient):
        """
        初始化帖子爬虫
        
        Args:
            api_client: API 客户端实例
        """
        self.api_client = api_client
    
    def get_post_detail(self, post_id: str) -> Optional[Post]:
        """
        获取帖子详情
        
        Args:
            post_id: 帖子 ID
        
        Returns:
            Post 对象，未找到返回 None
        """
        logger.info(f"获取帖子详情：{post_id}")
        
        detail = self.api_client.get_post_detail(post_id)
        if detail:
            return self._parse_tweet(detail)
        return None
    
    def get_post_replies(
        self,
        post_id: str,
        page: int = 1,
        count: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取帖子回复列表
        
        Args:
            post_id: 帖子 ID
            page: 页码
            count: 每页数量
        
        Returns:
            回复列表
        """
        logger.info(f"获取帖子 {post_id} 的回复，第 {page} 页")
        
        # 雪球回复 API
        url = "https://xueqiu.com/statuses/replies.json"
        params = {
            'id': post_id,
            'page': page,
            'count': count
        }
        
        try:
            response = self.api_client._request('GET', url, params=params)
            data = response.json()
            return data.get('list', [])
        except Exception as e:
            logger.error(f"获取回复失败：{e}")
            return []
    
    def _parse_tweet(self, tweet: Dict[str, Any]) -> Optional[Post]:
        """
        解析推文数据
        
        Args:
            tweet: 推文数据
        
        Returns:
            Post 对象
        """
        try:
            post_id = str(tweet.get('id', ''))
            if not post_id:
                return None
            
            # 解析时间
            created_at_timestamp = tweet.get('created_at')
            if created_at_timestamp:
                created_at = self.api_client.parse_timestamp(created_at_timestamp)
            else:
                created_at = self.api_client.parse_timestamp(0)
            
            # 获取用户信息
            user = tweet.get('user', {})
            user_id = str(user.get('id', ''))
            user_name = user.get('screen_name', user.get('nickname', '未知'))
            
            # 获取内容
            title = tweet.get('title', '')
            content = tweet.get('text', '')
            # 移除 HTML 标签
            content = self._clean_html(content)
            
            # 获取图片
            images = []
            pic_urls = tweet.get('pic', [])
            if isinstance(pic_urls, list):
                for pic in pic_urls:
                    if isinstance(pic, dict):
                        images.append(pic.get('url', ''))
                    elif isinstance(pic, str):
                        images.append(pic)
            
            # 构建 URL
            url = f"https://xueqiu.com/{post_id}"
            
            # 尝试获取股票信息
            stock_code = ''
            stock_name = ''
            symbols = tweet.get('symbols', [])
            if symbols and isinstance(symbols, list):
                symbol_info = symbols[0] if isinstance(symbols[0], dict) else {}
                stock_code = symbol_info.get('symbol', '')
                stock_name = symbol_info.get('name', '')
            
            return Post(
                id=post_id,
                title=title,
                content=content,
                url=url,
                created_at=created_at,
                user_id=user_id,
                user_name=user_name,
                stock_code=stock_code,
                stock_name=stock_name,
                reply_count=tweet.get('retweet_count', 0) + tweet.get('reply_count', 0),
                like_count=tweet.get('like_count', 0),
                retweet_count=tweet.get('retweet_count', 0),
                view_count=tweet.get('view_count', 0),
                images=images,
                source=tweet.get('source', ''),
                is_hot=tweet.get('is_hot', False)
            )
            
        except Exception as e:
            logger.error(f"解析推文失败：{e}")
            return None
    
    def _clean_html(self, text: str) -> str:
        """清理 HTML 标签"""
        if not text:
            return ''
        
        # 简单的 HTML 标签清理
        import re
        # 移除 <a> 标签但保留文本
        text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text, flags=re.IGNORECASE)
        # 移除其他 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 解码 HTML 实体
        text = text.replace('&', '&')
        text = text.replace('<', '<')
        text = text.replace('>', '>')
        text = text.replace('"', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        
        return text.strip()