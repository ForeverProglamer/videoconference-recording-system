from hashlib import md5
from typing import TypeVar

from app.schemas.conference import ConferenceBase

ENCODING = 'utf-8'

Conference = TypeVar('Conference', bound=ConferenceBase)


def generate_recording_filename(
    user_id: int,
    conference: Conference,
    conference_id: int
) -> str:
    filename = (
        f'{user_id}-{conference_id}-'
        f'{conference.invite_link}-{conference.start_time}'
    ).encode(ENCODING)

    return f'{md5(filename)}.mp4'
