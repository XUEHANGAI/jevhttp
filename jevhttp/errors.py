"""定义jevhttp异常类型"""


class JevHttpError(Exception):
    """定义jevhttp基础异常"""


class HTTPRequestError(JevHttpError):
    """表示网页请求失败"""


class AITransportError(JevHttpError):
    """表示模型接口传输失败"""


class AIResponseError(JevHttpError):
    """表示模型响应结构异常"""


class DecisionParseError(JevHttpError):
    """表示模型响应无法解析为JSON"""


class DecisionValueError(JevHttpError):
    """表示模型结果未通过本地类型校验"""
