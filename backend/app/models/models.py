from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class User(TimestampMixin, Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120), default="管理员")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspace"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(30), default="personal")
    color: Mapped[str] = mapped_column(String(20), default="#5b5ce2")
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class Project(TimestampMixin, Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    goal: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="planning", index=True)
    tech_stack: Mapped[list] = mapped_column(JSON, default=list)
    repo_url: Mapped[str] = mapped_column(String(1000), default="")
    local_path: Mapped[str] = mapped_column(String(1000), default="")
    deployment_url: Mapped[str] = mapped_column(String(1000), default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class WorkRecord(TimestampMixin, Base):
    __tablename__ = "work_record"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    work_date: Mapped[date] = mapped_column(Date, index=True)
    hours: Mapped[float] = mapped_column(Float, default=0)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("todo_task.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"), nullable=True, index=True)


class WorkPlan(TimestampMixin, Base):
    __tablename__ = "work_plan"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"), nullable=True, index=True)


class EventReminder(TimestampMixin, Base):
    __tablename__ = "event_reminder"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    remind_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    repeat_type: Mapped[str] = mapped_column(String(20), default="once")
    status: Mapped[str] = mapped_column(String(20), default="active")
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    schedule_type: Mapped[str] = mapped_column(String(20), default="once")
    time_of_day: Mapped[str | None] = mapped_column(String(8), nullable=True)
    weekdays: Mapped[list | None] = mapped_column(JSON, nullable=True)
    month_days: Mapped[list | None] = mapped_column(JSON, nullable=True)
    next_trigger_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    last_trigger_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Shanghai")


class TodoTask(TimestampMixin, Base):
    __tablename__ = "todo_task"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("todo_task.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="todo", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    group_name: Mapped[str] = mapped_column(String(80), default="默认分组")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    timer_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, default=0)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"), nullable=True, index=True)
    subtasks: Mapped[list["TodoSubtask"]] = relationship("TodoSubtask", cascade="all, delete-orphan", lazy="selectin")


class TodoSubtask(Base):
    __tablename__ = "todo_subtask"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("todo_task.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class QuickLink(TimestampMixin, Base):
    __tablename__ = "quick_link"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    url: Mapped[str] = mapped_column(String(1000))
    category: Mapped[str] = mapped_column(String(80), default="未分类")
    description: Mapped[str] = mapped_column(String(500), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"), nullable=True, index=True)


class ToolUsageLog(Base):
    __tablename__ = "tool_usage_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    tool_name: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(80), default="use")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class SystemConfig(Base):
    __tablename__ = "system_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    config_key: Mapped[str] = mapped_column(String(100), index=True)
    config_value: Mapped[dict] = mapped_column(JSON, default=dict)


class AccountCategory(TimestampMixin, Base):
    """用户自己的收支分类；默认分类也落库，便于后续自定义。"""
    __tablename__ = "account_category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    entry_type: Mapped[str] = mapped_column(String(20), default="expense")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class AccountEntry(TimestampMixin, Base):
    __tablename__ = "account_entry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    entry_type: Mapped[str] = mapped_column(String(20), index=True)
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(80), index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    entry_date: Mapped[date] = mapped_column(Date, index=True)


class Memo(TimestampMixin, Base):
    __tablename__ = "memo"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)


class ContactSubmission(TimestampMixin, Base):
    """官网公开联系表单提交的需求信息。"""
    __tablename__ = "contact_submission"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip: Mapped[str] = mapped_column(String(45), default="")
    name: Mapped[str] = mapped_column(String(120))
    contact: Mapped[str] = mapped_column(String(255))
    project_type: Mapped[str] = mapped_column(String(80), default="")
    budget: Mapped[str] = mapped_column(String(80), default="")
    timeline: Mapped[str] = mapped_column(String(80), default="")
    materials: Mapped[str] = mapped_column(String(80), default="")
    message: Mapped[str] = mapped_column(Text)
    consent: Mapped[bool] = mapped_column(Boolean, default=False)


class ProjectMilestone(TimestampMixin, Base):
    __tablename__ = "project_milestone"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)


class ProjectVersion(TimestampMixin, Base):
    __tablename__ = "project_version"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="planned")
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    release_notes: Mapped[str] = mapped_column(Text, default="")


class ProjectCommit(TimestampMixin, Base):
    __tablename__ = "project_commit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)
    commit_hash: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(String(500))
    branch: Mapped[str] = mapped_column(String(160), default="main")
    committed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    url: Mapped[str] = mapped_column(String(1000), default="")
