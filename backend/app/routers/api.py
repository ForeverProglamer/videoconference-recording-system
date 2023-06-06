import logging
from typing import Annotated

from fastapi import APIRouter, status, Response, Request, Cookie, HTTPException
from fastapi.responses import RedirectResponse

from app.persistence import postgres as db
from app.schemas.conference import (
    ConferenceCreate,
    ConferenceRead,
    ConferenceUpdate
)
from app.schemas.user import UserCreate, UserBase
from app.utils.auth import check_password

log = logging.getLogger(__name__)

router = APIRouter(prefix='/api', tags=['API'])

Token = Annotated[str | None, Cookie()]


@router.post('/users/sign-up')
def sign_up(
    user: UserCreate,
    token: Token = None
) -> RedirectResponse:
    if token:
        return RedirectResponse('/', status.HTTP_302_FOUND)

    db.create_user(user)
    return RedirectResponse('/sign-in', status.HTTP_302_FOUND)


@router.post('/users/sign-in')
def sing_in(
    user: UserBase,
    token: Token = None
) -> RedirectResponse:
    if token:
        return RedirectResponse('/', status.HTTP_302_FOUND)

    user_in_db = db.get_user(user)

    if not user_in_db:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            'Incorrect login'
        )

    if not check_password(user.password, user_in_db.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            'Incorrect password'
        )

    session = db.create_session(user_in_db)

    response = RedirectResponse('/', status.HTTP_302_FOUND)

    response.set_cookie(
        key='token',
        value=session.token,
        expires=session.expires_at.astimezone(),
        httponly=True,
        samesite='strict'
    )

    return response


@router.post('/users/sign-out')
def sign_out(token: Token = None) -> RedirectResponse:
    response = RedirectResponse('/sign-in', status.HTTP_302_FOUND)

    if not token:
        return response

    db.delete_session(token)
    response.delete_cookie('token')

    return response


@router.get('/conferences')
def get_conferences(token: Token = None) -> list[ConferenceRead]:
    user_id = 1
    return db.get_conferences(user_id)


@router.post('/conferences', status_code=status.HTTP_201_CREATED)
def create_conference(
    conference: ConferenceCreate,
    request: Request,
    response: Response,
    token: Token = None
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
