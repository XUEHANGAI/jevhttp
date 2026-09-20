"""提供10086txt测试共享配置和精简网页状态"""

from __future__ import annotations

import os
from urllib.parse import urlsplit

from jevhttp import JevHttp, Page


os.environ.setdefault('NO_PROXY', '127.0.0.1,localhost')

SITE_URL = 'https://www.10086txt.com/'
SITE_HOST = 'www.10086txt.com'
MODEL_URL = 'http://127.0.0.1:8000/v1'
MODEL_NAME = 'openbmb/MiniCPM5-2B'


def create_client() -> JevHttp:
    """创建连接本地vLLM的测试客户端"""
    return JevHttp(
        base_url=MODEL_URL,
        api_key='EMPTY',
        model=MODEL_NAME,
        timeout=60,
        max_retries=1,
    )


def is_site_url(url: str) -> bool:
    """判断URL是否属于10086txt主站"""
    return urlsplit(url).hostname in {SITE_HOST, '10086txt.com'}


def concise_state(page: Page, include_links: bool = False) -> list[dict]:
    """从网页生成低长度Decision State，不发送完整正文"""
    state = [
        {
            '来源': '网页元数据',
            '网址': page.final_url,
            '状态码': page.status_code,
            '内容类型': page.content_type,
            '标题': page.title,
            '描述': page.description,
            '标题列表': page.headings[:10],
        }
    ]
    if include_links:
        state.append(
            {
                '来源': '站内链接摘要',
                '链接': [
                    {'文字': link.text, '网址': link.url}
                    for link in page.links
                    if is_site_url(link.url)
                ][:100],
            }
        )
    return state


def detail_links(page: Page, limit: int = 20) -> list[str]:
    """提取站内详情页候选URL，不包含下载链接"""
    urls = []
    for link in page.links:
        if not is_site_url(link.url) or link.url in urls:
            continue
        if 'download' in link.url.lower() or '下载' in (link.text or ''):
            continue
        if '?id=' in link.url:
            urls.append(link.url)
        if len(urls) >= limit:
            break
    return urls
