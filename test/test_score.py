"""测试中文Score网页相关性判断"""

from jevhttp import JevHttp

client = JevHttp(
    base_url="http://127.0.0.1:8000/v1",
    api_key="EMPTY",
    model="openbmb/MiniCPM5-2B",
    timeout=60,
    max_retries=2,
)

page = client.get(
    "https://se.bit.edu.cn/szdw/jsml/gdjyygcjyyjs1/679bedd44dc34365a8fdf908e04549a5.htm"
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
        "教师发现相关性": client.score(
            "这个网页与高校教师发现任务的相关性如何？访问错误时返回0",
            min=0,
            max=10,
        )
    },
)

print("教师发现相关性:", result["教师发现相关性"])
print("模型原始结果:", result.raw)
print("决策耗时(秒):", result.decision_time)
