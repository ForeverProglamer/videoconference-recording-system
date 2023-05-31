import logging
import os
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from psycopg2.errors import Error
from pypika import Table, PostgreSQLQuery as Query

from app.schemas.user import UserCreate, UserRead
from app.schemas.conference import ConferenceCreate, ConferenceRead, Recording, SettingsBase
from app.utils import generate_recording_filename

POSTGRES_DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT'),
    'dbname': os.getenv('POSTGRES_DB')
}

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
def create_user(conn: connection, user: UserCreate) -> UserRead:
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .into(users)
                .columns(*user.dict().keys())
                .insert(*user.dict().values())
                .returning(users.id).get_sql()
            )
            return UserRead(id=cur.fetchone()[0], **user.dict())
    except Error as e:
        log.exception(e)


@pg_connection()
def create_conference(
    conn: connection,
    user_id: int,
    conference: ConferenceCreate
) -> ConferenceRead:
    conf_without_settings = conference.dict(exclude={'settings'})
    settings = conference.settings.dict()
    recording = Recording(
        filename=generate_recording_filename(user_id, conference)
    )
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .into(conferences)
                .columns(conferences.user_id, *conf_without_settings.keys())
                .insert(user_id, *conf_without_settings.values())
                .returning(conferences.id).get_sql()
            )

            conference_id = cur.fetchone()[0]

            cur.execute(Query
                .into(conference_settings)
                .columns(conference_settings.conference_id, *settings.keys())
                .insert(conference_id, *settings.values()).get_sql()
            )

            cur.execute(Query
                .into(recordings)
                .columns(recordings.conference_id, *recording.dict().keys())
                .insert(conference_id, *recording.dict().values()).get_sql()
            )
            return ConferenceRead(
                id=conference_id,
                user_id=user_id,
                recording=recording,
                **conference.dict()
            )
    except Error as e:
        log.exception(e)


@pg_connection()
def get_conferences(conn: connection, user_id: int) -> list[ConferenceRead]:
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
                .where(conferences.user_id == user_id).get_sql()
            )
            return [
                ConferenceRead(
                    settings=SettingsBase(**item),
                    recording=Recording(**item),
                    **item
                )
                for item in cur
            ]
    except Error as e:
        log.exception(e)