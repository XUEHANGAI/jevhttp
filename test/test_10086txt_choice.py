"""测试10086txt页面类型中文分类效果和耗时"""

from test.site_10086txt import SITE_URL, concise_state, create_client


client = create_client()
page = client.get(SITE_URL)
result = client.system_one(
    state=concise_state(page),
    decisions={
        '页面类型': client.choice(
            [
                '小说网站首页',
                '小说分类页',
                '小说详情页',
                '下载页面',
                '访问错误',
                '其他',
            ],
            question='请严格从候选项中选择一个中文页面类型',
            fallback='其他',
        )
    },
)

print('页面类型:', result['页面类型'])
print('模型原始结果:', result.raw)
print('决策耗时(秒):', result.decision_time)
