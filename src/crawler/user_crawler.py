"""
用户爬虫模块
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .api_client import XueqiuAPIClient
from ..models.post import Post, User
from ..utils.logger import get_logger

logger = get_logger(__name__)


class UserCrawler:
    """
    用户爬虫
    
    功能:
    - 根据用户名搜索用户
    - 获取用户信息
    - 爬取用户发布的帖子
    """
    
    def __init__(self, api_client: XueqiuAPIClient):
        """
        初始化用户爬虫
        
        Args:
            api_client: API 客户端实例
        """
        self.api_client = api_client
    
    def search_user(self, query: str) -> List[User]:
        """
        搜索用户
        
        Args:
            query: 用户名或用户 ID
        
        Returns:
            用户列表
        """
        logger.info(f"搜索用户：{query}")
        
        # 雪球的用户搜索 API 不太一样，这里尝试用通用搜索
        results = self.api_client.search_stock(query)
        
        users = []
        for item in results:
            if item.get('type') == 'user':
                user_data = item.get('user', {})
                if user_data:
                    user = User(
                        user_id=str(user_data.get('id', '')),
                        screen_name=user_data.get('screen_name', user_data.get('nickname', '')),
                        description=user_data.get('description', ''),
                        profile_image_url=user_data.get('profile_image_url', ''),
                        followers_count=user_data.get('followers_count', 0),
                        followees_count=user_data.get('followees_count', 0),
                        status_count=user_data.get('status_count', 0)
                    )
                    users.append(user)
        
        logger.info(f"找到 {len(users)} 个用户")
        return users
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据用户 ID 获取用户信息
        
        Args:
            user_id: 用户 ID
        
        Returns:
            用户信息，未找到返回 None
        """
        logger.info(f"获取用户信息：{user_id}")
        
        user_info = self.api_client.get_user_info(user_id)
        if user_info:
            return User(
                user_id=str(user_info.get('id', user_id)),
                screen_name=user_info.get('screen_name', user_info.get('nickname', '未知')),
                description=user_info.get('description', ''),
                profile_image_url=user_info.get('profile_image_url', ''),
                followers_count=user_info.get('followers_count', 0),
                followees_count=user_info.get('followees_count', 0),
                status_count=user_info.get('status_count', 0)
            )
        
        return None
    
    def crawl_posts(
        self,
        user: User,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_reply_count: int = 0,
        min_like_count: int = 0,
        max_pages: int = 100
    ) -> List[Post]:
        """
        爬取用户帖子
        
        Args:
            user: 用户对象
            start_date: 起始日期
            end_date: 结束日期 (默认今天)
            min_reply_count: 最小回复数
            min_like_count: 最小点赞数
            max_pages: 最大爬取页数
        
        Returns:
            帖子列表
        """
        logger.info(f"开始爬取用户 {user.screen_name} 的帖子")
        
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=1825)  # 默认 5 年
        
        posts = []
        page = 1
        consecutive_empty_pages = 0
        max_consecutive_empty = 3
        
        while page <= max_pages and consecutive_empty_pages < max_consecutive_empty:
            logger.info(f"爬取第 {page} 页")
            
            try:
                response = self.api_client.get_user_posts(
                    user_id=user.user_id,
                    page=page,
                    count=20
                )
                
                tweet_list = response.get('list', [])
                if not tweet_list:
                    consecutive_empty_pages += 1
                    page += 1
                    continue
                
                consecutive_empty_pages = 0
                
                for tweet in tweet_list:
                    post = self._parse_tweet(tweet, user)
                    if post:
                        # 检查日期范围
                        if post.created_at < start_date:
                            logger.info(f"帖子 {post.id} 超出起始日期，停止爬取")
                            return posts
                        
                        if post.created_at > end_date:
                            continue
                        
                        # 检查过滤条件
                        if post.reply_count < min_reply_count:
                            continue
                        if post.like_count < min_like_count:
                            continue
                        
                        posts.append(post)
                
                page += 1
                
            except Exception as e:
                logger.error(f"爬取第 {page} 页失败：{e}")
                page += 1
                continue
        
        logger.info(f"爬取完成，共 {len(posts)} 篇帖子")
        return posts
    
    def _parse_tweet(self, tweet: Dict[str, Any], user: User) -> Optional[Post]:
        """
        解析推文数据
        
        Args:
            tweet: 推文数据
            user: 用户对象
        
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
                created_at = datetime.now()
            
            # 获取用户信息 (使用推文中的用户信息，可能更准确)
            tweet_user = tweet.get('user', {})
            user_id = str(tweet_user.get('id', user.user_id))
            user_name = tweet_user.get('screen_name', tweet_user.get('nickname', user.screen_name))
            
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