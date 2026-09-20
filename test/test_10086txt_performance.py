"""基准测试10086txt页面获取和解析性能"""

import statistics
import time

from test.site_10086txt import SITE_URL, create_client, detail_links


client = create_client()
first_page = client.get(SITE_URL)
urls = [SITE_URL, *detail_links(first_page, limit=19)]
fetch_times = []
success_count = 0
page_sizes = []

for url in urls:
    started = time.perf_counter()
    page = client.get(url)
    fetch_times.append(time.perf_counter() - started)
    if page.status_code == 200:
        success_count += 1
    page_sizes.append(len(page.content))

ordered_times = sorted(fetch_times)
p95_index = min(len(ordered_times) - 1, int(len(ordered_times) * 0.95))

print('测试页面数:', len(urls))
print('成功页面数:', success_count)
print('平均请求耗时(秒):', statistics.mean(fetch_times))
print('中位请求耗时(秒):', statistics.median(fetch_times))
print('P95请求耗时(秒):', ordered_times[p95_index])
print('平均响应大小(字节):', statistics.mean(page_sizes))
