from fastapi import APIRouter, status, Response, Request

from app.persistence import postgres as db
from app.schemas.conference import (
    ConferenceCreate,
    ConferenceRead,
    ConferenceUpdate
)
from app.schemas.user import UserRead, UserCreate

router = APIRouter(prefix='/api')


@router.post('/users')
def create_user(
    user: UserCreate, request: Request, response: Response
) -> UserRead:
    created_user = db.create_user(user)
    response.headers['location'] = f'{request.url}/{created_user.id}'
    return created_user


@router.get('/conferences')
def get_conferences() -> list[ConferenceRead]:
    user_id = 1
    return db.get_conferences(user_id)


@router.post('/conferences', status_code=status.HTTP_201_CREATED)
def create_conference(
    conference: ConferenceCreate, request: Request, response: Response
) -> ConferenceRead:
    user_id = 1
    created_conference = db.create_conference(user_id, conference)
    response.headers['location'] = f'{request.url}/{created_conference.id}'
    return created_conference


# @router.patch('/conferences/{conference_id}')
# def update_conference(conference: ConferenceUpdate) -> ConferenceRead:
#     ...


# @router.delete(
#     '/conferences/{conference_id}',
#     status_code=status.HTTP_204_NO_CONTENT
# )
# def delete_conference() -> None:
#     ...


# @router.post('/recordings/{recording_id}/stop')
# def stop_recording():
#     ...
