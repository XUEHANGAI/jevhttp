"""定义网页响应数据结构和HTML基础抽取器"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Mapping

from .url import normalize_url


@dataclass(frozen=True)
class Link:
    """保存一个网页链接"""

    url: str
    text: str | None = None
    title: str | None = None
    rel: str | None = None


class _HTMLParser(HTMLParser):
    """抽取标题、元数据、正文、标题节点和链接"""

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title: list[str] = []
        self.description: str | None = None
        self.headings: list[str] = []
        self.links: list[Link] = []
        self._text: list[str] = []
        self._capture: str | None = None
        self._buffer: list[str] = []
        self._link_attrs: dict[str, str] | None = None

    @staticmethod
    def _clean(value: str) -> str:
        """清理连续空白字符"""
        return ' '.join(value.split())

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        """处理HTML开始标签"""
        data = {key.lower(): value or '' for key, value in attrs}
        lower_tag = tag.lower()
        if lower_tag == 'meta' and data.get('name', '').lower() == 'description':
            self.description = self._clean(data.get('content', '')) or None
        if lower_tag == 'a' and data.get('href'):
            try:
                href = normalize_url(data['href'], self.base_url)
            except ValueError:
                return
            self._link_attrs = {
                'url': href,
                'title': data.get('title', ''),
                'rel': data.get('rel', ''),
            }
            self._buffer = []
        if lower_tag == 'title' or lower_tag in {f'h{i}' for i in range(1, 7)}:
            self._capture = lower_tag
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        """处理HTML结束标签"""
        lower_tag = tag.lower()
        value = self._clean(' '.join(self._buffer))
        if self._capture == lower_tag:
            if lower_tag == 'title' and value:
                self.title.append(value)
            elif lower_tag.startswith('h') and value:
                self.headings.append(value)
            self._capture = None
            self._buffer = []
        if lower_tag == 'a' and self._link_attrs is not None:
            self.links.append(
                Link(
                    self._link_attrs['url'],
                    value or None,
                    self._link_attrs['title'] or None,
                    self._link_attrs['rel'] or None,
                )
            )
            self._link_attrs = None

    def handle_data(self, data: str) -> None:
        """处理HTML文本节点"""
        if self._capture or self._link_attrs is not None:
            self._buffer.append(data)
        if data.strip():
            self._text.append(data)


@dataclass
class Page:
    """保存HTTP响应及其网页抽取结果"""

    url: str
    final_url: str
    status_code: int
    headers: Mapping[str, str]
    content: bytes
    html: str | None
    text: str
    title: str | None = None
    description: str | None = None
    headings: list[str] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    content_type: str | None = None
    depth: int = 0

    @classmethod
    def from_response(cls, response, depth: int = 0) -> 'Page':
        """将requests响应转换为``Page``"""
        content_type = response.headers.get('Content-Type')
        is_html = content_type is None or any(
            marker in content_type.lower() for marker in ('html', 'xhtml')
        )
        html = response.text if is_html else None
        parser = _HTMLParser(response.url) if html is not None else None
        if parser:
            parser.feed(html)
            text = ' '.join(' '.join(parser._text).split())
            title = parser.title[0] if parser.title else None
            description = parser.description
            headings, links = parser.headings, parser.links
        else:
            text, title, description, headings, links = '', None, None, [], []
        return cls(
            response.request.url,
            response.url,
            response.status_code,
            dict(response.headers),
            response.content,
            html,
            text,
            title,
            description,
            headings,
            links,
            content_type,
            depth,
        )

    def to_state(self, max_chars: int = 8000, max_links: int = 100) -> dict:
        """将网页转换为适合模型处理的JSON状态"""
        state = {
            'url': self.url,
            'final_url': self.final_url,
            'status_code': self.status_code,
            'title': self.title,
            'description': self.description,
            'headings': self.headings,
            'content': self.text[:max_chars],
            'links': [
                {
                    'url': link.url,
                    'text': link.text,
                    'title': link.title,
                    'rel': link.rel,
                }
                for link in self.links[:max_links]
            ],
        }
        state['content_truncated'] = len(self.text) > max_chars
        return state
