from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    user_id: int
    title: str
    message: str
    is_read: bool = False


class NotificationCreate(NotificationBase):
    pass


class NotificationInDBRequest(NotificationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
