"""
SQLite 数据库存储模块
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.post import Post, Stock, User
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Database:
    """
    SQLite 数据库操作类
    
    表结构:
    - stocks: 股票信息
    - users: 用户信息
    - posts: 帖子信息
    """
    
    def __init__(self, db_path: str):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建股票表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                market TEXT,
                industry TEXT,
                area TEXT,
                pe_ratio REAL,
                pb_ratio REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                screen_name TEXT NOT NULL,
                description TEXT,
                profile_image_url TEXT,
                followers_count INTEGER DEFAULT 0,
                followees_count INTEGER DEFAULT 0,
                status_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建帖子表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                url TEXT,
                created_at TIMESTAMP,
                user_id TEXT,
                user_name TEXT,
                stock_code TEXT,
                stock_name TEXT,
                reply_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                retweet_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                images TEXT,
                source TEXT,
                is_hot BOOLEAN DEFAULT 0,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (stock_code) REFERENCES stocks(code)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_stock ON posts(stock_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_like ON posts(like_count)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_reply ON posts(reply_count)')
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成：{self.db_path}")
    
    def save_stock(self, stock: Stock) -> bool:
        """
        保存股票信息
        
        Args:
            stock: Stock 对象
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO stocks 
                (code, name, market, industry, area, pe_ratio, pb_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                stock.code,
                stock.name,
                stock.market,
                stock.industry,
                stock.area,
                stock.pe_ratio,
                stock.pb_ratio
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存股票失败：{e}")
            return False
        finally:
            conn.close()
    
    def save_user(self, user: User) -> bool:
        """
        保存用户信息
        
        Args:
            user: User 对象
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, screen_name, description, profile_image_url, 
                 followers_count, followees_count, status_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id,
                user.screen_name,
                user.description,
                user.profile_image_url,
                user.followers_count,
                user.followees_count,
                user.status_count
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存用户失败：{e}")
            return False
        finally:
            conn.close()
    
    def save_post(self, post: Post) -> bool:
        """
        保存帖子信息
        
        Args:
            post: Post 对象
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO posts 
                (id, title, content, url, created_at, user_id, user_name,
                 stock_code, stock_name, reply_count, like_count, retweet_count,
                 view_count, images, source, is_hot, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post.id,
                post.title,
                post.content,
                post.url,
                post.created_at,
                post.user_id,
                post.user_name,
                post.stock_code,
                post.stock_name,
                post.reply_count,
                post.like_count,
                post.retweet_count,
                post.view_count,
                ','.join(post.images) if post.images else '',
                post.source,
                post.is_hot,
                post.crawled_at
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存帖子失败：{e}")
            return False
        finally:
            conn.close()
    
    def save_posts(self, posts: List[Post]) -> int:
        """
        批量保存帖子
        
        Args:
            posts: Post 对象列表
        
        Returns:
            成功保存的数量
        """
        count = 0
        for post in posts:
            if self.save_post(post):
                count += 1
        return count
    
    def get_posts(
        self,
        stock_code: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_reply_count: int = 0,
        min_like_count: int = 0,
        limit: int = 1000
    ) -> List[Post]:
        """
        查询帖子
        
        Args:
            stock_code: 股票代码
            user_id: 用户 ID
            start_date: 起始日期
            end_date: 结束日期
            min_reply_count: 最小回复数
            min_like_count: 最小点赞数
            limit: 返回数量限制
        
        Returns:
            Post 对象列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if stock_code:
            conditions.append('stock_code = ?')
            params.append(stock_code)
        
        if user_id:
            conditions.append('user_id = ?')
            params.append(user_id)
        
        if start_date:
            conditions.append('created_at >= ?')
            params.append(start_date.isoformat())
        
        if end_date:
            conditions.append('created_at <= ?')
            params.append(end_date.isoformat())
        
        if min_reply_count > 0:
            conditions.append('reply_count >= ?')
            params.append(min_reply_count)
        
        if min_like_count > 0:
            conditions.append('like_count >= ?')
            params.append(min_like_count)
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        query = f'''
            SELECT * FROM posts 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        '''
        params.append(limit)
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            posts = []
            for row in rows:
                images = row['images'].split(',') if row['images'] else []
                post = Post(
                    id=row['id'],
                    title=row['title'] or '',
                    content=row['content'] or '',
                    url=row['url'] or '',
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                    user_id=row['user_id'] or '',
                    user_name=row['user_name'] or '',
                    stock_code=row['stock_code'] or '',
                    stock_name=row['stock_name'] or '',
                    reply_count=row['reply_count'] or 0,
                    like_count=row['like_count'] or 0,
                    retweet_count=row['retweet_count'] or 0,
                    view_count=row['view_count'] or 0,
                    images=images,
                    source=row['source'] or '',
                    is_hot=bool(row['is_hot']),
                    crawled_at=datetime.fromisoformat(row['crawled_at']) if row['crawled_at'] else datetime.now()
                )
                posts.append(post)
            
            return posts
            
        except Exception as e:
            logger.error(f"查询帖子失败：{e}")
            return []
        finally:
            conn.close()
    
    def get_post_count(
        self,
        stock_code: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> int:
        """
        获取帖子数量
        
        Args:
            stock_code: 股票代码
            user_id: 用户 ID
        
        Returns:
            帖子数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if stock_code:
            conditions.append('stock_code = ?')
            params.append(stock_code)
        
        if user_id:
            conditions.append('user_id = ?')
            params.append(user_id)
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        cursor.execute(f'SELECT COUNT(*) FROM posts WHERE {where_clause}', params)
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """获取所有股票"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM stocks ORDER BY code')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY screen_name')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def close(self):
        """关闭数据库连接（如果需要）"""
        pass  # SQLite 连接在使用后会自动关闭