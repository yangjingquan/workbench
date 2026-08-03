from datetime import datetime
from unittest.mock import Mock

from app.api.routes import _ensure_todo_completion_record
from app.models import TodoTask, WorkRecord


def test_completed_todo_creates_one_linked_work_record():
    task = TodoTask(
        id=12,
        title="整理移动端适配",
        description="补齐 Todo 和弹窗体验",
        notes="完成后回顾",
        tags=["开发需求"],
        elapsed_seconds=3600,
        completed_at=datetime(2026, 8, 3, 10, 30),
    )
    db = Mock()
    db.scalar.return_value = None

    _ensure_todo_completion_record(task, 7, db)

    record = db.add.call_args.args[0]
    assert isinstance(record, WorkRecord)
    assert record.user_id == 7
    assert record.task_id == 12
    assert record.title == "整理移动端适配"
    assert record.work_date.isoformat() == "2026-08-03"
    assert record.hours == 1
    assert "补齐 Todo 和弹窗体验" in record.content


def test_completed_todo_does_not_duplicate_an_existing_record():
    task = TodoTask(id=12, title="已有记录")
    db = Mock()
    db.scalar.return_value = WorkRecord(task_id=12)

    _ensure_todo_completion_record(task, 7, db)

    db.add.assert_not_called()
