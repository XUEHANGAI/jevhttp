"""实现带安全边界和robots限制的同步广度优先爬虫"""

from __future__ import annotations

import time
import urllib.robotparser
from collections import deque
from dataclasses import dataclass
from urllib.parse import urlsplit

from .url import is_private_host, normalize_url


@dataclass
class CrawlConfig:
    """保存爬虫运行配置"""

    max_pages: int = 1000
    max_depth: int = 5
    same_domain: bool = True
    allowed_domains: list[str] | None = None
    respect_robots_txt: bool = True
    delay: float = 0.2
    on_ai_error: str = 'skip'
    block_private_hosts: bool = True


@dataclass
class CrawlItem:
    """保存单个爬虫结果"""

    page: object
    action: str
    saved: bool
    error: Exception | None = None


class Crawler:
    """使用同步队列执行受限网页遍历"""

    def __init__(self, client, config: CrawlConfig | None = None):
        self.client = client
        self.config = config or CrawlConfig()

    def crawl(
        self,
        seed_url: str,
        goal: str,
        *,
        max_pages: int | None = None,
        max_depth: int | None = None,
        **kwargs,
    ):
        """按照中文动作决策遍历网页并逐个返回结果"""
        config_values = {**self.config.__dict__, **kwargs}
        config = CrawlConfig(**config_values)
        if max_pages is not None:
            config.max_pages = max_pages
        if max_depth is not None:
            config.max_depth = max_depth
        seed = normalize_url(seed_url)
        seed_host = urlsplit(seed).hostname or ''
        allowed_domains = set(
            config.allowed_domains or ([seed_host] if config.same_domain else [])
        )
        queue = deque([(seed, 0)])
        visited = set()
        robots = {}
        while queue and len(visited) < config.max_pages:
            url, depth = queue.popleft()
            if url in visited or depth > config.max_depth:
                continue
            host = urlsplit(url).hostname or ''
            if (
                allowed_domains and host not in allowed_domains
            ) or (
                config.block_private_hosts and is_private_host(host)
            ):
                continue
            if config.respect_robots_txt:
                parser = robots.setdefault(host, self._robots(host, url))
                if parser and not parser.can_fetch('jevhttp/0.1', url):
                    visited.add(url)
                    continue
            visited.add(url)
            try:
                page = self.client.get(url, depth=depth)
                decision = self.client.system_one(
                    page.to_state(),
                    {
                        'action': self.client.choice(
                            ['保存', '跟随', '保存并跟随', '跳过'],
                            question='请选择后续动作',
                        ),
                        'relevance': self.client.score(
                            goal,
                            min=0,
                            max=1,
                        ),
                    },
                )
                action = decision.action
                item = CrawlItem(
                    page,
                    action,
                    action in {'保存', '保存并跟随'},
                )
            except Exception as exc:
                if config.on_ai_error == 'stop':
                    raise
                item = CrawlItem(locals().get('page'), '跳过', False, exc)
                yield item
                continue
            yield item
            if action in {'跟随', '保存并跟随'} and depth < config.max_depth:
                for link in page.links:
                    if link.url not in visited:
                        queue.append((link.url, depth + 1))
            if config.delay:
                time.sleep(config.delay)

    def _robots(self, host: str, url: str):
        """读取站点robots.txt，读取失败时不阻断当前页面"""
        try:
            parts = urlsplit(url)
            robots_url = f'{parts.scheme}://{host}/robots.txt'
            response = self.client.session.get(
                robots_url,
                timeout=self.client.timeout,
            )
            if response.ok:
                parser = urllib.robotparser.RobotFileParser()
                parser.set_url(robots_url)
                parser.parse(response.text.splitlines())
                return parser
        except Exception:
            pass
        return None
