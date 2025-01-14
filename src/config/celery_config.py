from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "delete-expired-diaries": {
        "task": "tasks.delete_expired_diaries",
        "schedule": crontab(hour="6", minute="0"),  # 매일 오전 6시에 실행
    },
    "delete-expired-users": {
        "task": "tasks.delete_expired_users",
        "schedule": crontab(hour="6", minute="20"),  # 매일 오전 6시 20분에 실행
    },
}
