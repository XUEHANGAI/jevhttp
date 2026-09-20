"""测试中文Choice页面分类决策"""

from jevhttp import JevHttp

client = JevHttp(
    base_url="http://127.0.0.1:8000/v1",
    api_key="EMPTY",
    model="openbmb/MiniCPM5-2B",
    timeout=60,
    max_retries=2,
)

page = client.get(
    "https://www.10086txt.com/?id=29768"
)
print("网页状态码:", page.status_code)

state = [
    {
        "网址": page.final_url,
        "标题": page.title,
        "描述": page.description,
        "状态码": page.status_code,
    }
]

result = client.system_one(
    state=state,
    decisions={
        "页面分类": client.choice(
            [
                "玄幻小说",
                "奇幻小说",
                "武侠小说",
                "都市小说",
                "科幻小说",
                "其他",
            ],
            question="请严格从候选项中选择一个中文页面分类",
            fallback="其他",
        )
    },
)

print("页面分类:", result["页面分类"])
print("模型原始结果:", result.raw)
print("决策耗时(秒):", result.decision_time)
