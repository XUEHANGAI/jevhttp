"""测试10086txt首页的HTTP获取、HTML解析和链接发现"""

from test.site_10086txt import SITE_URL, concise_state, create_client, detail_links


client = create_client()
page = client.get(SITE_URL)
state = concise_state(page, include_links=True)
links = detail_links(page)

assert page.status_code == 200
assert page.html is not None
assert page.title
assert page.content_type and 'html' in page.content_type.lower()

print('网页状态码:', page.status_code)
print('网页标题:', page.title)
print('正文长度:', len(page.text))
print('解析链接数:', len(page.links))
print('详情页候选数:', len(links))
print('Decision State字符数:', len(str(state)))
print('详情页示例:', links[:5])
