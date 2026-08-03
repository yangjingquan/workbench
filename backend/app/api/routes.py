from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.common import ok
from app.api.deps import get_current_user
from app.core.security import create_access_token, decrypt_login_password, hash_password, login_public_key, verify_password
from app.db.session import get_db
from app.models import AccountCategory, AccountEntry, EventReminder, Memo, QuickLink, SystemConfig, TodoSubtask, TodoTask, ToolUsageLog, User, WorkPlan, WorkRecord

router = APIRouter(prefix="/api")
DEFAULT_TIMEZONE = "Asia/Shanghai"
UTC = dt_timezone.utc


def _zone(name: str | None) -> ZoneInfo:
    timezone_name = name or DEFAULT_TIMEZONE
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        raise HTTPException(400, f"无效的时区：{timezone_name}")


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _to_utc_naive(value: datetime | None, zone: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    aware = value if value.tzinfo else value.replace(tzinfo=zone)
    return aware.astimezone(UTC).replace(tzinfo=None)


def _from_utc_naive(value: datetime | None, zone: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return aware.astimezone(zone).replace(tzinfo=None)


def _utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return aware.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _time_value(value: str | None) -> tuple[int, int, int]:
    try:
        parts = [int(part) for part in (value or "00:00").split(":")]
        return parts[0], parts[1], parts[2] if len(parts) > 2 else 0
    except (TypeError, ValueError):
        raise HTTPException(400, "时间格式必须是 HH:mm 或 HH:mm:ss")


def _candidate(day: date, value: str | None) -> datetime:
    hour, minute, second = _time_value(value)
    return datetime(day.year, day.month, day.day, hour, minute, second)


def _next_occurrence(schedule_type: str, value: str | None, weekdays: list[int], month_days: list[int], after: datetime) -> datetime | None:
    if schedule_type == "once":
        return None
    if schedule_type == "daily":
        valid_days = sorted({day for day in weekdays if 1 <= day <= 7})
        if valid_days:
            for offset in range(0, 8):
                day = after.date() + timedelta(days=offset)
                candidate = _candidate(day, value)
                if day.isoweekday() in valid_days and candidate > after:
                    return candidate
            return None
        candidate = _candidate(after.date(), value)
        return candidate if candidate > after else candidate + timedelta(days=1)
    if schedule_type == "weekly":
        valid_days = sorted({day for day in weekdays if 1 <= day <= 7})
        if not valid_days:
            raise HTTPException(400, "每周提醒至少选择一天")
        for offset in range(0, 8):
            day = after.date() + timedelta(days=offset)
            candidate = _candidate(day, value)
            if day.isoweekday() in valid_days and candidate > after:
                return candidate
        return None
    if schedule_type == "monthly":
        valid_days = sorted({day for day in month_days if 1 <= day <= 31})
        if not valid_days:
            raise HTTPException(400, "每月提醒至少选择一个日期")
        for month_offset in range(0, 25):
            month_index = after.year * 12 + after.month - 1 + month_offset
            year, month = divmod(month_index, 12)
            month += 1
            for day_number in valid_days:
                if day_number <= monthrange(year, month)[1]:
                    candidate = _candidate(date(year, month, day_number), value)
                    if candidate > after:
                        return candidate
        return None
    raise HTTPException(400, "不支持的提醒周期")


def _prepare_reminder(payload: ReminderIn, now: datetime) -> dict:
    zone = _zone(payload.timezone)
    now_utc = now.astimezone(UTC).replace(tzinfo=None) if now.tzinfo else now
    now_local = _from_utc_naive(now_utc, zone)
    schedule_type = payload.schedule_type
    if schedule_type not in {"once", "daily", "weekly", "monthly"}:
        raise HTTPException(400, "不支持的提醒周期")
    if schedule_type == "once":
        if not payload.remind_at:
            raise HTTPException(400, "固定日期提醒必须填写执行时间")
        remind_at = _to_utc_naive(payload.remind_at, zone)
        local_remind_at = _from_utc_naive(remind_at, zone)
        next_trigger = remind_at
        time_of_day = local_remind_at.strftime("%H:%M:%S")
    else:
        time_of_day = payload.time_of_day or (payload.remind_at.strftime("%H:%M:%S") if payload.remind_at else None)
        _time_value(time_of_day)
        if schedule_type == "weekly" and not payload.weekdays:
            raise HTTPException(400, "每周提醒至少选择一天")
        if schedule_type == "monthly" and not payload.month_days:
            raise HTTPException(400, "每月提醒至少选择一个日期")
        next_local = _next_occurrence(schedule_type, time_of_day, payload.weekdays, payload.month_days, now_local)
        next_trigger = _to_utc_naive(next_local, zone)
    return {
        "remind_at": next_trigger or now_utc,
        "repeat_type": schedule_type,
        "schedule_type": schedule_type,
        "time_of_day": time_of_day,
        "weekdays": sorted(set(payload.weekdays)),
        "month_days": sorted(set(payload.month_days)),
        "next_trigger_at": next_trigger,
        "snoozed_until": None,
        "timezone": payload.timezone or DEFAULT_TIMEZONE,
    }


def _reminder_dict(row: EventReminder) -> dict:
    result = dump(row)
    for key in ("remind_at", "snoozed_until", "next_trigger_at", "last_trigger_at"):
        result[key] = _utc_iso(result.get(key))
    result["schedule_type"] = row.schedule_type or row.repeat_type or "once"
    result["weekdays"] = row.weekdays or []
    result["month_days"] = row.month_days or []
    result["timezone"] = row.timezone or DEFAULT_TIMEZONE
    return result


def dump(obj: Any, exclude: set[str] | None = None) -> dict:
    exclude = exclude or set()
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns if column.name not in exclude}


class LoginIn(BaseModel):
    username: str
    encrypted_password: str = Field(min_length=1)


class PasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


class ResetPasswordIn(BaseModel):
    new_password: str = Field(min_length=6)


class WorkRecordIn(BaseModel):
    title: str
    content: str = ""
    work_date: date
    hours: float = 0
    tags: list[str] = []
    task_id: int | None = None


class WorkPlanIn(BaseModel):
    title: str
    description: str = ""
    start_date: date
    end_date: date
    priority: str = "medium"
    status: str = "pending"


class ReminderIn(BaseModel):
    title: str
    content: str = ""
    remind_at: datetime | None = None
    schedule_type: str = "once"
    time_of_day: str | None = None
    weekdays: list[int] = []
    month_days: list[int] = []
    timezone: str = DEFAULT_TIMEZONE


class TodoIn(BaseModel):
    title: str
    description: str = ""
    notes: str = ""
    status: str = "todo"
    priority: str = "medium"
    due_at: datetime | None = None
    group_name: str = "默认分组"
    tags: list[str] = []
    parent_id: int | None = None


class TodoStatusIn(BaseModel):
    status: str


class SubtaskIn(BaseModel):
    title: str


class LinkIn(BaseModel):
    title: str
    url: str
    category: str = "未分类"
    description: str = ""


class UsageIn(BaseModel):
    tool_name: str
    action: str = "use"


class ConfigIn(BaseModel):
    values: dict[str, Any]


class AccountCategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    entry_type: str = "expense"


class AccountEntryIn(BaseModel):
    entry_type: str = "expense"
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=80)
    note: str = ""
    entry_date: date


class MemoIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


@router.post("/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    try:
        password = decrypt_login_password(payload.encrypted_password)
    except ValueError:
        raise HTTPException(400, "登录参数无效，请刷新页面后重试")
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    token = create_access_token(user.id, user.token_version)
    return ok({"token": token, "user": dump(user, {"password_hash", "token_version"})})


@router.get("/auth/public-key")
def auth_public_key():
    return ok({"public_key": login_public_key()})


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return ok(dump(user, {"password_hash", "token_version"}))


@router.post("/auth/change-password")
def change_password(payload: PasswordIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(400, "原密码不正确")
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    db.commit()
    return ok(msg="密码已修改，旧登录状态已全部失效")


@router.post("/auth/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    db.commit()
    return ok(msg="密码已重置，旧登录状态已全部失效")


@router.post("/auth/logout-all")
def logout_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.token_version += 1
    db.commit()
    return ok(msg="已强制下线所有设备")


@router.put("/auth/profile")
def profile(payload: dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if "display_name" in payload:
        user.display_name = str(payload["display_name"])[:120]
    if "avatar_url" in payload:
        user.avatar_url = str(payload["avatar_url"])[:500]
    db.commit()
    return ok(dump(user, {"password_hash", "token_version"}))


@router.get("/work-records")
def list_records(start: date | None = None, end: date | None = None, keyword: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(WorkRecord).where(WorkRecord.user_id == user.id)
    if start: query = query.where(WorkRecord.work_date >= start)
    if end: query = query.where(WorkRecord.work_date <= end)
    if keyword: query = query.where(or_(WorkRecord.title.like(f"%{keyword}%"), WorkRecord.content.like(f"%{keyword}%")))
    rows = db.scalars(query.order_by(desc(WorkRecord.work_date), desc(WorkRecord.id))).all()
    return ok([dump(row) for row in rows])


@router.post("/work-records")
def create_record(payload: WorkRecordIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = WorkRecord(user_id=user.id, **payload.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return ok(dump(row), "工作记录已保存")


@router.put("/work-records/{item_id}")
def update_record(item_id: int, payload: WorkRecordIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(WorkRecord).where(WorkRecord.id == item_id, WorkRecord.user_id == user.id))
    if not row: raise HTTPException(404, "记录不存在")
    for key, value in payload.model_dump().items(): setattr(row, key, value)
    db.commit(); db.refresh(row)
    return ok(dump(row), "工作记录已更新")


@router.delete("/work-records/{item_id}")
def delete_record(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(WorkRecord).where(WorkRecord.id == item_id, WorkRecord.user_id == user.id))
    if not row: raise HTTPException(404, "记录不存在")
    db.delete(row); db.commit(); return ok(msg="工作记录已删除")


@router.get("/work-plans")
def list_plans(month: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(WorkPlan).where(WorkPlan.user_id == user.id)
    if month:
        prefix = f"{month}%"
        query = query.where(or_(func.date_format(WorkPlan.start_date, "%Y-%m").like(prefix), func.date_format(WorkPlan.end_date, "%Y-%m").like(prefix)))
    return ok([dump(row) for row in db.scalars(query.order_by(WorkPlan.start_date)).all()])


@router.post("/work-plans")
def create_plan(payload: WorkPlanIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = WorkPlan(user_id=user.id, **payload.model_dump()); db.add(row); db.commit(); db.refresh(row); return ok(dump(row), "计划已创建")


@router.put("/work-plans/{item_id}")
def update_plan(item_id: int, payload: WorkPlanIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(WorkPlan).where(WorkPlan.id == item_id, WorkPlan.user_id == user.id))
    if not row: raise HTTPException(404, "计划不存在")
    for key, value in payload.model_dump().items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return ok(dump(row), "计划已更新")


@router.delete("/work-plans/{item_id}")
def delete_plan(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(WorkPlan).where(WorkPlan.id == item_id, WorkPlan.user_id == user.id))
    if not row: raise HTTPException(404, "计划不存在")
    db.delete(row); db.commit(); return ok(msg="计划已删除")


@router.get("/reminders")
def list_reminders(due: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(EventReminder).where(EventReminder.user_id == user.id, EventReminder.status != "deleted")
    if due:
        now = _utc_now()
        query = query.where(
            EventReminder.status == "active",
            EventReminder.next_trigger_at.is_not(None),
            EventReminder.next_trigger_at <= now,
            or_(EventReminder.snoozed_until.is_(None), EventReminder.snoozed_until <= now),
        )
    status_order = case((EventReminder.status == "active", 0), (EventReminder.status == "closed", 1), else_=2)
    return ok([_reminder_dict(row) for row in db.scalars(query.order_by(status_order, EventReminder.next_trigger_at, EventReminder.remind_at)).all()])


@router.post("/reminders")
def create_reminder(payload: ReminderIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prepared = _prepare_reminder(payload, _utc_now())
    row = EventReminder(user_id=user.id, title=payload.title, content=payload.content, **prepared)
    db.add(row); db.commit(); db.refresh(row); return ok(_reminder_dict(row), "提醒已创建")


@router.put("/reminders/{item_id}")
def update_reminder(item_id: int, payload: ReminderIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(EventReminder).where(EventReminder.id == item_id, EventReminder.user_id == user.id, EventReminder.status != "deleted"))
    if not row: raise HTTPException(404, "提醒不存在")
    prepared = _prepare_reminder(payload, _utc_now())
    row.title = payload.title; row.content = payload.content; row.status = "active"
    for key, value in prepared.items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return ok(_reminder_dict(row), "提醒已更新")


@router.post("/reminders/{item_id}/action")
def reminder_action(item_id: int, action: str = Query(..., pattern="^(ack|snooze|close|activate|delete)$"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(EventReminder).where(EventReminder.id == item_id, EventReminder.user_id == user.id, EventReminder.status != "deleted"))
    if not row: raise HTTPException(404, "提醒不存在")
    now = _utc_now()
    zone = _zone(row.timezone)
    if action == "ack":
        current_trigger = row.next_trigger_at or now
        row.last_trigger_at = current_trigger
        row.snoozed_until = None
        if row.schedule_type == "once": row.next_trigger_at = None; row.status = "closed"
        else:
            current_local = _from_utc_naive(current_trigger, zone)
            row.next_trigger_at = _to_utc_naive(_next_occurrence(row.schedule_type, row.time_of_day, row.weekdays or [], row.month_days or [], current_local), zone)
    elif action == "snooze": row.snoozed_until = now + timedelta(minutes=10)
    elif action == "close": row.status = "closed"; row.snoozed_until = None
    elif action == "activate":
        row.status = "active"; row.snoozed_until = None
        if row.schedule_type == "once": row.next_trigger_at = row.remind_at if row.remind_at and row.remind_at > now else None
        else:
            now_local = _from_utc_naive(now, zone)
            row.next_trigger_at = _to_utc_naive(_next_occurrence(row.schedule_type, row.time_of_day, row.weekdays or [], row.month_days or [], now_local), zone)
    elif action == "delete": row.status = "deleted"; row.snoozed_until = None; row.next_trigger_at = None
    db.commit(); return ok(_reminder_dict(row), "提醒已处理")


def todo_dict(row: TodoTask):
    result = dump(row)
    result["subtasks"] = [dump(item) for item in row.subtasks]
    return result


def _ensure_todo_completion_record(task: TodoTask, user_id: int, db: Session) -> None:
    """Create one linked work record the first time a Todo reaches done."""
    if not task.id:
        return
    existing = db.scalar(select(WorkRecord).where(WorkRecord.user_id == user_id, WorkRecord.task_id == task.id))
    if existing:
        return
    content_parts = [value.strip() for value in (task.description, task.notes) if value and value.strip()]
    completed_at = task.completed_at or datetime.now()
    db.add(WorkRecord(
        user_id=user_id,
        title=task.title[:200],
        content="\n\n".join(content_parts),
        work_date=completed_at.date(),
        hours=round((task.elapsed_seconds or 0) / 3600, 2),
        tags=list(task.tags or []),
        task_id=task.id,
    ))


@router.get("/todos")
def list_todos(include_archived: bool = False, keyword: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(TodoTask).where(TodoTask.user_id == user.id)
    if not include_archived: query = query.where(TodoTask.archived.is_(False))
    if keyword: query = query.where(or_(TodoTask.title.like(f"%{keyword}%"), TodoTask.description.like(f"%{keyword}%"), TodoTask.notes.like(f"%{keyword}%")))
    return ok([todo_dict(row) for row in db.scalars(query.order_by(TodoTask.position, desc(TodoTask.id))).all()])


@router.post("/todos")
def create_todo(payload: TodoIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = TodoTask(user_id=user.id, **payload.model_dump()); db.add(row)
    if row.status == "done":
        row.completed_at = datetime.now()
        db.flush()
        _ensure_todo_completion_record(row, user.id, db)
    db.commit(); db.refresh(row); return ok(todo_dict(row), "待办已创建")


@router.post("/todos/batch")
def batch_todos(action: str = Query(..., pattern="^(complete|delete|archive)$"), ids: list[int] = Body(default=[]), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(TodoTask).where(TodoTask.user_id == user.id, TodoTask.id.in_(ids))).all()
    for row in rows:
        if action == "delete": db.delete(row)
        elif action == "complete":
            row.status = "done"; row.completed_at = row.completed_at or datetime.now(); _ensure_todo_completion_record(row, user.id, db)
        else: row.archived = True
    db.commit(); return ok(msg="批量操作完成")


@router.put("/todos/{item_id}")
def update_todo(item_id: int, payload: TodoIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(TodoTask).where(TodoTask.id == item_id, TodoTask.user_id == user.id))
    if not row: raise HTTPException(404, "待办不存在")
    for key, value in payload.model_dump().items(): setattr(row, key, value)
    if row.status == "done":
        row.completed_at = row.completed_at or datetime.now()
        _ensure_todo_completion_record(row, user.id, db)
    elif row.status != "done":
        row.completed_at = None
    db.commit(); db.refresh(row); return ok(todo_dict(row), "待办已更新")


@router.patch("/todos/{item_id}/status")
def update_todo_status(item_id: int, payload: TodoStatusIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(TodoTask).where(TodoTask.id == item_id, TodoTask.user_id == user.id))
    if not row: raise HTTPException(404, "待办不存在")
    row.status = payload.status; row.completed_at = datetime.now() if payload.status == "done" else None
    if payload.status == "done": _ensure_todo_completion_record(row, user.id, db)
    db.commit(); return ok(todo_dict(row), "状态已更新")


@router.post("/todos/{item_id}/timer")
def todo_timer(item_id: int, action: str = Query(..., pattern="^(start|pause|stop)$"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.scalar(select(TodoTask).where(TodoTask.id == item_id, TodoTask.user_id == user.id))
    if not task: raise HTTPException(404, "待办不存在")
    now = datetime.now()
    if action == "start":
        task.timer_started_at = now
    else:
        if task.timer_started_at:
            task.elapsed_seconds += max(0, int((now - task.timer_started_at).total_seconds()))
        task.timer_started_at = None
        if action == "stop" and task.elapsed_seconds:
            db.add(WorkRecord(user_id=user.id, title=f"任务计时：{task.title}", content=task.notes or task.description, work_date=date.today(), hours=round(task.elapsed_seconds / 3600, 2), tags=task.tags or [], task_id=task.id))
            task.elapsed_seconds = 0
    db.commit(); db.refresh(task); return ok(todo_dict(task), "计时已更新")


@router.delete("/todos/{item_id}")
def delete_todo(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(TodoTask).where(TodoTask.id == item_id, TodoTask.user_id == user.id))
    if not row: raise HTTPException(404, "待办不存在")
    db.delete(row); db.commit(); return ok(msg="待办已删除")


@router.post("/todos/{item_id}/subtasks")
def add_subtask(item_id: int, payload: SubtaskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.scalar(select(TodoTask).where(TodoTask.id == item_id, TodoTask.user_id == user.id))
    if not task: raise HTTPException(404, "待办不存在")
    item = TodoSubtask(task_id=item_id, title=payload.title); db.add(item); db.commit(); db.refresh(task); return ok(todo_dict(task), "子任务已添加")


@router.patch("/todos/{item_id}/archive")
def archive_todo(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(TodoTask).where(TodoTask.id == item_id, TodoTask.user_id == user.id));
    if not row: raise HTTPException(404, "待办不存在")
    row.archived = True; db.commit(); return ok(msg="已归档")


@router.patch("/todos/{item_id}/restore")
def restore_todo(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(TodoTask).where(TodoTask.id == item_id, TodoTask.user_id == user.id))
    if not row: raise HTTPException(404, "待办不存在")
    row.archived = False; db.commit(); return ok(todo_dict(row), "已恢复到看板")


@router.get("/quick-links")
def list_links(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ok([dump(row) for row in db.scalars(select(QuickLink).where(QuickLink.user_id == user.id).order_by(QuickLink.position, QuickLink.id)).all()])


@router.post("/quick-links")
def create_link(payload: LinkIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = QuickLink(user_id=user.id, **payload.model_dump()); db.add(row); db.commit(); db.refresh(row); return ok(dump(row), "链接已添加")


@router.put("/quick-links/{item_id}")
def update_link(item_id: int, payload: LinkIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(QuickLink).where(QuickLink.id == item_id, QuickLink.user_id == user.id))
    if not row: raise HTTPException(404, "链接不存在")
    for key, value in payload.model_dump().items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return ok(dump(row), "链接已更新")


@router.delete("/quick-links/{item_id}")
def delete_link(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(QuickLink).where(QuickLink.id == item_id, QuickLink.user_id == user.id));
    if not row: raise HTTPException(404, "链接不存在")
    db.delete(row); db.commit(); return ok(msg="链接已删除")


ACCOUNT_DEFAULT_CATEGORIES = [
    ("expense", "餐饮"), ("expense", "交通"), ("expense", "购物"),
    ("expense", "居住"), ("expense", "娱乐"), ("expense", "医疗"),
    ("expense", "学习"), ("expense", "其他支出"),
    ("income", "工资"), ("income", "奖金"), ("income", "兼职"),
    ("income", "投资"), ("income", "其他收入"),
]


def _ensure_account_categories(db: Session, user_id: int):
    existing = {(row.entry_type, row.name) for row in db.scalars(select(AccountCategory).where(AccountCategory.user_id == user_id)).all()}
    created = False
    for entry_type, name in ACCOUNT_DEFAULT_CATEGORIES:
        if (entry_type, name) not in existing:
            db.add(AccountCategory(user_id=user_id, entry_type=entry_type, name=name, is_default=True))
            created = True
    if created:
        db.commit()


def _account_period(period: str, anchor: str | None) -> tuple[date, date]:
    if period == "day":
        selected = date.fromisoformat((anchor or str(date.today()))[:10])
        return selected, selected
    if period == "month":
        raw = (anchor or str(date.today()))[:7]
        year, month = [int(value) for value in raw.split("-")]
        return date(year, month, 1), date(year, month, monthrange(year, month)[1])
    if period == "year":
        year = int((anchor or str(date.today()))[:4])
        return date(year, 1, 1), date(year, 12, 31)
    raise HTTPException(400, "统计周期必须是 day、month 或 year")


@router.get("/accounts/categories")
def list_account_categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_account_categories(db, user.id)
    rows = db.scalars(select(AccountCategory).where(AccountCategory.user_id == user.id).order_by(AccountCategory.entry_type, AccountCategory.is_default.desc(), AccountCategory.name)).all()
    return ok([dump(row) for row in rows])


@router.post("/accounts/categories")
def create_account_category(payload: AccountCategoryIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entry_type = payload.entry_type.strip().lower()
    name = payload.name.strip()
    if entry_type not in {"expense", "income"}:
        raise HTTPException(400, "分类类型必须是 expense 或 income")
    if not name:
        raise HTTPException(400, "分类名称不能为空")
    duplicate = db.scalar(select(AccountCategory).where(AccountCategory.user_id == user.id, AccountCategory.entry_type == entry_type, AccountCategory.name == name))
    if duplicate:
        raise HTTPException(400, "该分类已存在")
    row = AccountCategory(user_id=user.id, entry_type=entry_type, name=name, is_default=False)
    db.add(row); db.commit(); db.refresh(row)
    return ok(dump(row), "分类已添加")


@router.get("/accounts/entries")
def list_account_entries(start: date | None = None, end: date | None = None, entry_type: str | None = None, category: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(AccountEntry).where(AccountEntry.user_id == user.id)
    if start: query = query.where(AccountEntry.entry_date >= start)
    if end: query = query.where(AccountEntry.entry_date <= end)
    if entry_type: query = query.where(AccountEntry.entry_type == entry_type)
    if category: query = query.where(AccountEntry.category == category)
    rows = db.scalars(query.order_by(desc(AccountEntry.entry_date), desc(AccountEntry.id)).limit(300)).all()
    return ok([dump(row) for row in rows])


@router.post("/accounts/entries")
def create_account_entry(payload: AccountEntryIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entry_type = payload.entry_type.strip().lower()
    category = payload.category.strip()
    if entry_type not in {"expense", "income"}:
        raise HTTPException(400, "账目类型必须是 expense 或 income")
    if not category:
        raise HTTPException(400, "请选择或填写分类")
    row = AccountEntry(user_id=user.id, entry_type=entry_type, amount=round(payload.amount, 2), category=category, note=payload.note.strip(), entry_date=payload.entry_date)
    db.add(row); db.commit(); db.refresh(row)
    return ok(dump(row), "账目已保存")


@router.put("/accounts/entries/{item_id}")
def update_account_entry(item_id: int, payload: AccountEntryIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(AccountEntry).where(AccountEntry.id == item_id, AccountEntry.user_id == user.id))
    if not row: raise HTTPException(404, "账目不存在")
    entry_type = payload.entry_type.strip().lower(); category = payload.category.strip()
    if entry_type not in {"expense", "income"} or not category:
        raise HTTPException(400, "账目类型或分类无效")
    row.entry_type = entry_type; row.amount = round(payload.amount, 2); row.category = category; row.note = payload.note.strip(); row.entry_date = payload.entry_date
    db.commit(); db.refresh(row)
    return ok(dump(row), "账目已更新")


@router.delete("/accounts/entries/{item_id}")
def delete_account_entry(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(AccountEntry).where(AccountEntry.id == item_id, AccountEntry.user_id == user.id))
    if not row: raise HTTPException(404, "账目不存在")
    db.delete(row); db.commit(); return ok(msg="账目已删除")


@router.get("/accounts/summary")
def account_summary(period: str = Query("month"), anchor: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start, end = _account_period(period, anchor)
    rows = db.scalars(select(AccountEntry).where(AccountEntry.user_id == user.id, AccountEntry.entry_date.between(start, end))).all()
    total_income = sum(row.amount for row in rows if row.entry_type == "income")
    total_expense = sum(row.amount for row in rows if row.entry_type == "expense")
    category_totals: dict[tuple[str, str], dict[str, float | int | str]] = {}
    trend_totals: dict[str, dict[str, float | str]] = {}
    for row in rows:
        category_key = (row.entry_type, row.category)
        category = category_totals.setdefault(category_key, {"entry_type": row.entry_type, "category": row.category, "total": 0.0, "count": 0})
        category["total"] = float(category["total"]) + row.amount
        category["count"] = int(category["count"]) + 1
        label = str(row.entry_date) if period in {"day", "month"} else row.entry_date.strftime("%Y-%m")
        trend = trend_totals.setdefault(label, {"label": label, "income": 0.0, "expense": 0.0})
        trend[row.entry_type] = float(trend[row.entry_type]) + row.amount
    return ok({
        "period": period, "start": str(start), "end": str(end),
        "total_income": round(total_income, 2), "total_expense": round(total_expense, 2), "balance": round(total_income - total_expense, 2),
        "by_category": sorted(({**item, "total": round(float(item["total"]), 2)} for item in category_totals.values()), key=lambda item: item["total"], reverse=True),
        "trend": [{"label": label, "income": round(float(item["income"]), 2), "expense": round(float(item["expense"]), 2)} for label, item in sorted(trend_totals.items())],
    })


@router.get("/memos")
def list_memos(keyword: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(Memo).where(Memo.user_id == user.id)
    if keyword and keyword.strip(): query = query.where(Memo.title.like(f"%{keyword.strip()}%"))
    rows = db.scalars(query.order_by(desc(Memo.created_at), desc(Memo.id))).all()
    return ok([dump(row) for row in rows])


@router.post("/memos")
def create_memo(payload: MemoIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    title = payload.title.strip(); content = payload.content.strip()
    if not title or not content: raise HTTPException(400, "标题和内容都不能为空")
    row = Memo(user_id=user.id, title=title, content=content)
    db.add(row); db.commit(); db.refresh(row)
    return ok(dump(row), "备忘录已保存")


@router.put("/memos/{item_id}")
def update_memo(item_id: int, payload: MemoIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(Memo).where(Memo.id == item_id, Memo.user_id == user.id))
    if not row: raise HTTPException(404, "备忘录不存在")
    title = payload.title.strip(); content = payload.content.strip()
    if not title or not content: raise HTTPException(400, "标题和内容都不能为空")
    row.title = title; row.content = content; db.commit(); db.refresh(row)
    return ok(dump(row), "备忘录已更新")


@router.delete("/memos/{item_id}")
def delete_memo(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(Memo).where(Memo.id == item_id, Memo.user_id == user.id))
    if not row: raise HTTPException(404, "备忘录不存在")
    db.delete(row); db.commit(); return ok(msg="备忘录已删除")


@router.post("/tools/usage")
def log_tool_usage(payload: UsageIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.add(ToolUsageLog(user_id=user.id, **payload.model_dump())); db.commit(); return ok(msg="工具使用已记录")


@router.get("/config")
def get_config(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(SystemConfig).where(SystemConfig.user_id == user.id)).all()
    return ok({row.config_key: row.config_value for row in rows})


@router.put("/config")
def save_config(payload: ConfigIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for key, value in payload.values.items():
        row = db.scalar(select(SystemConfig).where(SystemConfig.user_id == user.id, SystemConfig.config_key == key))
        if row: row.config_value = value
        else: db.add(SystemConfig(user_id=user.id, config_key=key, config_value=value))
    db.commit(); return get_config(db, user)


@router.get("/search")
def global_search(keyword: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    like = f"%{keyword}%"
    records = db.scalars(select(WorkRecord).where(WorkRecord.user_id == user.id, or_(WorkRecord.title.like(like), WorkRecord.content.like(like))).limit(10)).all()
    plans = db.scalars(select(WorkPlan).where(WorkPlan.user_id == user.id, or_(WorkPlan.title.like(like), WorkPlan.description.like(like))).limit(10)).all()
    todos = db.scalars(select(TodoTask).where(TodoTask.user_id == user.id, or_(TodoTask.title.like(like), TodoTask.description.like(like), TodoTask.notes.like(like))).limit(10)).all()
    links = db.scalars(select(QuickLink).where(QuickLink.user_id == user.id, or_(QuickLink.title.like(like), QuickLink.url.like(like), QuickLink.description.like(like))).limit(10)).all()
    memos = db.scalars(select(Memo).where(Memo.user_id == user.id, or_(Memo.title.like(like), Memo.content.like(like))).limit(10)).all()
    return ok({"records": [dump(x) for x in records], "plans": [dump(x) for x in plans], "todos": [todo_dict(x) for x in todos], "links": [dump(x) for x in links], "memos": [dump(x) for x in memos]})


@router.get("/dashboard")
def dashboard(month: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    month = month or date.today().strftime("%Y-%m")
    month_start = date.fromisoformat(f"{month}-01")
    month_end = date(month_start.year + (month_start.month == 12), 1 if month_start.month == 12 else month_start.month + 1, 1) - timedelta(days=1)
    hours = db.scalar(select(func.coalesce(func.sum(WorkRecord.hours), 0)).where(WorkRecord.user_id == user.id, WorkRecord.work_date.between(month_start, month_end))) or 0
    total = db.scalar(select(func.count(TodoTask.id)).where(TodoTask.user_id == user.id, TodoTask.archived.is_(False))) or 0
    done = db.scalar(select(func.count(TodoTask.id)).where(TodoTask.user_id == user.id, TodoTask.status == "done", TodoTask.archived.is_(False))) or 0
    records = db.execute(select(WorkRecord.work_date, func.sum(WorkRecord.hours)).where(WorkRecord.user_id == user.id, WorkRecord.work_date.between(month_start, month_end)).group_by(WorkRecord.work_date).order_by(WorkRecord.work_date)).all()
    tools = db.execute(select(ToolUsageLog.tool_name, func.count(ToolUsageLog.id)).where(ToolUsageLog.user_id == user.id).group_by(ToolUsageLog.tool_name).order_by(desc(func.count(ToolUsageLog.id)))).all()
    return ok({"cards": {"hours": round(float(hours), 1), "todo_total": total, "todo_done": done, "completion_rate": round(done / total * 100) if total else 0}, "work_trend": [{"date": str(d), "hours": float(h)} for d, h in records], "tool_usage": [{"name": n, "count": c} for n, c in tools]})
