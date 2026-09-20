"""扫描10086txt全站页面类型并实时保存JSON结果"""

from __future__ import annotations

import argparse
import json
import os
import signal
import threading
import time
from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from test.site_10086txt import SITE_HOST, SITE_URL, create_client
from jevhttp import Page
from jevhttp.url import normalize_url


PAGE_TYPES = [
    '网站首页',
    '小说分类列表页',
    '小说详情页',
    '小说搜索结果页',
    '作者列表页',
    '作者详情页',
    '下载页面',
    '分页列表页',
    '站内导航页',
    '错误页面',
    '空白页面',
    '外部跳转页',
    '其他页面',
]

ALLOWED_QUERY_KEYS = {'id', 'cate', 'auth', 'page', 'p', 'keyword', 'q'}
DOWNLOAD_WORDS = {'下载', '普通下载', '点击下载', 'TXT下载'}


class SiteScanner:
    """使用BFS扫描站内页面并实时保存扫描状态"""

    def __init__(
        self,
        output_dir: Path,
        max_pages: int,
        max_depth: int,
        delay: float,
        max_chars: int,
        workers: int,
    ):
        self.output_dir = output_dir
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.max_chars = max_chars
        self.workers = workers
        self.thread_local = threading.local()
        self.records_path = output_dir / 'pages.jsonl'
        self.summary_path = output_dir / 'summary.json'
        self.checkpoint_path = output_dir / 'checkpoint.json'
        self.stop_requested = False
        self.records = 0
        self.errors = 0
        self.type_counts = Counter()
        self.started_at = time.time()

    def request_stop(self, signum, frame) -> None:
        """响应中断信号并在当前页面处理完后停止"""
        del signum, frame
        self.stop_requested = True
        print('收到停止信号，将在当前页面完成后保存断点')

    @staticmethod
    def is_allowed_url(url: str) -> bool:
        """判断URL是否属于允许扫描的站内页面"""
        try:
            normalized = normalize_url(url)
        except ValueError:
            return False
        parts = urlsplit(normalized)
        if parts.hostname not in {SITE_HOST, '10086txt.com'}:
            return False
        query = parse_qs(parts.query)
        if any(key not in ALLOWED_QUERY_KEYS for key in query):
            return False
        return not any(word in normalized.lower() for word in ('download', '.txt'))

    @staticmethod
    def page_state(page: Page) -> list[dict]:
        """生成不包含正文的页面判断状态"""
        parts = urlsplit(page.final_url)
        query = parse_qs(parts.query)
        link_texts = [link.text for link in page.links if link.text]
        hints = []
        if not query and parts.path in {'', '/'}:
            hints.append('网址结构像网站首页')
        if 'cate' in query:
            hints.append('网址包含小说分类参数cate')
        if 'id' in query:
            hints.append('网址包含内容详情参数id')
        if 'auth' in query:
            hints.append('网址包含作者或站点参数auth')
        if 'page' in query or 'p' in query:
            hints.append('网址包含分页参数')
        return [
            {
                '来源': '页面元数据',
                '网址': page.final_url,
                '路径': parts.path or '/',
                '查询参数': query,
                '网址结构提示': hints,
                '状态码': page.status_code,
                '内容类型': page.content_type,
                '标题': page.title,
                '描述': page.description,
                '标题列表': page.headings[:12],
                '链接数量': len(page.links),
                '链接文字样本': link_texts[:40],
                '包含下载文字': any(
                    text in (link.text or '')
                    for link in page.links
                    for text in DOWNLOAD_WORDS
                ),
            }
        ]

    @staticmethod
    def next_urls(page: Page) -> list[str]:
        """提取下一层可扫描的站内URL并去重"""
        urls = []
        for link in page.links:
            if not SiteScanner.is_allowed_url(link.url):
                continue
            url = normalize_url(link.url)
            if url not in urls:
                urls.append(url)
        return urls

    def get_client(self):
        """为每个工作线程创建独立的模型客户端"""
        if not hasattr(self.thread_local, 'client'):
            self.thread_local.client = create_client()
        return self.thread_local.client

    def classify(
        self,
        client,
        page: Page,
    ) -> tuple[str, str | None, float | None]:
        """使用一次中文Choice决策判断页面类型"""
        result = client.system_one(
            state=self.page_state(page),
            decisions={
                '页面类型': client.choice(
                    PAGE_TYPES,
                    question=(
                        '请根据网址、查询参数、标题、描述和链接特征，'
                        '严格选择最精确的中文页面类型'
                    ),
                    fallback='其他页面',
                )
            },
            max_chars=self.max_chars,
        )
        return result['页面类型'], result.raw, result.decision_time

    def process_page(self, url: str, depth: int) -> tuple[dict, list[str]]:
        """在线程中请求网页、执行分类并返回下一层URL"""
        client = self.get_client()
        started = time.perf_counter()
        record = {
            'url': url,
            'depth': depth,
            'collected_at': time.time(),
        }
        try:
            page = client.get(url, depth=depth)
            page_type, raw, decision_time = self.classify(client, page)
            record.update(
                {
                    'status_code': page.status_code,
                    'final_url': page.final_url,
                    'title': page.title,
                    'description': page.description,
                    'headings': page.headings[:12],
                    'page_type': page_type,
                    'model_raw': raw,
                    'decision_time': decision_time,
                    'request_and_parse_time': time.perf_counter() - started,
                }
            )
            return record, self.next_urls(page)
        except Exception as exc:
            record['error'] = repr(exc)
            record['request_and_parse_time'] = time.perf_counter() - started
            return record, []

    def save_summary(self, queue: deque, visited: set[str]) -> None:
        """实时更新扫描汇总和断点文件"""
        summary = {
            'site': SITE_URL,
            'records': self.records,
            'errors': self.errors,
            'queued': len(queue),
            'visited': len(visited),
            'page_types': dict(self.type_counts),
            'started_at': self.started_at,
            'updated_at': time.time(),
        }
        self._atomic_json_write(self.summary_path, summary)
        self._atomic_json_write(
            self.checkpoint_path,
            {
                'queue': list(queue),
                'visited': sorted(visited),
                'summary': summary,
            },
        )

    @staticmethod
    def _atomic_json_write(path: Path, value: dict) -> None:
        """原子写入JSON，避免中断时留下半个文件"""
        temp_path = path.with_suffix(path.suffix + '.tmp')
        with temp_path.open('w', encoding='utf-8') as output_file:
            json.dump(value, output_file, ensure_ascii=False, indent=2)
            output_file.flush()
            os.fsync(output_file.fileno())
        temp_path.replace(path)

    def scan(self, resume: bool) -> None:
        """执行可恢复的广度优先扫描"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        queue = deque([(SITE_URL, 0)])
        visited = {SITE_URL}
        if resume and self.checkpoint_path.exists():
            checkpoint = json.loads(self.checkpoint_path.read_text(encoding='utf-8'))
            queue = deque(tuple(item) for item in checkpoint['queue'])
            visited = set(checkpoint['visited'])
            previous_summary = checkpoint.get('summary', {})
            self.records = previous_summary.get('records', 0)
            self.errors = previous_summary.get('errors', 0)
            self.type_counts.update(previous_summary.get('page_types', {}))
            self.started_at = previous_summary.get('started_at', self.started_at)
            print('已恢复断点，待处理页面:', len(queue))
        with self.records_path.open('a', encoding='utf-8') as records_file:
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {}
                while (queue or futures) and not self.stop_requested:
                    if not futures and not queue:
                        break
                    while (
                        queue
                        and len(futures) < self.workers
                        and self.records + len(futures) < self.max_pages
                    ):
                        url, depth = queue.popleft()
                        if depth > self.max_depth:
                            continue
                        futures[executor.submit(self.process_page, url, depth)] = (
                            url,
                            depth,
                        )
                    if not futures:
                        break
                    done, _ = wait(
                        futures,
                        return_when=FIRST_COMPLETED,
                    )
                    for future in done:
                        futures.pop(future)
                        record, next_urls = future.result()
                        if 'error' in record:
                            self.errors += 1
                        else:
                            self.type_counts[record['page_type']] += 1
                        self.records += 1
                        for next_url in next_urls:
                            if len(visited) >= self.max_pages:
                                break
                            if next_url not in visited:
                                visited.add(next_url)
                                queue.append((next_url, record['depth'] + 1))
                        records_file.write(
                            json.dumps(record, ensure_ascii=False) + '\n'
                        )
                        records_file.flush()
                        os.fsync(records_file.fileno())
                        self.save_summary(queue, visited)
                        print(
                            f'[{self.records}] {record["url"]} -> '
                            f'{record.get("page_type", "错误")}, '
                            f'队列={len(queue)}, 并发={self.workers}, '
                            f'耗时={record.get("decision_time", 0):.3f}s'
                        )
                        if 'error' in record:
                            print('错误原因:', record['error'])
                        if self.delay:
                            time.sleep(self.delay)
                # 停止信号到来时等待已提交任务，避免断点丢失正在处理的页面
                for future, (url, depth) in list(futures.items()):
                    record, next_urls = future.result()
                    if 'error' in record:
                        self.errors += 1
                    else:
                        self.type_counts[record['page_type']] += 1
                    self.records += 1
                    records_file.write(
                        json.dumps(record, ensure_ascii=False) + '\n'
                    )
                    records_file.flush()
                    os.fsync(records_file.fileno())
                    futures.pop(future)
        self.save_summary(queue, visited)


def main() -> None:
    """解析参数并启动全站扫描"""
    parser = argparse.ArgumentParser(description='扫描10086txt全站页面类型')
    parser.add_argument('--max-pages', type=int, default=100000)
    parser.add_argument('--max-depth', type=int, default=30)
    parser.add_argument('--delay', type=float, default=0.3)
    parser.add_argument('--max-chars', type=int, default=3500)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('test/data/10086txt_scan'),
    )
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    scanner = SiteScanner(
        args.output_dir,
        args.max_pages,
        args.max_depth,
        args.delay,
        args.max_chars,
        args.workers,
    )
    signal.signal(signal.SIGINT, scanner.request_stop)
    signal.signal(signal.SIGTERM, scanner.request_stop)
    scanner.scan(args.resume)


if __name__ == '__main__':
    main()
