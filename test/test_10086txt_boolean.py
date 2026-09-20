"""测试10086txt页面是否属于小说站点"""

from test.site_10086txt import SITE_URL, concise_state, create_client


client = create_client()
page = client.get(SITE_URL)
result = client.system_one(
    state=concise_state(page),
    decisions={
        '是否为小说相关页面': client.boolean(
            '这个页面是否与小说阅读、小说分类或小说下载有关？'
        )
    },
)

print('是否为小说相关页面:', result['是否为小说相关页面'])
print('模型原始结果:', result.raw)
print('决策耗时(秒):', result.decision_time)
