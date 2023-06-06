from datetime import datetime
from enum import StrEnum
from typing import Self, Type, Container

from pydantic import BaseModel


class ConferencingPlatform(StrEnum):
    ZOOM = 'zoom'
    MEET = 'google_meet'


class RecordingStatus(StrEnum):
    SCHEDULED = 'scheduled'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class Model(BaseModel):
    @classmethod
    def get_fields(
        cls: Type[Self],
        *,
        include: Container[str] | None = None,
        exclude: Container[str] | None = None
    ) -> list[str]:
        if include and exclude:
            raise Exception('You cannot specify both include and exclude.')

        fields = cls.schema().get('properties').keys()
        if include:
            return [f for f in fields if f in include]
        elif exclude:
            return [f for f in fields if f not in exclude]
        else:
            return fields


class Settings(Model):
    participant_name: str
    disclaimer_message: str


class Recording(Model):
    filename: str
    status: RecordingStatus


class Conference(Model):
    id: int
    user_id: int
    title: str
    invite_link: str
    start_time: datetime
    end_time: datetime
    platform: ConferencingPlatform
    settings: Settings
    recording: Recording
