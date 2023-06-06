import logging
from threading import Thread, current_thread
from time import sleep

from app.postgres import get_upcoming_conferences, get_ending_conferences
from app.orchestrator_client import (
    start_conference_recording,
    stop_conference_recording
)

SLEEP_TIME_SECONDS = 60

logging.basicConfig(
    format='[%(asctime)s]:%(levelname)s:%(name)s:%(module)s:%(message)s',
    level=logging.INFO
)
log = logging.getLogger(__name__)


def monitor_upcoming_conferences() -> None:
    t_name = current_thread().name
    log.info(f'{t_name}: started monitoring upcoming confs')
    while True:
        try:
            conferences = get_upcoming_conferences()

            for conference in conferences:
                log.info(conference)
                response = start_conference_recording(conference)
                log.info(
                    f'{t_name}: Response: {response.status_code},'
                    f' {response.json()}'
                )

            sleep(SLEEP_TIME_SECONDS)
        except Exception as e:
            log.exception(e)


def monitor_ending_conferences() -> None:
    t_name = current_thread().name
    log.info(f'{t_name}: started monitoring ending confs')
    while True:
        try:
            conferences = get_ending_conferences()

            for conference in conferences:
                log.info(f'{t_name}: {conference}')
                response = stop_conference_recording(conference.id)
                log.info(
                    f'{t_name}: Response: {response.status_code},'
                    f' {response.json()}'
                )

            sleep(SLEEP_TIME_SECONDS)
        except Exception as e:
            log.exception(e)


def main() -> None:
    t1 = Thread(target=monitor_upcoming_conferences, args=[])
    t2 = Thread(target=monitor_ending_conferences, args=[])

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == '__main__':
    main()
