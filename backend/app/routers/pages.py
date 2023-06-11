import logging
import os
from typing import Annotated

from fastapi import APIRouter, Cookie, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.persistence import postgres as db

VIDEO_HOST = os.getenv('VIDEO_HOST')

log = logging.getLogger(__name__)

router = APIRouter(tags=['Pages'])

templates = Jinja2Templates(directory='templates')

Token = Annotated[str | None, Cookie()]


@router.get('/sign-in', response_class=HTMLResponse)
def sign_in(request: Request, token: Token = None):
    if token:
        return RedirectResponse('/', status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        'signx.html', {'request': request, 'page_name': 'Sign In'}
    )


@router.get('/sign-up', response_class=HTMLResponse)
def sign_up(request: Request, token: Token = None):
    if token:
        return RedirectResponse('/', status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        'signx.html', {'request': request, 'page_name': 'Sign Up'}
    )


@router.get('/', response_class=HTMLResponse)
def home(request: Request, token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)
    
    conferences = db.get_upcoming_conferences(token)

    return templates.TemplateResponse(
        'index.html',
        {'request': request, 'page_name': 'Home', 'conferences': conferences}
    )


@router.get('/in-progress', response_class=HTMLResponse)
def in_progress(request: Request, token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)

    conferences = db.get_in_progress_conferences(token)

    return templates.TemplateResponse(
        'in-progress.html',
        {
            'request': request,
            'page_name': 'History',
            'conferences': conferences
        }
    )


@router.get('/history', response_class=HTMLResponse)
def history(request: Request, token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)

    conferences = db.get_finished_conferences(token)

    return templates.TemplateResponse(
        'history.html',
        {
            'request': request,
            'page_name': 'History',
            'conferences': conferences
        }
    )


@router.get('/settings', response_class=HTMLResponse)
def settings(request: Request, token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        'settings.html', {'request': request, 'page_name': 'Settings'}
    )


@router.get(
    '/conferences/{conference_id}/recording',
    response_class=HTMLResponse
)
def recordings(conference_id: int, request: Request, token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)

    conference = db.get_conference(token, conference_id)
    
    return templates.TemplateResponse(
        'recording.html',
        {
            'request': request,
            'page_name': 'Recording',
            'video_host': VIDEO_HOST,
            'conference': conference
        }
    )