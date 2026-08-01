from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def ok(data: Any = None, msg: str = "ok") -> JSONResponse:
    return JSONResponse(jsonable_encoder({"code": 0, "msg": msg, "data": data}))


def fail(msg: str, code: int = 1, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=jsonable_encoder({"code": code, "msg": msg, "data": None}))
