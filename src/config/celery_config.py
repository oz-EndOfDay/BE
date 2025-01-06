from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "delete-expired-diaries": {
        "task": "tasks.delete_expired_diaries",
        "schedule": crontab(hour="0", minute="0"),  # 매일 자정에 실행
    },
}
