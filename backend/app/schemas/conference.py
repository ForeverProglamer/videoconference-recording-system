from datetime import datetime
from enum import StrEnum
from typing import Type, Self, Container

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


class Recording(Model):
    filename: str
    status: RecordingStatus = RecordingStatus.SCHEDULED


class SettingsBase(Model):
    participant_name: str
    disclaimer_message: str


class SettingsCreate(SettingsBase):
    ...


class SettingsRead(SettingsBase):
    id: int
    conference_id: int


class SettingsUpdate(SettingsBase):
    participant_name: str | None = None
    disclaimer_message: str | None = None


class ConferenceBase(Model):
    title: str
    invite_link: str
    start_time: datetime
    end_time: datetime | None = None
    platform: ConferencingPlatform
    settings: SettingsBase


class ConferenceCreate(ConferenceBase):
    ...


class ConferenceRead(ConferenceBase):
    id: int
    recording: Recording


class ConferenceUpdate(ConferenceBase):
    title: str | None = None
    invite_link: str | None = None
    start_time: datetime | None = None
    platform: ConferencingPlatform | None = None
    settings: SettingsUpdate | None = None
