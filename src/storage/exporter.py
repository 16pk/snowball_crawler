"""
Markdown 导出模块
"""
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..models.post import Post, Stock, User
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownExporter:
    """
    Markdown 导出器
    
    功能:
    - 将帖子导出为 Markdown 格式
    - 支持批量导出
    - 支持图片下载和本地引用
    """
    
    def __init__(self, export_dir: str, download_images: bool = False):
        """
        初始化导出器
        
        Args:
            export_dir: 导出目录
            download_images: 是否下载图片
        """
        self.export_dir = Path(export_dir)
        self.download_images = download_images
        self.image_dir = self.export_dir / 'images'
        
        if self.download_images:
            self.image_dir.mkdir(parents=True, exist_ok=True)
    
    def export_post(
        self,
        post: Post,
        filename: Optional[str] = None,
        save_local: bool = True
    ) -> Path:
        """
        导出单个帖子为 Markdown
        
        Args:
            post: Post 对象
            filename: 文件名 (可选，默认使用帖子 ID)
            save_local: 是否保存到本地文件
        
        Returns:
            保存的文件路径
        """
        # 确定文件名
        if filename is None:
            # 使用标题或 ID 作为文件名
            if post.title:
                # 清理标题中的非法字符
                safe_title = self._sanitize_filename(post.title[:50])
                filename = f"{post.id}_{safe_title}"
            else:
                filename = post.id
        
        # 生成 Markdown 内容
        md_content = self._generate_markdown(post)
        
        if save_local:
            # 保存文件
            output_path = self.export_dir / f"{filename}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"导出帖子：{output_path}")
            return output_path
        else:
            # 返回临时路径
            return Path(f"{filename}.md")
    
    def export_posts(
        self,
        posts: List[Post],
        prefix: str = "",
        group_by_date: bool = False
    ) -> List[Path]:
        """
        批量导出帖子
        
        Args:
            posts: Post 对象列表
            prefix: 文件名前缀
            group_by_date: 是否按日期分组 (创建子目录)
        
        Returns:
            保存的文件路径列表
        """
        paths = []
        
        if not posts:
            logger.warning("没有帖子需要导出")
            return paths
        
        logger.info(f"开始导出 {len(posts)} 篇帖子")
        
        for i, post in enumerate(posts, 1):
            logger.info(f"导出第 {i}/{len(posts)} 篇帖子")
            
            # 确定文件名前缀
            filename_prefix = prefix
            if not filename_prefix:
                if post.stock_code:
                    filename_prefix = f"{post.stock_code}_{post.stock_name}"
                elif post.user_name:
                    filename_prefix = post.user_name
            
            # 按日期分组
            if group_by_date:
                date_str = post.created_at.strftime('%Y-%m')
                subdir = self.export_dir / date_str
                subdir.mkdir(parents=True, exist_ok=True)
                temp_exporter = MarkdownExporter(str(subdir), self.download_images)
                path = temp_exporter.export_post(post, save_local=True)
            else:
                path = self.export_post(post, save_local=True)
            
            paths.append(path)
        
        logger.info(f"导出完成，共 {len(paths)} 个文件")
        return paths
    
    def export_summary(
        self,
        posts: List[Post],
        stock: Optional[Stock] = None,
        user: Optional[User] = None
    ) -> Path:
        """
        导出汇总报告
        
        Args:
            posts: Post 对象列表
            stock: 股票对象 (可选)
            user: 用户对象 (可选)
        
        Returns:
            汇总报告路径
        """
        md = []
        
        # 标题
        if stock:
            md.append(f"# {stock.name}({stock.code}) 讨论贴汇总\n")
        elif user:
            md.append(f"# {user.screen_name} 发帖汇总\n")
        else:
            md.append("# 帖子汇总\n")
        
        # 汇总信息
        md.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append(f"**帖子总数**: {len(posts)}\n")
        
        if posts:
            # 统计信息
            total_likes = sum(p.like_count for p in posts)
            total_replies = sum(p.reply_count for p in posts)
            total_retweets = sum(p.retweet_count for p in posts)
            
            md.append(f"**总点赞数**: {total_likes}\n")
            md.append(f"**总回复数**: {total_replies}\n")
            md.append(f"**总转发数**: {total_retweets}\n")
            
            # 日期范围
            dates = [p.created_at for p in posts]
            md.append(f"**最早发帖**: {min(dates).strftime('%Y-%m-%d')}\n")
            md.append(f"**最晚发帖**: {max(dates).strftime('%Y-%m-%d')}\n")
            
            # 热门帖子 (按点赞数)
            md.append("\n---\n")
            md.append("\n## 热门帖子 (按点赞数)\n")
            
            top_posts = sorted(posts, key=lambda x: x.like_count, reverse=True)[:10]
            for i, post in enumerate(top_posts, 1):
                md.append(f"\n### {i}. {post.title or '无标题'}\n")
                md.append(f"- **作者**: {post.user_name}\n")
                md.append(f"- **时间**: {post.created_at.strftime('%Y-%m-%d')}\n")
                md.append(f"- **点赞**: {post.like_count} | **回复**: {post.reply_count}\n")
                md.append(f"- **链接**: [{post.id}]({post.url})\n")
        
        # 帖子列表
        md.append("\n---\n")
        md.append("\n## 完整帖子列表\n")
        md.append("\n| 标题 | 作者 | 时间 | 点赞 | 回复 | 链接 |\n")
        md.append("|------|------|------|------|------|------|\n")
        
        for post in posts[:100]:  # 限制 100 条
            title = (post.title or '无标题')[:30]
            md.append(f"| {title} | {post.user_name} | {post.created_at.strftime('%Y-%m-%d')} | {post.like_count} | {post.reply_count} | [链接]({post.url}) |\n")
        
        if len(posts) > 100:
            md.append(f"\n... 还有 {len(posts) - 100} 篇帖子，请查看单独的文件\n")
        
        # 保存文件
        output_path = self.export_dir / 'SUMMARY.md'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(md))
        
        logger.info(f"汇总报告已保存：{output_path}")
        return output_path
    
    def _generate_markdown(self, post: Post) -> str:
        """
        生成 Markdown 内容
        
        Args:
            post: Post 对象
        
        Returns:
            Markdown 字符串
        """
        md = []
        
        # 标题
        if post.title:
            md.append(f"# {post.title}\n\n")
        
        # 元信息
        md.append(f"**作者**: {post.user_name}\n\n")
        md.append(f"**发布时间**: {post.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if post.stock_name:
            md.append(f"**股票**: {post.stock_name}({post.stock_code})\n\n")
        
        md.append(f"**互动数据**:\n")
        md.append(f"- 💬 回复：{post.reply_count}\n")
        md.append(f"- 👍 点赞：{post.like_count}\n")
        md.append(f"- 🔁 转发：{post.retweet_count}\n")
        md.append(f"- 👁 阅读：{post.view_count}\n\n")
        
        md.append(f"**来源**: [雪球]({post.url})\n\n")
        md.append("---\n\n")
        
        # 正文
        md.append("## 正文\n\n")
        md.append(f"{post.content}\n\n")
        
        # 图片
        if post.images:
            md.append("---\n\n")
            md.append("## 图片\n\n")
            
            for i, img_url in enumerate(post.images, 1):
                if self.download_images and img_url:
                    # 下载图片并保存
                    img_path = self._download_image(img_url, post.id, i)
                    if img_path:
                        md.append(f"![图片{i}]({img_path})\n\n")
                    else:
                        md.append(f"![图片{i}]({img_url})\n\n")
                else:
                    md.append(f"![图片{i}]({img_url})\n\n")
        
        return ''.join(md)
    
    def _download_image(
        self,
        url: str,
        post_id: str,
        index: int
    ) -> Optional[Path]:
        """
        下载图片
        
        Args:
            url: 图片 URL
            post_id: 帖子 ID
            index: 图片序号
        
        Returns:
            本地图片路径，下载失败返回 None
        """
        if not self.download_images:
            return None
        
        try:
            import requests
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 确定文件名
            img_name = f"{post_id}_{index}.jpg"
            img_path = self.image_dir / img_name
            
            with open(img_path, 'wb') as f:
                f.write(response.content)
            
            # 返回相对路径
            return Path('images') / img_name
            
        except Exception as e:
            logger.error(f"下载图片失败：{url}, 错误：{e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的非法字符
        
        Args:
            filename: 原文件名
        
        Returns:
            清理后的文件名
        """
        # 移除非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '')
        
        # 替换空格为下划线
        filename = filename.replace(' ', '_')
        
        return filename.strip('_.')