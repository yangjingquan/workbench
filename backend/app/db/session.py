from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """创建表并为旧版提醒表补齐周期调度字段。"""
    Base.metadata.create_all(bind=engine)
    columns = {item["name"] for item in inspect(engine).get_columns("event_reminder")}
    additions = {
        "schedule_type": "VARCHAR(20) NOT NULL DEFAULT 'once'",
        "time_of_day": "VARCHAR(8) NULL",
        "weekdays": "JSON NULL",
        "month_days": "JSON NULL",
        "next_trigger_at": "DATETIME NULL",
        "last_trigger_at": "DATETIME NULL",
        "timezone": "VARCHAR(64) NOT NULL DEFAULT 'Asia/Shanghai'",
    }
    timezone_added = "timezone" not in columns
    with engine.begin() as conn:
        for name, ddl in additions.items():
            if name not in columns:
                conn.execute(text(f"ALTER TABLE event_reminder ADD COLUMN {name} {ddl}"))
        conn.execute(text("UPDATE event_reminder SET schedule_type = CASE WHEN repeat_type IN ('daily','weekly','monthly') THEN repeat_type ELSE COALESCE(NULLIF(schedule_type, ''), 'once') END"))
        conn.execute(text("UPDATE event_reminder SET time_of_day = DATE_FORMAT(remind_at, '%H:%i:%s') WHERE time_of_day IS NULL AND schedule_type <> 'once'"))
        conn.execute(text("UPDATE event_reminder SET weekdays = JSON_ARRAY(MOD(DAYOFWEEK(remind_at) + 5, 7) + 1) WHERE schedule_type = 'weekly' AND weekdays IS NULL"))
        conn.execute(text("UPDATE event_reminder SET month_days = JSON_ARRAY(DAY(remind_at)) WHERE schedule_type = 'monthly' AND month_days IS NULL"))
        conn.execute(text("UPDATE event_reminder SET next_trigger_at = remind_at WHERE next_trigger_at IS NULL AND status = 'active'"))
        if timezone_added:
            legacy_zone = ZoneInfo("Asia/Shanghai")
            rows = conn.execute(text("SELECT id, remind_at, snoozed_until, next_trigger_at, last_trigger_at FROM event_reminder")).mappings().all()

            def legacy_to_utc(value: datetime | None) -> datetime | None:
                if value is None:
                    return None
                return value.replace(tzinfo=legacy_zone).astimezone(dt_timezone.utc).replace(tzinfo=None)

            for row in rows:
                conn.execute(
                    text("""
                        UPDATE event_reminder
                        SET timezone = :timezone,
                            remind_at = :remind_at,
                            snoozed_until = :snoozed_until,
                            next_trigger_at = :next_trigger_at,
                            last_trigger_at = :last_trigger_at
                        WHERE id = :id
                    """),
                    {
                        "id": row["id"],
                        "timezone": "Asia/Shanghai",
                        "remind_at": legacy_to_utc(row["remind_at"]),
                        "snoozed_until": legacy_to_utc(row["snoozed_until"]),
                        "next_trigger_at": legacy_to_utc(row["next_trigger_at"]),
                        "last_trigger_at": legacy_to_utc(row["last_trigger_at"]),
                    },
                )
