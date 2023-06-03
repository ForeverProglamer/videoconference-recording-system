from threading import Thread
from time import sleep
from typing import Self

from app.orchestrator.conference_bot import from_conference
from app.orchestrator.exceptions import (
    ConferenceAlreadyBeingRecordedError,
    ConferenceIsNotBeingRecordedError
)
from app.persistence.postgres import update_recording_status
from app.schema import Conference, RecordingStatus


class Worker(Thread):

    _SLEEP_DURATION_SECONDS = 30

    def __init__(self: Self, conference: Conference) -> None:
        super().__init__(daemon=True)
        self._to_run = True
        self._conference = conference

    def stop(self: Self) -> None:
        self._to_run = False

    def run(self: Self) -> None:
        bot = from_conference(self._conference)

        bot.join_conference()
        bot.send_message()

        update_recording_status(
            self._conference.id, RecordingStatus.IN_PROGRESS
        )

        while self._to_run:
            sleep(self._SLEEP_DURATION_SECONDS)

        bot.leave_conference()

        update_recording_status(
            self._conference.id, RecordingStatus.FINISHED
        )


class BotsOrchestrator:
    def __init__(self: Self) -> None:
        self._workers: dict[int, Worker] = {}
    
    def start_recording(self: Self, conference: Conference) -> None:
        if conference.id in self._workers:
            raise ConferenceAlreadyBeingRecordedError(
                f'Conference with id {conference.id} is '
                'already being recorded.'
            )

        worker = Worker(conference)
        self._workers[conference.id] = worker
        worker.start()

    def stop_recording(self: Self, conference_id: int) -> None:
        if conference_id not in self._workers:
            raise ConferenceIsNotBeingRecordedError(
                f'There is no conference with id {conference_id} '
                'being recorded.'
            )

        worker = self._workers[conference_id]
        worker.stop()

        del self._workers[conference_id]

    def __del__(self: Self) -> None:
        for worker in self._workers.values():
            worker.stop()
