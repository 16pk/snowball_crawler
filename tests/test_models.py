"""
测试数据模型
"""
import pytest
from datetime import datetime

from src.models.post import Post, Stock, User
from src.models.dataclass import PostData, StockData, UserData


class TestStock:
    """测试 Stock 类"""
    
    def test_create_stock(self):
        stock = Stock(code='600519', name='贵州茅台', market='SH')
        assert stock.code == '600519'
        assert stock.name == '贵州茅台'
        assert stock.market == 'SH'
    
    def test_stock_to_dict(self):
        stock = Stock(code='600519', name='贵州茅台', market='SH')
        data = stock.to_dict()
        assert data['code'] == '600519'
        assert data['name'] == '贵州茅台'
    
    def test_stock_from_dict(self):
        data = {'code': '600519', 'name': '贵州茅台', 'market': 'SH'}
        stock = Stock.from_dict(data)
        assert stock.code == '600519'


class TestUser:
    """测试 User 类"""
    
    def test_create_user(self):
        user = User(user_id='123', screen_name='测试用户')
        assert user.user_id == '123'
        assert user.screen_name == '测试用户'
    
    def test_user_to_dict(self):
        user = User(user_id='123', screen_name='测试用户')
        data = user.to_dict()
        assert data['user_id'] == '123'
    
    def test_user_from_dict(self):
        data = {'user_id': '123', 'screen_name': '测试用户'}
        user = User.from_dict(data)
        assert user.user_id == '123'


class TestPost:
    """测试 Post 类"""
    
    def test_create_post(self):
        post = Post(
            id='123456',
            title='测试标题',
            content='测试内容',
            url='https://xueqiu.com/123456',
            created_at=datetime.now(),
            user_id='123',
            user_name='测试用户'
        )
        assert post.id == '123456'
        assert post.title == '测试标题'
        assert post.content == '测试内容'
    
    def test_post_to_dict(self):
        post = Post(
            id='123456',
            title='测试标题',
            content='测试内容',
            url='https://xueqiu.com/123456',
            created_at=datetime.now(),
            user_id='123',
            user_name='测试用户',
            like_count=100,
            reply_count=50
        )
        data = post.to_dict()
        assert data['id'] == '123456'
        assert data['like_count'] == 100
    
    def test_post_from_dict(self):
        data = {
            'id': '123456',
            'title': '测试标题',
            'content': '测试内容',
            'url': 'https://xueqiu.com/123456',
            'created_at': datetime.now().isoformat(),
            'user_id': '123',
            'user_name': '测试用户',
            'images': 'url1,url2'
        }
        post = Post.from_dict(data)
        assert post.id == '123456'
        assert post.images == ['url1', 'url2']
    
    def test_post_to_markdown(self):
        post = Post(
            id='123456',
            title='测试标题',
            content='测试内容',
            url='https://xueqiu.com/123456',
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            user_id='123',
            user_name='测试用户',
            like_count=100,
            reply_count=50,
            retweet_count=20
        )
        md = post.to_markdown()
        assert '# 测试标题' in md
        assert '**作者**: 测试用户' in md
        assert '测试内容' in md


if __name__ == '__main__':
    pytest.main([__file__, '-v'])