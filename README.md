# jevhttp

[English README](README.en.md)

`jevhttp` 是一个本地模型优先的同步HTTP与结构化决策工具包。

它把网页请求、网页元数据抽取和OpenAI-compatible模型决策组合成一个轻量Python接口。

主要用于本地模型推理，同时兼容在线OpenAI-compatible推理服务。

## 为什么使用 jevhttp

传统网页采集通常需要分别处理HTTP请求、HTML解析、链接发现和业务分类。

`jevhttp`将这些步骤组合起来，让网页分类、相关性判断和后续动作成为可校验的结构化结果，而不是自由文本。

```text
HTTP请求 → Page网页对象 → 精简State → 结构化决策 → 业务结果
```

模型不会直接访问网页。程序负责获取和清洗网页，模型只处理用户明确提供的State。

## 安装

项目发布到PyPI后，可以直接安装：

```bash
pip install jevhttp
```

从源码使用uv管理环境：

```bash
uv sync
```

## 快速开始

```python
from jevhttp import JevHttp

client = JevHttp(
    base_url='http://127.0.0.1:8000/v1',
    api_key='EMPTY',
    model='openbmb/MiniCPM5-2B',
)

page = client.get('https://example.com')
state = [
    {
        '网址': page.final_url,
        '标题': page.title,
        '描述': page.description,
        '状态码': page.status_code,
    }
]

result = client.system_one(
    state=state,
    decisions={
        '页面类型': client.choice(['文章页', '列表页', '其他']),
        '是否相关': client.boolean('这个网页与当前任务相关吗？'),
        '相关性': client.score('请评估网页相关性', min=0, max=10),
    },
)

print(result['页面类型'])
print(result['是否相关'])
print(result['相关性'])
print(result.decision_time)
```

`base_url`只用于模型API，不影响`client.get()`访问的网页地址。

## 主要特性

- 基于`requests.Session`的同步HTTP请求、连接复用、超时和有限重试
- `Page`和`Link`网页对象，提供标题、描述、标题列表、正文、链接和HTTP响应信息
- 自动把相对链接转换为绝对URL，并移除fragment和常见追踪参数
- `system_one()`一次请求执行一个或多个结构化决策
- 内置`Choice`、`Boolean`和`Score`决策类型
- 中文优先的模型提示词和分类结果校验
- 支持中文分类兜底项，避免小模型偶发同义词导致批处理终止
- 支持Pydantic结构化抽取：`client.extract(state, Model)`
- 支持带域名、深度、页数、robots.txt和内网地址保护的同步爬虫
- 每次决策提供原始JSON、模型名称、Token使用量和决策耗时
- 通过OpenAI-compatible接口兼容本地vLLM和远程模型服务

## 适合做什么

`jevhttp`适合需要“先获取网页，再进行结构化判断”的任务，例如：

- 学校、机构、企业网站的页面类型识别
- 新闻、文章、目录和详情页分类
- 网页相关性筛选和采集入口发现
- 本地小模型驱动的大规模网页预处理和批量决策
- 将网页状态抽取为业务Pydantic模型
- 对特定域名进行受限、可恢复的同步采集

它不是浏览器自动化框架，也不负责JavaScript渲染、验证码绕过、代理池、数据库、向量数据库或分布式任务调度。

## 性能验证

以下数据来自本地vLLM部署`openbmb/MiniCPM5-2B`的批量网页决策验证，使用8个并发工作线程。实际速度会受到GPU、网络和网页响应时间影响。

### 分阶段耗时

| 阶段 | 任务 | 并发数 | 平均耗时 | 中位数 | P95 | 备注 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| HTTP | 请求网页并解析HTML | 8 | 2.875秒 | 2.752秒 | 4.071秒 | 包含网络耗时 |
| Choice | 单项页面类型分类 | 1 | 0.376秒 | - | - | 本地小模型单次测试 |
| Boolean | 单项布尔判断 | 1 | 0.362秒 | - | - | 本地小模型单次测试 |
| Score | 单项相关性评分 | 1 | 0.398秒 | - | - | 本地小模型单次测试 |
| Choice | 批量页面类型分类 | 8 | 0.125秒 | 0.108秒 | 0.238秒 | 9998次成功分类 |
| 全流程 | 请求、解析、决策和落盘 | 8 | 约0.463秒/页 | - | - | 10000页约77分钟 |

### 页面处理结果

| 指标 | 数值 |
| --- | ---: |
| 处理页面数 | 10000 |
| 成功分类页面 | 9998 |
| 异常页面 | 2 |
| 成功率 | 99.98% |
| 唯一URL数量 | 10000 |
| 主要详情页分类 | 8983 |
| 主要列表页分类 | 1015 |

测试代码位于`test/`目录，包含HTTP解析、Choice、Boolean、Score、多决策、性能基准和实时JSONL采集测试。

## 版本范围

当前版本优先保证同步调用和可预测行为，暂不包含：

- asyncio和异步API
- 浏览器渲染
- Playwright和Selenium
- 数据库和ORM
- 向量数据库和RAG
- 代理池、验证码绕过和分布式队列

## 生态

- [awesome-jev](https://github.com/kraayenjon/awesome-jev)
- [Made with jev](https://madewithjev.com/)
- [xuehang.ai](https://xuehang.ai/)

## 许可证

本项目采用[MIT License](LICENSE)。

Copyright © 2026 [XUEHANG AI](https://xuehang.ai/)。
