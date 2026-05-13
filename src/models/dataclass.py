"""
数据类定义 - 用于 API 传输和数据库存储
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class StockData:
    """股票数据"""
    code: str  # 股票代码
    name: str  # 股票名称
    market: str = ""  # 市场 (SH/SZ)
    industry: str = ""  # 行业
    area: str = ""  # 地区
    pe_ratio: float = 0.0  # 市盈率
    pb_ratio: float = 0.0  # 市净率


@dataclass
class UserData:
    """用户数据"""
    user_id: str  # 用户 ID
    screen_name: str  # 昵称
    description: str = ""  # 简介
    profile_image_url: str = ""  # 头像 URL
    followers_count: int = 0  # 粉丝数
    followees_count: int = 0  # 关注数
    status_count: int = 0  # 发帖数


@dataclass
class PostData:
    """帖子数据"""
    id: str  # 帖子 ID
    title: str  # 标题
    content: str  # 正文内容
    url: str  # URL 链接
    created_at: datetime  # 发布时间
    user_id: str  # 用户 ID
    user_name: str  # 用户名
    stock_code: str = ""  # 相关股票代码
    stock_name: str = ""  # 相关股票名称
    reply_count: int = 0  # 回复数
    like_count: int = 0  # 点赞数
    retweet_count: int = 0  # 转发数
    view_count: int = 0  # 阅读数
    images: List[str] = field(default_factory=list)  # 图片 URL 列表
    source: str = ""  # 来源 (Android/iOS/Web)
    is_hot: bool = False  # 是否热门
    crawled_at: datetime = field(default_factory=datetime.now)  # 爬取时间