from typing import TypeVar

from app.schemas.conference import ConferenceBase


Conference = TypeVar('Conference', bound=ConferenceBase)


def generate_recording_filename(
    user_id: int,
    conference: Conference
) -> str:
    link = conference.invite_link.replace("https://", "")
    return f'{user_id}_{link}_{conference.start_time}.mp4'
