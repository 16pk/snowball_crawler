"""
股票爬虫模块
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .api_client import XueqiuAPIClient
from ..models.post import Post, Stock
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StockCrawler:
    """
    股票爬虫
    
    功能:
    - 根据股票名称或代码搜索股票
    - 获取股票信息
    - 爬取股票讨论贴
    """
    
    def __init__(self, api_client: XueqiuAPIClient):
        """
        初始化股票爬虫
        
        Args:
            api_client: API 客户端实例
        """
        self.api_client = api_client
    
    def search_stock(self, query: str) -> List[Stock]:
        """
        搜索股票
        
        Args:
            query: 股票名称或代码
        
        Returns:
            股票列表
        """
        logger.info(f"搜索股票：{query}")
        results = self.api_client.search_stock(query)
        
        stocks = []
        for item in results:
            if item.get('type') == 'stock':
                stock_data = item.get('stock', {})
                if stock_data:
                    stock = Stock(
                        code=stock_data.get('code', ''),
                        name=stock_data.get('name', ''),
                        market=stock_data.get('market', ''),
                        industry=stock_data.get('industry', '')
                    )
                    stocks.append(stock)
        
        logger.info(f"找到 {len(stocks)} 只股票")
        return stocks
    
    def get_stock_by_code(self, code: str) -> Optional[Stock]:
        """
        根据股票代码获取股票信息
        
        Args:
            code: 股票代码 (如 600519 或 SH600519)
        
        Returns:
            股票信息，未找到返回 None
        """
        # 如果没有市场前缀，尝试自动添加
        if not code.startswith(('SH', 'SZ', 'BJ', 'HK')):
            # 根据代码前缀判断市场
            if code.startswith('6'):
                code = f"SH{code}"
            elif code.startswith(('0', '3')):
                code = f"SZ{code}"
            elif code.startswith('4', '8'):
                code = f"BJ{code}"
        
        logger.info(f"获取股票信息：{code}")
        
        # 搜索股票
        results = self.search_stock(code)
        if results:
            return results[0]
        
        return None
    
    def get_stock_id(self, stock: Stock) -> Optional[str]:
        """
        获取股票 ID (雪球内部 ID)
        
        Args:
            stock: 股票对象
        
        Returns:
            股票 ID
        """
        # 通过行情接口获取
        symbol = f"{stock.market}{stock.code}" if stock.market else stock.code
        quote = self.api_client.get_stock_quote(symbol)
        
        if quote:
            return str(quote.get('symbol', ''))
        
        return None
    
    def crawl_posts(
        self,
        stock: Stock,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_reply_count: int = 0,
        min_like_count: int = 0,
        max_pages: int = 100
    ) -> List[Post]:
        """
        爬取股票讨论贴
        
        Args:
            stock: 股票对象
            start_date: 起始日期
            end_date: 结束日期 (默认今天)
            min_reply_count: 最小回复数
            min_like_count: 最小点赞数
            max_pages: 最大爬取页数
        
        Returns:
            帖子列表
        """
        logger.info(f"开始爬取股票 {stock} 的讨论贴")
        
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
                # 获取股票 ID
                stock_id = stock.code  # 使用股票代码作为 ID
                response = self.api_client.get_stock_posts(
                    stock_id=stock_id,
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
                    post = self._parse_tweet(tweet, stock)
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
    
    def _parse_tweet(self, tweet: Dict[str, Any], stock: Stock) -> Optional[Post]:
        """
        解析推文数据
        
        Args:
            tweet: 推文数据
            stock: 股票对象
        
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
            
            return Post(
                id=post_id,
                title=title,
                content=content,
                url=url,
                created_at=created_at,
                user_id=user_id,
                user_name=user_name,
                stock_code=stock.code,
                stock_name=stock.name,
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