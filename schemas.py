# -*- coding:utf-8 -*-

from typing import Any, List, Optional
from pydantic import BaseModel


class Response(BaseModel):
    code: Optional[int] = 0
    msg: Optional[str] = "success"
    data: Optional[Any] = None


class Message(BaseModel):
    role: str
    content: str


class Data(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = None
