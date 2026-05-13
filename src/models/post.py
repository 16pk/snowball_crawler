"""
Post, Stock, User 类定义 - 包含数据库操作和导出功能
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class Stock:
    """股票类 - 包含股票信息和相关操作"""
    
    def __init__(self, code: str, name: str, market: str = "", **kwargs):
        self.code = code
        self.name = name
        self.market = market
        self.industry = kwargs.get('industry', '')
        self.area = kwargs.get('area', '')
        self.pe_ratio = kwargs.get('pe_ratio', 0.0)
        self.pb_ratio = kwargs.get('pb_ratio', 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'market': self.market,
            'industry': self.industry,
            'area': self.area,
            'pe_ratio': self.pe_ratio,
            'pb_ratio': self.pb_ratio
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stock':
        """从字典创建"""
        return cls(**data)
    
    def __repr__(self):
        return f"Stock({self.market}{self.code}, {self.name})"


class User:
    """用户类 - 包含用户信息和相关操作"""
    
    def __init__(self, user_id: str, screen_name: str, **kwargs):
        self.user_id = user_id
        self.screen_name = screen_name
        self.description = kwargs.get('description', '')
        self.profile_image_url = kwargs.get('profile_image_url', '')
        self.followers_count = kwargs.get('followers_count', 0)
        self.followees_count = kwargs.get('followees_count', 0)
        self.status_count = kwargs.get('status_count', 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'screen_name': self.screen_name,
            'description': self.description,
            'profile_image_url': self.profile_image_url,
            'followers_count': self.followers_count,
            'followees_count': self.followees_count,
            'status_count': self.status_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """从字典创建"""
        return cls(**data)
    
    def __repr__(self):
        return f"User({self.user_id}, {self.screen_name})"


class Post:
    """帖子类 - 包含帖子信息和相关操作"""
    
    def __init__(self, 
                 id: str,
                 title: str,
                 content: str,
                 url: str,
                 created_at: datetime,
                 user_id: str,
                 user_name: str,
                 **kwargs):
        self.id = id
        self.title = title
        self.content = content
        self.url = url
        self.created_at = created_at
        self.user_id = user_id
        self.user_name = user_name
        self.stock_code = kwargs.get('stock_code', '')
        self.stock_name = kwargs.get('stock_name', '')
        self.reply_count = kwargs.get('reply_count', 0)
        self.like_count = kwargs.get('like_count', 0)
        self.retweet_count = kwargs.get('retweet_count', 0)
        self.view_count = kwargs.get('view_count', 0)
        self.images = kwargs.get('images', [])
        self.source = kwargs.get('source', '')
        self.is_hot = kwargs.get('is_hot', False)
        self.crawled_at = kwargs.get('crawled_at', datetime.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'created_at': self.created_at,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'reply_count': self.reply_count,
            'like_count': self.like_count,
            'retweet_count': self.retweet_count,
            'view_count': self.view_count,
            'images': ','.join(self.images) if self.images else '',
            'source': self.source,
            'is_hot': self.is_hot,
            'crawled_at': self.crawled_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Post':
        """从字典创建"""
        # 处理字符串格式的 images
        images = data.get('images', [])
        if isinstance(images, str) and images:
            images = images.split(',')
        
        # 处理字符串格式的 created_at
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        crawled_at = data.get('crawled_at')
        if isinstance(crawled_at, str):
            crawled_at = datetime.fromisoformat(crawled_at)
        
        return cls(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            url=data['url'],
            created_at=created_at or datetime.now(),
            user_id=data['user_id'],
            user_name=data['user_name'],
            stock_code=data.get('stock_code', ''),
            stock_name=data.get('stock_name', ''),
            reply_count=data.get('reply_count', 0),
            like_count=data.get('like_count', 0),
            retweet_count=data.get('retweet_count', 0),
            view_count=data.get('view_count', 0),
            images=images,
            source=data.get('source', ''),
            is_hot=data.get('is_hot', False),
            crawled_at=crawled_at or datetime.now()
        )
    
    def to_markdown(self, image_dir: Optional[Path] = None) -> str:
        """转换为 Markdown 格式"""
        md = []
        
        # 标题
        if self.title:
            md.append(f"# {self.title}\n")
        
        # 元信息
        md.append(f"**作者**: {self.user_name}\n")
        md.append(f"**发布时间**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        if self.stock_name:
            md.append(f"**股票**: {self.stock_name}({self.stock_code})\n")
        md.append(f"**回复**: {self.reply_count} | **点赞**: {self.like_count} | **转发**: {self.retweet_count}\n")
        md.append(f"**来源**: [雪球]({self.url})\n")
        md.append("\n---\n")
        
        # 正文
        md.append(f"\n{self.content}\n")
        
        # 图片
        if self.images:
            md.append("\n---\n")
            md.append("\n**图片**:\n")
            for i, img_url in enumerate(self.images, 1):
                if image_dir:
                    # 本地图片路径
                    img_name = f"{self.id}_{i}.jpg"
                    img_path = image_dir / img_name
                    md.append(f"![图片{i}]({img_path})\n")
                else:
                    # 网络图片 URL
                    md.append(f"![图片{i}]({img_url})\n")
        
        return ''.join(md)
    
    def __repr__(self):
        return f"Post(id={self.id}, title={self.title[:20] if self.title else 'None'}...)"