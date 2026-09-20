"""定义结构化决策及其本地校验逻辑"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Decision:
    """定义一个结构化决策"""

    kind: str
    question: str | None = None

    def schema(self) -> dict[str, Any]:
        """生成供模型使用的JSON Schema"""
        raise NotImplementedError

    def validate(self, value: Any) -> Any:
        """校验模型返回的值"""
        return value


@dataclass(frozen=True)
class Choice(Decision):
    """定义一个只能从候选项中选择的分类决策"""

    choices: tuple[str, ...] = ()
    fallback: str | None = None

    def schema(self) -> dict[str, Any]:
        """生成中文枚举JSON Schema"""
        return {
            'type': 'string',
            'enum': list(self.choices),
            'description': self.question or '必须原样返回一个候选项，不得翻译或创造新分类',
        }

    def validate(self, value: Any) -> str:
        """校验分类是否完全匹配候选项"""
        if value not in self.choices:
            if self.fallback is not None:
                return self.fallback
            raise ValueError(f'分类必须是{self.choices}中的一项，实际得到{value!r}')
        return value


@dataclass(frozen=True)
class Boolean(Decision):
    """定义一个布尔决策"""

    def schema(self) -> dict[str, Any]:
        """生成布尔值JSON Schema"""
        return {
            'type': 'boolean',
            'description': self.question or '只能返回true或false',
        }

    def validate(self, value: Any) -> bool:
        """校验模型是否返回布尔值"""
        if isinstance(value, str):
            normalized_value = value.strip().lower()
            if normalized_value in {'是', '对', '正确', '真', '有', 'yes', 'true'}:
                return True
            if normalized_value in {'否', '不', '错误', '假', '无', 'no', 'false'}:
                return False
        if not isinstance(value, bool):
            raise ValueError(f'结果必须是布尔值，实际得到{value!r}')
        return value


@dataclass(frozen=True)
class Score(Decision):
    """定义一个指定范围内的数值决策"""

    minimum: float = 0
    maximum: float = 1

    def schema(self) -> dict[str, Any]:
        """生成带范围约束的数值JSON Schema"""
        return {
            'type': 'number',
            'minimum': self.minimum,
            'maximum': self.maximum,
            'description': self.question or '只能返回范围内的数字',
        }

    def validate(self, value: Any) -> int | float:
        """校验并转换分数"""
        if isinstance(value, bool):
            raise ValueError('分数不能是布尔值')
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f'结果必须是数字，实际得到{value!r}') from exc
        if not self.minimum <= number <= self.maximum:
            raise ValueError(
                f'分数必须位于[{self.minimum}, {self.maximum}]，实际得到{number}'
            )
        return int(number) if number.is_integer() else number
