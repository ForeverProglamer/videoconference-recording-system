import json
import os

import httpx

from app.schema import Conference

API_DOMAIN = os.getenv('BOTS_API_DOMAIN')
API_PORT = os.getenv('BOTS_API_PORT')

API_URL = f'http://{API_DOMAIN}:{API_PORT}'
START_RECORDING_URI = '/recording/start'
STOP_RECORDING_URI = '/recording/{}/stop'


def start_conference_recording(conference: Conference) -> httpx.Response:
    url = f'{API_URL}{START_RECORDING_URI}'
    response = httpx.post(url, data=json.loads(conference.json()))
    return response


def stop_conference_recording(conference_id: int) -> httpx.Response:
    url = f'{API_URL}{STOP_RECORDING_URI.format(conference_id)}'
    response = httpx.post(url)
    return response
