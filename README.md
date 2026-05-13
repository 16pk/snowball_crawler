# 雪球网爬虫工具 (Snowball Crawler)

一个用于爬取雪球网股票讨论贴和用户发帖的 Python 爬虫工具。

## 功能特性

- ✅ **股票爬取**: 根据股票名称或代码爬取讨论贴
- ✅ **用户爬取**: 根据用户名或 ID 爬取用户发帖
- ✅ **日期过滤**: 支持自定义起始日期，默认爬取最近 5 年
- ✅ **数据过滤**: 支持按最低回复数、最低点赞数过滤
- ✅ **数据存储**: SQLite 数据库存储，支持查询和导出
- ✅ **Markdown 导出**: 导出为 Markdown 格式，支持图片下载
- ✅ **命令行接口**: 简单易用的 CLI 工具

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Cookie

```bash
# 复制示例配置文件
cp config/config.yaml.example config/config.yaml
```

**获取 Cookie 步骤：**

1. 打开浏览器 (Chrome/Firefox/Edge)
2. 访问 https://xueqiu.com 并登录账号
3. 按 F12 打开开发者工具
4. 刷新页面，在 Network 标签中找到任意请求
5. 点击请求，在 Request Headers 中找到 Cookie 字段
6. 复制整个 Cookie 值，粘贴到 `config/config.yaml` 的 `raw_cookie` 字段

### 3. 使用示例

```bash
# 安装为命令行工具 (可选)
pip install -e .

# 爬取贵州茅台的讨论贴
snowball crawl --stock 贵州茅台

# 爬取某股票的讨论贴 (使用代码)
snowball crawl --stock 600519

# 爬取某用户的发帖
snowball crawl --user 123456789

# 设置日期范围和过滤条件
snowball crawl --stock 000001 \
    --start-date 2023-01-01 \
    --end-date 2024-01-01 \
    --min-replies 10 \
    --min-likes 50

# 爬取并下载图片
snowball crawl --stock 600519 --download-images

# 从数据库导出
snowball export --stock 600519

# 查看帮助
snowball --help
```

## 命令行参数

### crawl 命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--stock, -s` | 股票名称或代码 | 必填 (与 user 互斥) |
| `--user, -u` | 用户名或用户 ID | 必填 (与 stock 互斥) |
| `--start-date` | 起始日期 (YYYY-MM-DD) | 5 年前 |
| `--end-date` | 结束日期 (YYYY-MM-DD) | 今天 |
| `--min-replies` | 最小回复数 | 0 |
| `--min-likes` | 最小点赞数 | 0 |
| `--max-pages` | 最大爬取页数 | 100 |
| `--output, -o` | 输出目录 | data/export |
| `--no-db` | 不保存到数据库 | False |
| `--download-images` | 下载图片到本地 | False |

### export 命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--stock, -s` | 股票代码 | 必填 (与 user 互斥) |
| `--user, -u` | 用户 ID | 必填 (与 stock 互斥) |
| `--output, -o` | 输出目录 | data/export |
| `--download-images` | 下载图片 | False |

## 项目结构

```
snowball_crawler/
├── config/
│   └── config.yaml.example    # 配置文件示例
├── src/
│   ├── __init__.py
│   ├── cli.py                 # 命令行接口
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── api_client.py      # API 客户端
│   │   ├── stock_crawler.py   # 股票爬虫
│   │   ├── user_crawler.py    # 用户爬虫
│   │   └── post_crawler.py    # 帖子爬虫
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dataclass.py       # 数据类
│   │   └── post.py            # 模型类
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py        # 数据库操作
│   │   └── exporter.py        # Markdown 导出
│   └── utils/
│       ├── __init__.py
│       ├── cookie.py          # Cookie 管理
│       └── logger.py          # 日志
├── data/                       # 数据目录 (自动生成)
│   ├── db/                     # SQLite 数据库
│   ├── images/                 # 图片 (可选下载)
│   └── export/                 # 导出的 Markdown
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 输出格式

### Markdown 文件

每个帖子导出为一个 Markdown 文件，包含：
- 标题
- 作者、发布时间
- 互动数据 (回复、点赞、转发、阅读)
- 正文内容
- 图片 (URL 或本地路径)

### 汇总报告

`SUMMARY.md` 包含：
- 帖子总数
- 总互动数统计
- 日期范围
- 热门帖子 Top 10
- 完整帖子列表 (前 100 条)

### 数据库

SQLite 数据库包含三张表：
- `stocks`: 股票信息
- `users`: 用户信息
- `posts`: 帖子信息

## 注意事项

1. **Cookie 有效期**: 雪球网的 Cookie 会过期，如果爬虫失效，请重新获取 Cookie
2. **爬取频率**: 默认设置了 1 秒延迟，请勿调低以免被封 IP
3. **合规使用**: 请遵守雪球网 robots.txt 协议，仅用于个人学习/研究
4. **数据量**: 爬取 5 年数据可能需要较长时间，建议设置合适的过滤条件

## 技术栈

- Python 3.8+
- requests - HTTP 请求
- click - 命令行接口
- sqlite3 - 数据库
- PyYAML - 配置文件
- tenacity - 重试机制

## 现有工具对比

| 项目 | 语言 | Stars | 特点 |
|------|------|-------|------|
| [XueQiuSuperSpider](https://github.com/decaywood/XueQiuSuperSpider) | Java | 2366+ | 功能完善，支持分布式 |
| snowball_crawler (本项目) | Python | - | 简单易用，CLI 友好 |

## 常见问题

### Q: Cookie 如何获取？

A: 详见上方"配置 Cookie"章节，需要从浏览器开发者工具中复制。

### Q: 爬取失败怎么办？

A: 
1. 检查 Cookie 是否有效
2. 检查网络连接
3. 可能是雪球网 API 变更，请查看 issue

### Q: 如何修改爬取频率？

A: 编辑 `config/config.yaml`，修改 `request.delay` 值 (单位：秒)。

### Q: 图片存储格式建议？

A: 
- **推荐**: SQLite 存储元数据 + 图片 URL，不下载图片
- **需要离线查看**: 使用 `--download-images` 下载图片到本地

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！