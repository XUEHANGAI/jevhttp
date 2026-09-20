"""实现网页请求、结构化决策和模型结构化抽取"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping, Type

import requests
from openai import OpenAI

from .decisions import Boolean, Choice, Decision, Score
from .errors import (
    AIResponseError,
    AITransportError,
    DecisionParseError,
    DecisionValueError,
    HTTPRequestError,
)
from .page import Page


@dataclass
class DecisionResult:
    """保存结构化决策结果和模型调试信息"""

    values: dict[str, Any]
    raw: Any = None
    model: str | None = None
    usage: Any = None
    decision_time: float | None = None
    state_truncated: bool = False

    @property
    def latency(self) -> float | None:
        """返回本次模型决策耗时，单位为秒"""
        return self.decision_time

    def __getattr__(self, name: str) -> Any:
        """支持通过属性名读取决策结果"""
        try:
            return self.values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __getitem__(self, name: str) -> Any:
        """支持通过键读取决策结果"""
        return self.values[name]


class JevHttp:
    """提供同步网页请求和OpenAI-compatible结构化决策"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30,
        max_retries: int = 2,
        temperature: float = 0,
        max_tokens: int | None = None,
        extra_body: dict | None = None,
        headers: Mapping[str, str] | None = None,
    ):
        """初始化客户端及其网页、模型请求配置"""
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_body = extra_body or {}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'jevhttp/0.1'})
        if headers:
            self.session.headers.update(headers)
        self._ai = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=0,
        )

    @classmethod
    def from_env(cls, **kwargs) -> 'JevHttp':
        """从环境变量创建客户端"""
        return cls(
            os.environ['JEVHTTP_BASE_URL'],
            os.environ['JEVHTTP_API_KEY'],
            os.environ['JEVHTTP_MODEL'],
            **kwargs,
        )

    def choice(
        self,
        choices,
        question: str = '',
        fallback: str | None = None,
    ) -> Choice:
        """创建中文枚举决策"""
        choices = tuple(str(choice) for choice in choices)
        if not choices:
            raise ValueError('choices不能为空')
        if fallback is not None and fallback not in choices:
            raise ValueError('fallback必须是choices中的一项')
        return Choice('choice', question, choices, fallback)

    def boolean(self, question: str = '') -> Boolean:
        """创建布尔决策"""
        return Boolean('boolean', question)

    noul = boolean

    def score(
        self,
        question: str = '',
        min: float = 0,
        max: float = 1,
    ) -> Score:
        """创建指定范围内的数值决策"""
        if min > max:
            raise ValueError('min不能大于max')
        return Score('score', question, min, max)

    def _request(self, method: str, url: str, **kwargs):
        """发送网页请求并执行有限重试"""
        last_error = None
        timeout = kwargs.pop('timeout', self.timeout)
        retry_post = kwargs.pop('retry_post', False)
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=timeout,
                    **kwargs,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                should_stop = attempt >= self.max_retries
                should_stop = should_stop or (
                    method.upper() == 'POST' and not retry_post
                )
                if should_stop:
                    break
                time.sleep(min(2**attempt * 0.25, 2))
        raise HTTPRequestError(
            f'HTTP请求失败: method={method}, url={url}, error={last_error}'
        ) from last_error

    def get(self, url: str, **kwargs) -> Page:
        """获取网页并返回解析后的``Page``对象"""
        return self._page_request('GET', url, **kwargs)

    def post(self, url: str, data=None, **kwargs) -> Page:
        """提交表单并返回解析后的``Page``对象"""
        return self._page_request('POST', url, data=data, **kwargs)

    def _page_request(self, method: str, url: str, depth: int = 0, **kwargs):
        """发送请求并将响应转换为``Page``"""
        response = self._request(method, url, **kwargs)
        return Page.from_response(response, depth=depth)

    @staticmethod
    def _state_json(state, max_chars: int = 8000) -> tuple[str, bool]:
        """序列化并限制送入模型的状态长度"""
        value = state.to_state() if isinstance(state, Page) else state
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            separators=(',', ':'),
            default=str,
        )
        return encoded[:max_chars], len(encoded) > max_chars

    def _chat_json(self, system: str, user: str, schema: dict):
        """调用模型并优先请求JSON Schema输出"""
        request_body = {
            'model': self.model,
            'temperature': self.temperature,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
            'response_format': {
                'type': 'json_schema',
                'json_schema': {
                    'name': 'jevhttp_result',
                    'strict': True,
                    'schema': schema,
                },
            },
        }
        if self.max_tokens is not None:
            request_body['max_tokens'] = self.max_tokens
        request_body.update(self.extra_body)
        try:
            response = self._ai.chat.completions.create(**request_body)
            content = response.choices[0].message.content if response.choices else None
        except Exception as first_error:
            content = None
        if not content:
            request_body['response_format'] = {'type': 'json_object'}
            try:
                response = self._ai.chat.completions.create(**request_body)
            except Exception as second_error:
                raise AITransportError(
                    f'模型请求失败: {second_error}'
                ) from locals().get('first_error')
        if not response.choices:
            raise AIResponseError('模型响应没有choices')
        content = response.choices[0].message.content
        if not content:
            finish_reason = getattr(response.choices[0], 'finish_reason', None)
            raise AIResponseError(
                f'模型响应没有文本内容，finish_reason={finish_reason!r}'
            )
        return response, content

    def system_one(
        self,
        state,
        decisions: Mapping[str, Decision],
        max_chars: int = 8000,
    ) -> DecisionResult:
        """使用一次中文提示词完成多个结构化决策"""
        if not decisions:
            raise ValueError('decisions不能为空')
        state_text, state_truncated = self._state_json(state, max_chars)
        schema = {
            'type': 'object',
            'properties': {
                name: decision.schema()
                for name, decision in decisions.items()
            },
            'required': list(decisions),
            'additionalProperties': False,
        }
        system = (
            '你是一个严谨的中文结构化信息判断模型。'
            '请只返回符合JSON Schema的JSON对象。'
            '所有Choice分类必须原样使用候选项中的中文文本，禁止输出英文、翻译结果或新分类。'
            '只能依据提供的网页状态判断，不要补充网页中不存在的事实。'
        )
        decision_text = '\n'.join(
            f'{name}: {decision.question or "请根据网页状态判断"}'
            for name, decision in decisions.items()
        )
        user = (
            f'网页状态(JSON):\n{state_text}\n\n'
            f'待判断项目:\n{decision_text}'
        )
        started = time.perf_counter()
        response, content = self._chat_json(system, user, schema)
        try:
            values = json.loads(content)
        except json.JSONDecodeError as exc:
            raise DecisionParseError(
                f'模型返回内容不是有效JSON: {content[:300]!r}'
            ) from exc
        if not isinstance(values, dict):
            raise DecisionParseError('模型结果必须是JSON对象')
        validated = {}
        for name, decision in decisions.items():
            try:
                validated[name] = decision.validate(values[name])
            except (KeyError, TypeError, ValueError) as exc:
                raise DecisionValueError(
                    f'决策{name!r}的结果未通过校验: {exc}'
                ) from exc
        return DecisionResult(
            validated,
            raw=content,
            model=getattr(response, 'model', self.model),
            usage=getattr(response, 'usage', None),
            decision_time=time.perf_counter() - started,
            state_truncated=state_truncated,
        )

    def extract(
        self,
        state,
        model: Type,
        max_chars: int = 8000,
        instruction: str = '',
    ):
        """使用中文提示词将状态抽取为Pydantic模型"""
        if not hasattr(model, 'model_json_schema'):
            raise TypeError('model必须是Pydantic模型类')
        state_text, _ = self._state_json(state, max_chars)
        system = (
            '你是一个严谨的中文结构化信息抽取模型。'
            '请只返回符合JSON Schema的JSON对象，不要输出解释。'
            '只能依据输入内容抽取，无法确认的字段按Schema允许的空值处理。'
        )
        user = f'网页状态(JSON):\n{state_text}\n\n补充要求:\n{instruction}'
        _, content = self._chat_json(system, user, model.model_json_schema())
        try:
            return model.model_validate_json(content)
        except Exception as exc:
            raise DecisionValueError(f'抽取结果未通过Pydantic校验: {exc}') from exc

    def crawl(self, seed_url: str, goal: str, **kwargs):
        """创建同步广度优先网页爬虫"""
        from .crawler import Crawler

        return Crawler(self).crawl(seed_url, goal, **kwargs)
