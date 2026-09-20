"""测试10086txt一次请求执行多个中文决策"""

from test.site_10086txt import SITE_URL, concise_state, create_client


client = create_client()
page = client.get(SITE_URL)
result = client.system_one(
    state=concise_state(page),
    decisions={
        '页面类型': client.choice(
            ['小说网站首页', '小说分类页', '小说详情页', '其他'],
            question='请选择一个中文页面类型',
            fallback='其他',
        ),
        '是否为小说相关页面': client.boolean(
            '这个页面是否与小说相关？'
        ),
        '采集相关性': client.score(
            '这个页面与小说元数据采集任务的相关性如何？',
            min=0,
            max=10,
        ),
    },
)

print('页面类型:', result['页面类型'])
print('是否为小说相关页面:', result['是否为小说相关页面'])
print('采集相关性:', result['采集相关性'])
print('模型原始结果:', result.raw)
print('三决策总耗时(秒):', result.decision_time)
