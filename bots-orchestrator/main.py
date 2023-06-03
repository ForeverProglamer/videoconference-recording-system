import logging

from fastapi import FastAPI

from app.orchestrator import BotsOrchestrator
from app.orchestrator.exceptions import (
    ConferenceIsNotBeingRecordedError,
    ConferenceAlreadyBeingRecordedError
)
from app.schema import Conference

logging.basicConfig(
    format='[%(asctime)s]:%(levelname)s:%(name)s:%(module)s:%(message)s',
    level=logging.INFO
)
log = logging.getLogger(__name__)

app = FastAPI(title='Bots Orchestration API')
orchestrator = BotsOrchestrator()


@app.get('/')
def root() -> dict[str, str]:
    return {'status': 'up'}


@app.post('/recording/start')
def start_conference_recording(conference: Conference) -> dict[str, str]:
    try:
        orchestrator.start_recording(conference)
    except ConferenceAlreadyBeingRecordedError as e:
        log.exception(e)
        return {'status': 'already being recorded'}
    return {'status': 'started'}


@app.post('/recording/{conference_id}/stop')
def stop_conference_recording(conference_id: int) -> dict[str, str]:
    try:
        orchestrator.stop_recording(conference_id)
    except ConferenceIsNotBeingRecordedError as e:
        log.exception(e)
        return {'status': 'is not being recorded'}
    return {'status': 'stopped'}
