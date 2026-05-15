"""Result 类型：Ok/Err 模式，用于安全处理可能失败的操作。"""
from dataclasses import dataclass
from typing import Any, TypeAlias, TypeGuard
from abc import ABC

import requests
from requests import RequestException
from time import sleep


class _Result(ABC):
    """结果基类。"""
    def unwrap_or(self, default: Any) -> Any: ...
    def unwrap(self) -> Any: ...


@dataclass
class Ok(_Result):
    """成功结果。"""
    value: Any

    def unwrap_or(self, default: Any) -> Any:
        return self.value

    def unwrap(self) -> Any:
        return self.value


@dataclass
class Err(_Result):
    """失败结果。"""
    error: Any

    def unwrap_or(self, default: Any) -> Any:
        return default

    def unwrap(self) -> None:
        raise self.error


Result: TypeAlias = Ok | Err


def is_ok(result: Result) -> TypeGuard[Ok]:
    """判断结果是否为成功。"""
    return isinstance(result, Ok)


def is_err(result: Result) -> TypeGuard[Err]:
    """判断结果是否为失败。"""
    return isinstance(result, Err)


def noexcept_get(*args, **kwargs) -> Result:
    """安全的 GET 请求，带重试和指数退避。"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(*args, **kwargs)
            response.raise_for_status()
            return Ok(response)
        except RequestException as e:
            if attempt == max_retries - 1:
                return Err(e)
            sleep(2 ** attempt)
    return Err(Exception("所有重试都失败了"))


def get_response_json(response: requests.Response) -> Result:
    """安全解析响应 JSON。"""
    try:
        return Ok(response.json())
    except Exception as e:
        return Err(e)
