# jevhttp

[中文 README](README.md)

`jevhttp` is a local-model-first synchronous HTTP and structured decision toolkit.
It combines web requests, page metadata extraction, and OpenAI-compatible model decisions in a lightweight Python API.

the project is designed primarily for local model inference while remaining compatible with online OpenAI-compatible inference services.

## Why jevhttp

Traditional web collection usually requires separate handling for HTTP requests, HTML parsing, link discovery, and business classification.
`jevhttp` combines these steps so page classification, relevance decisions, and follow-up actions become validated structured results instead of free-form text.

```text
HTTP request → Page object → Compact State → Structured decision → Business result
```

The model does not access URLs directly. The program fetches and cleans pages, then sends only the State explicitly selected by the user to the model.

## Installation

After the PyPI release, install the package with:

```bash
pip install jevhttp
```

For source development with uv:

```bash
uv sync
```

## Quick start

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
        'url': page.final_url,
        'title': page.title,
        'description': page.description,
        'status_code': page.status_code,
    }
]

result = client.system_one(
    state=state,
    decisions={
        'page_type': client.choice(['article', 'listing', 'other']),
        'is_relevant': client.boolean('Is this page relevant to the task?'),
        'relevance': client.score('Rate page relevance', min=0, max=10),
    },
)

print(result['page_type'])
print(result['is_relevant'])
print(result['relevance'])
print(result.decision_time)
```

`base_url` is used only for the model API and does not change the URL passed to `client.get()`.

## Features

- Synchronous HTTP requests based on `requests.Session`
- Connection reuse, timeouts, redirects, and limited retries
- `Page` and `Link` objects with titles, descriptions, headings, text, links, and HTTP metadata
- Relative URL normalization and removal of fragments and common tracking parameters
- One or multiple structured decisions through `system_one()`
- Built-in `Choice`, `Boolean`, and `Score` decisions
- Chinese-first prompts and classification validation
- Optional fallback categories for small models and batch processing
- Pydantic extraction through `client.extract(state, Model)`
- Synchronous crawling with domain, depth, page, robots.txt, and private-network controls
- Raw JSON, model name, token usage, and decision latency in every decision result
- Compatibility with local vLLM deployments and remote OpenAI-compatible services

## Use cases

`jevhttp` is designed for workflows that fetch a page and then make a structured decision, including:

- Page type classification for institutional and enterprise websites
- Article, directory, listing, and detail page classification
- Relevance filtering and discovery of collection entry points
- Large-scale preprocessing and batch decisions with local small models
- Converting page state into application-specific Pydantic models
- Restricted and resumable synchronous collection for a specific domain

It is not a browser automation framework and does not provide JavaScript rendering, CAPTCHA bypassing, proxy pools, databases, vector databases, or distributed task scheduling.

## Performance

The following measurements come from a large-scale page decision benchmark using a local vLLM deployment of `openbmb/MiniCPM5-2B` with 8 concurrent workers. Actual performance depends on GPU, network, and target page response time.

### Latency by stage

| Stage | Operation | Workers | Average | Median | P95 | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| HTTP | Fetch and parse HTML | 8 | 2.875 s | 2.752 s | 4.071 s | Includes network time |
| Choice | Single page classification | 1 | 0.376 s | - | - | Local small-model test |
| Boolean | Single boolean decision | 1 | 0.362 s | - | - | Local small-model test |
| Score | Single relevance score | 1 | 0.398 s | - | - | Local small-model test |
| Choice | Concurrent page classification | 8 | 0.125 s | 0.108 s | 0.238 s | 9,998 successful decisions |
| End-to-end | Fetch, parse, decide, and persist | 8 | ~0.463 s/page | - | - | 10,000 pages in ~77 minutes |

### Processing results

| Metric | Value |
| --- | ---: |
| Pages processed | 10,000 |
| Successfully classified | 9,998 |
| Errors | 2 |
| Success rate | 99.98% |
| Unique URLs | 10,000 |
| Main detail-page category | 8,983 |
| Main listing-page category | 1,015 |

Test programs are available under `test/` and cover HTTP parsing, Choice, Boolean, Score, multi-decision calls, performance benchmarks, and real-time JSONL collection.

## Scope

The current version prioritizes synchronous and predictable behavior. It does not include:

- Asyncio or asynchronous APIs
- Browser rendering
- Playwright or Selenium
- Databases or ORMs
- Vector databases or RAG
- Proxy pools, CAPTCHA bypassing, or distributed queues

## Ecosystem

- [awesome-jev](https://github.com/kraayenjon/awesome-jev)
- [Made with jev](https://madewithjev.com/)
- [xuehang.ai](https://xuehang.ai/)

## License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2026 [XUEHANG AI](https://xuehang.ai/).
