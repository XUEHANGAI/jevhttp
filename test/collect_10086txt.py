"""采集10086txt公开小说元数据，不下载TXT正文"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from test.site_10086txt import SITE_URL, create_client, detail_links, is_site_url


def page_record(page) -> dict:
    """将网页转换为可保存的公开元数据"""
    return {
        'url': page.final_url,
        'status_code': page.status_code,
        'title': page.title,
        'description': page.description,
        'headings': page.headings[:20],
        'links': [
            {'text': link.text, 'url': link.url}
            for link in page.links
            if is_site_url(link.url)
        ][:100],
        'content_type': page.content_type,
    }


def collect(max_pages: int, output_path: Path, delay: float) -> None:
    """按站内详情页链接采集公开元数据"""
    client = create_client()
    queue = [SITE_URL]
    visited = set()
    records = []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as output_file:
        while queue and len(records) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                page = client.get(url)
            except Exception as exc:
                records.append({'url': url, 'error': str(exc)})
                continue
            records.append(page_record(page))
            output_file.write(
                json.dumps(records[-1], ensure_ascii=False) + '\n'
            )
            output_file.flush()
            for link_url in detail_links(page, limit=max_pages):
                if link_url not in visited and link_url not in queue:
                    queue.append(link_url)
            if delay:
                time.sleep(delay)
    print('采集记录数:', len(records))
    print('输出文件:', output_path)


def main() -> None:
    """解析参数并执行元数据采集"""
    parser = argparse.ArgumentParser(description='采集10086txt公开小说元数据')
    parser.add_argument('--max-pages', type=int, default=20)
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('test/data/10086txt_metadata.jsonl'),
    )
    parser.add_argument('--delay', type=float, default=0.5)
    args = parser.parse_args()
    collect(args.max_pages, args.output, args.delay)


if __name__ == '__main__':
    main()
