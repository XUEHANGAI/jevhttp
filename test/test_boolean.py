"""测试中文Boolean教师主页判断"""

from jevhttp import JevHttp

client = JevHttp(
    base_url="http://127.0.0.1:8000/v1",
    api_key="EMPTY",
    model="openbmb/MiniCPM5-2B",
    timeout=60,
    max_retries=2,
)

page = client.get("https://grd.bit.edu.cn/tzgg1/85b26cdfd438483bb2b8c52028891e13.htm")
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
    decisions={"是否为教师主页": client.boolean("这是一个高校教师个人主页吗？")},
)

print("是否为教师主页:", result["是否为教师主页"])
print("模型原始结果:", result.raw)
print("决策耗时(秒):", result.decision_time)
