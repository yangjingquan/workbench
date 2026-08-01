import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.routes import router
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal, ensure_schema
from app.models import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("workbench")

app = FastAPI(title="Dev Workbench API", version="1.0.0", description="程序员个人工作台 REST API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content=jsonable_encoder({"code": 422, "msg": "请求参数校验失败", "data": exc.errors()}))


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled API error: %s", exc)
    return JSONResponse(status_code=500, content={"code": 500, "msg": "服务器内部错误", "data": None})


@app.on_event("startup")
def startup():
    ensure_schema()
    db = SessionLocal()
    try:
        if not db.scalar(select(User).where(User.username == "admin")):
            db.add(User(username="admin", password_hash=hash_password("admin123"), display_name="工作台管理员"))
            db.commit()
            logger.info("Created default admin account: admin / admin123")
    finally:
        db.close()


@app.get("/health")
def health():
    return {"code": 0, "msg": "ok", "data": {"service": "dev-workbench"}}
