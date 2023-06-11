import logging
from typing import Annotated, Any

from fastapi import (
    APIRouter,status, Response, Request, Cookie, HTTPException, Header
)
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

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

templates = Jinja2Templates(directory='templates')

Token = Annotated[str | None, Cookie()]

Accept = Annotated[str | None, Header()]


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

    session = db.get_session(user_in_db)

    if not session:
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
    return db.get_conferences(token)


@router.post('/conferences', status_code=status.HTTP_201_CREATED)
def create_conference(
    conference: ConferenceCreate,
    request: Request,
    accept: Accept = 'application/json',
    token: Token = None
) -> Any:
    created_conference = db.create_conference(token, conference)
    log.info(f'{accept = }')
    if accept == 'text/html':
        return templates.TemplateResponse(
            'conference.html',
            context={'request': request, 'conference': created_conference},
            status_code=status.HTTP_201_CREATED
        )
    return created_conference


# @router.patch('/conferences/{conference_id}')
# def update_conference(conference: ConferenceUpdate) -> ConferenceRead:
#     ...


@router.delete(
    '/conferences/{conference_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_conference(conference_id: int, token: Token = None) -> None:
    db.delete_conference(token, conference_id)


@router.post(
    '/conferences/{conference_id}/recording/stop',
    status_code=status.HTTP_204_NO_CONTENT
)
def stop_recording(conference_id: int, token: Token = None) -> None:
    db.stop_recording(token, conference_id)
