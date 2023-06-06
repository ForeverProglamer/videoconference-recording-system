import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, TypeVar, ParamSpec, Mapping, Any

from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from psycopg2.errors import Error
from pypika import Table, PostgreSQLQuery as Query

from app.schema import Settings, Recording, Conference, RecordingStatus

POSTGRES_DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT'),
    'dbname': os.getenv('POSTGRES_DB')
}

DELTA_MINUTES = 2
BIG_DELTA_MINUTES = 2
SMALL_DELTA_MINUTES = 1

T = TypeVar('T')
P = ParamSpec('P')

FuncToDecorate = Callable[[connection, P.args, P.kwargs], T]

log = logging.getLogger(__name__)

users = Table('users')
conferences = Table('conferences')
conference_settings = Table('conference_settings')
recordings = Table('recordings')


def pg_connection(
    autocommit: bool = False
) -> Callable[[FuncToDecorate], Callable[P, T]]:
    def fn_wrapper(fn: FuncToDecorate) -> Callable[P, T]:
        @wraps(fn)
        def args_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            conn = connect(**POSTGRES_DB_CONFIG)
            conn.autocommit = autocommit
            try:
                res = fn(conn, *args, **kwargs)
            except Error as e:
                log.exception(e)
                if not autocommit:
                    conn.rollback()
                raise e
            else:
                if not autocommit:
                    conn.commit()
            finally:
                conn.close()
            return res
        return args_wrapper
    return fn_wrapper


@pg_connection()
def get_upcoming_conferences(conn: connection) -> list[Conference]:
    now = datetime.now()
    start = now - timedelta(minutes=SMALL_DELTA_MINUTES)
    stop = now + timedelta(minutes=BIG_DELTA_MINUTES)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(Query
                .from_(conferences)
                .inner_join(conference_settings)
                .on(conferences.id == conference_settings.conference_id)
                .inner_join(recordings)
                .on(conferences.id == recordings.conference_id)
                .select(
                    conferences.id, conferences.user_id, conferences.title,
                    conferences.invite_link, conferences.start_time,
                    conferences.end_time, conferences.platform,
                    conference_settings.participant_name,
                    conference_settings.disclaimer_message,
                    recordings.filename, recordings.status
                )
                .where(recordings.status == RecordingStatus.SCHEDULED)
                .where(conferences.start_time[start:stop]).get_sql()
            )

            return [
                Conference(
                    settings=Settings(**item),
                    recording=Recording(**item),
                    **item
                )
                for item in cur
            ]
    except Error as e:
        log.exception(e)


@pg_connection()
def get_ending_conferences(conn: connection) -> list[Conference]:
    now = datetime.now()
    start = now - timedelta(minutes=BIG_DELTA_MINUTES)
    stop = now + timedelta(minutes=SMALL_DELTA_MINUTES)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(Query
                .from_(conferences)
                .inner_join(conference_settings)
                .on(conferences.id == conference_settings.conference_id)
                .inner_join(recordings)
                .on(conferences.id == recordings.conference_id)
                .select(
                    conferences.id, conferences.user_id, conferences.title,
                    conferences.invite_link, conferences.start_time,
                    conferences.end_time, conferences.platform,
                    conference_settings.participant_name,
                    conference_settings.disclaimer_message,
                    recordings.filename, recordings.status
                )
                .where(recordings.status == RecordingStatus.IN_PROGRESS)
                .where(conferences.end_time[start:stop]).get_sql()
            )

            return [
                Conference(
                    settings=Settings(**item),
                    recording=Recording(**item),
                    **item
                )
                for item in cur
            ]
    except Error as e:
        log.exception(e)
