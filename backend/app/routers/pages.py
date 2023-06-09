import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.persistence import postgres as db

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
    
    conferences = db.get_conferences(token)

    return templates.TemplateResponse(
        'index.html',
        {'request': request, 'page_name': 'Home', 'conferences': conferences}
    )


@router.get('/history', response_class=HTMLResponse)
def history(request: Request, token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        'history.html', {'request': request, 'page_name': 'History'}
    )


@router.get('/settings', response_class=HTMLResponse)
def settings(request: Request, token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        'settings.html', {'request': request, 'page_name': 'Settings'}
    )


# @router.get('/recordings/{recording_id}/')
@router.get('/conferences/{conference_id}/recording')
def recordings(request: Request, token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)

    # Get recording data by id and session token
    
    # If there is no such recording return not found page

    return templates.TemplateResponse(
        'recording.html', {'request': request, 'page_name': 'Recording'}
    )