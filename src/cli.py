"""
命令行接口模块
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import click
import yaml

from .crawler import XueqiuAPIClient, StockCrawler, UserCrawler
from .storage import Database, MarkdownExporter
from .utils.cookie import CookieManager
from .utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    config_file = Path(config_path)
    if not config_file.exists():
        # 尝试默认路径
        default_config = Path(__file__).parent.parent / 'config' / 'config.yaml'
        if default_config.exists():
            config_file = default_config
        else:
            logger.warning(f"配置文件不存在：{config_path}")
            return {}
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@click.group()
@click.option(
    '--config', '-c',
    default='config/config.yaml',
    help='配置文件路径 (默认：config/config.yaml)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='显示详细日志'
)
@click.pass_context
def cli(ctx, config: str, verbose: bool):
    """
    雪球网爬虫工具
    
    用于爬取雪球网上股票讨论贴和用户发帖。
    
    使用前请确保:
    1. 已配置 Cookie (见 config/config.yaml.example)
    2. 已安装依赖：pip install -r requirements.txt
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config(config)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        get_logger('snowball_crawler', level=10)  # DEBUG level


@cli.command()
@click.option(
    '--stock', '-s',
    'stock_query',
    help='股票名称或代码 (如：贵州茅台 或 600519)'
)
@click.option(
    '--user', '-u',
    'user_query',
    help='用户名或用户 ID'
)
@click.option(
    '--start-date',
    type=str,
    help='起始日期 (格式：YYYY-MM-DD，默认：5 年前)'
)
@click.option(
    '--end-date',
    type=str,
    help='结束日期 (格式：YYYY-MM-DD，默认：今天)'
)
@click.option(
    '--min-replies',
    type=int,
    default=0,
    help='最小回复数 (默认：0)'
)
@click.option(
    '--min-likes',
    type=int,
    default=0,
    help='最小点赞数 (默认：0)'
)
@click.option(
    '--max-pages',
    type=int,
    default=100,
    help='最大爬取页数 (默认：100)'
)
@click.option(
    '--output', '-o',
    type=str,
    default='data/export',
    help='输出目录 (默认：data/export)'
)
@click.option(
    '--no-db',
    is_flag=True,
    help='不保存到数据库'
)
@click.option(
    '--download-images',
    is_flag=True,
    help='下载图片到本地'
)
@click.pass_context
def crawl(
    ctx,
    stock_query: Optional[str],
    user_query: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    min_replies: int,
    min_likes: int,
    max_pages: int,
    output: str,
    no_db: bool,
    download_images: bool
):
    """
    爬取股票讨论贴或用户发帖
    
    示例:
    
    \b
    # 爬取贵州茅台的讨论贴
    snowball crawl --stock 贵州茅台
    
    # 爬取某用户的发帖
    snowball crawl --user 某用户 ID
    
    # 爬取并下载图片
    snowball crawl --stock 600519 --download-images
    
    # 设置过滤条件
    snowball crawl --stock 000001 --min-replies 10 --min-likes 50
    """
    config = ctx.obj['config']
    
    # 检查输入
    if not stock_query and not user_query:
        click.echo("❌ 错误：请指定 --stock 或 --user 参数")
        click.echo("使用 --help 查看用法")
        sys.exit(1)
    
    if stock_query and user_query:
        click.echo("❌ 错误：--stock 和 --user 不能同时指定")
        sys.exit(1)
    
    # 初始化组件
    cookie_manager = CookieManager(config)
    if not cookie_manager.is_valid():
        click.echo("❌ 错误：Cookie 未配置")
        click.echo("请编辑 config/config.yaml 文件，填入有效的 Cookie")
        click.echo("详见 config/config.yaml.example")
        sys.exit(1)
    
    api_client = XueqiuAPIClient(cookie_manager, config)
    
    # 解析日期
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = end_date - timedelta(days=1825)  # 默认 5 年
    
    # 创建输出目录
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    db = None
    if not no_db:
        db_config = config.get('storage', {})
        db_path = db_config.get('database_path', 'data/db/snowball.db')
        db = Database(db_path)
    
    # 爬取股票
    if stock_query:
        click.echo(f"🔍 搜索股票：{stock_query}")
        stock_crawler = StockCrawler(api_client)
        stocks = stock_crawler.search_stock(stock_query)
        
        if not stocks:
            click.echo(f"❌ 未找到股票：{stock_query}")
            sys.exit(1)
        
        # 如果有多个结果，选择第一个
        stock = stocks[0]
        if len(stocks) > 1:
            click.echo(f"找到多个股票，使用第一个：{stock}")
        
        click.echo(f"📈 爬取股票：{stock.name}({stock.code})")
        click.echo(f"📅 日期范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        click.echo(f"📊 过滤条件：回复>={min_replies}, 点赞>={min_likes}")
        
        posts = stock_crawler.crawl_posts(
            stock=stock,
            start_date=start_date,
            end_date=end_date,
            min_reply_count=min_replies,
            min_like_count=min_likes,
            max_pages=max_pages
        )
        
        # 保存股票信息
        if db:
            db.save_stock(stock)
        
        click.echo(f"✅ 爬取完成，共 {len(posts)} 篇帖子")
    
    # 爬取用户
    else:
        click.echo(f"🔍 搜索用户：{user_query}")
        user_crawler = UserCrawler(api_client)
        
        # 尝试直接使用 user_query 作为 user_id
        user = user_crawler.get_user_by_id(user_query)
        
        if not user:
            # 尝试搜索
            users = user_crawler.search_user(user_query)
            if users:
                user = users[0]
        
        if not user:
            click.echo(f"❌ 未找到用户：{user_query}")
            sys.exit(1)
        
        click.echo(f"👤 爬取用户：{user.screen_name}({user.user_id})")
        click.echo(f"📅 日期范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        click.echo(f"📊 过滤条件：回复>={min_replies}, 点赞>={min_likes}")
        
        posts = user_crawler.crawl_posts(
            user=user,
            start_date=start_date,
            end_date=end_date,
            min_reply_count=min_replies,
            min_like_count=min_likes,
            max_pages=max_pages
        )
        
        # 保存用户信息
        if db:
            db.save_user(user)
        
        click.echo(f"✅ 爬取完成，共 {len(posts)} 篇帖子")
    
    # 保存到数据库
    if db and posts:
        click.echo("💾 保存到数据库...")
        saved_count = db.save_posts(posts)
        click.echo(f"✅ 已保存 {saved_count} 篇帖子到数据库")
    
    # 导出为 Markdown
    if posts:
        click.echo(f"📝 导出为 Markdown...")
        exporter = MarkdownExporter(str(output_path), download_images=download_images)
        
        # 导出汇总报告
        if stock_query:
            exporter.export_summary(posts, stock=stock)
        else:
            exporter.export_summary(posts, user=user)
        
        # 导出所有帖子
        exporter.export_posts(posts)
        
        click.echo(f"✅ 导出完成，输出目录：{output_path.absolute()}")


@cli.command()
@click.option(
    '--stock', '-s',
    help='股票代码'
)
@click.option(
    '--user', '-u',
    help='用户 ID'
)
@click.option(
    '--output', '-o',
    type=str,
    default='data/export',
    help='输出目录'
)
@click.option(
    '--download-images',
    is_flag=True,
    help='下载图片'
)
@click.pass_context
def export(
    ctx,
    stock: Optional[str],
    user: Optional[str],
    output: str,
    download_images: bool
):
    """
    从数据库导出帖子为 Markdown
    
    示例:
    
    \b
    # 导出某股票的帖子
    snowball export --stock 600519
    
    # 导出某用户的帖子
    snowball export --user 123456
    """
    config = ctx.obj['config']
    
    if not stock and not user:
        click.echo("❌ 错误：请指定 --stock 或 --user 参数")
        sys.exit(1)
    
    # 初始化数据库
    db_config = config.get('storage', {})
    db_path = db_config.get('database_path', 'data/db/snowball.db')
    db = Database(db_path)
    
    # 查询帖子
    if stock:
        click.echo(f"📈 查询股票 {stock} 的帖子...")
        posts = db.get_posts(stock_code=stock)
    else:
        click.echo(f"👤 查询用户 {user} 的帖子...")
        posts = db.get_posts(user_id=user)
    
    if not posts:
        click.echo("❌ 未找到帖子")
        sys.exit(1)
    
    click.echo(f"找到 {len(posts)} 篇帖子")
    
    # 导出
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    exporter = MarkdownExporter(str(output_path), download_images=download_images)
    exporter.export_posts(posts)
    exporter.export_summary(posts)
    
    click.echo(f"✅ 导出完成：{output_path.absolute()}")


@cli.command()
@click.pass_context
def init_config(ctx):
    """
    初始化配置文件
    
    复制示例配置文件到 config/config.yaml
    """
    src = Path(__file__).parent.parent / 'config' / 'config.yaml.example'
    dst = Path('config') / 'config.yaml'
    
    if not src.exists():
        click.echo("❌ 错误：示例配置文件不存在")
        sys.exit(1)
    
    if dst.exists():
        click.echo("⚠️  配置文件已存在，是否覆盖？")
        if not click.confirm("确认覆盖？"):
            sys.exit(0)
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(content)
    
    click.echo(f"✅ 配置文件已创建：{dst}")
    click.echo("\n请编辑配置文件，填入有效的 Cookie")
    click.echo("详见文件中的注释说明")


@cli.command()
@click.pass_context
def version(ctx):
    """显示版本信息"""
    from . import __version__
    click.echo(f"snowball_crawler v{__version__}")


def main():
    """主入口"""
    cli(obj={})


if __name__ == '__main__':
    main()