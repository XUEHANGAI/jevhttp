"""测试10086txt页面与小说元数据采集任务的相关性"""

from test.site_10086txt import SITE_URL, concise_state, create_client


client = create_client()
page = client.get(SITE_URL)
result = client.system_one(
    state=concise_state(page),
    decisions={
        '采集相关性': client.score(
            '这个页面与采集小说书名、作者、分类和简介元数据的相关性如何？',
            min=0,
            max=10,
        )
    },
)

print('采集相关性:', result['采集相关性'])
print('模型原始结果:', result.raw)
print('决策耗时(秒):', result.decision_time)
