from datetime import datetime
import logging
import os
from functools import reduce, wraps
from typing import Callable, Iterable, TypeVar, ParamSpec

from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from psycopg2.errors import Error
from pypika import Table, PostgreSQLQuery as Query, Criterion, Field, Order

from app.schemas.user import (
    UserCreate, UserRead, UserBase, SessionBase, UserInDb
)
from app.schemas.conference import (
    ConferenceCreate, ConferenceRead, Recording, RecordingStatus, SettingsBase
)
from app.utils.auth import hash_password
from app.utils.recording import generate_recording_filename

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
sessions = Table('sessions')
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
    user_ = user.copy(update={'password': hash_password(user.password)})
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .into(users)
                .columns(*user_.dict().keys())
                .insert(*user_.dict().values())
                .returning(users.id).get_sql()
            )

            return UserRead(**user_.dict())
    except Error as e:
        log.exception(e)


@pg_connection()
def get_user(conn: connection, user: UserBase) -> UserInDb | None:
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(Query
                .from_(users)
                .select(users.star)
                .where(users.login == user.login).get_sql()
            )

            user_data = cur.fetchone()
            if not user_data:
                return None
            return UserInDb(**user_data)
    except Error as e:
        log.exception(e)


@pg_connection()
def create_session(conn: connection, user: UserInDb) -> SessionBase:
    session = SessionBase()
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .into(sessions)
                .columns(
                    sessions.user_id, sessions.token, sessions.expires_at
                )
                .insert(user.id, session.token, session.expires_at).get_sql()
            )
            return session
    except Error as e:
        log.exception(e)


@pg_connection()
def get_session(conn: connection, user: UserInDb) -> SessionBase | None:
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sessions
                .select(sessions.token, sessions.expires_at)
                .where(sessions.user_id == user.id).get_sql()
            )

            item = cur.fetchone()
            if not item:
                return None
            return SessionBase(**item)
    except Error as e:
        log.exception(e)


@pg_connection()
def delete_session(conn: connection, token: str) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .from_(sessions)
                .delete()
                .where(sessions.token == token).get_sql()
            )
    except Error as e:
        log.exception(e)


@pg_connection()
def create_conference(
    conn: connection,
    token: str,
    conference: ConferenceCreate
) -> ConferenceRead:
    conf_without_settings = conference.dict(exclude={'settings'})
    settings = conference.settings.dict()
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .from_(sessions)
                .select(sessions.user_id)
                .where(sessions.token == token).get_sql()
            )

            user_id = cur.fetchone()[0]

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

            recording = Recording(
                filename=generate_recording_filename(
                    user_id, conference, conference_id
                )
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
def get_upcoming_conferences(
    conn: connection, token: str
) -> list[ConferenceRead]:
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_prepare_get_conferences_query(
                token,
                criterions=[recordings.status == RecordingStatus.SCHEDULED],
                orders=[(conferences.start_time, Order.asc)]
            ))
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


@pg_connection()
def get_in_progress_conferences(
    conn: connection, token: str
) -> list[ConferenceRead]:
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_prepare_get_conferences_query(
                token,
                criterions=[recordings.status == RecordingStatus.IN_PROGRESS],
                orders=[(conferences.start_time, Order.asc)]
            ))
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


@pg_connection()
def get_finished_conferences(
    conn: connection, token: str
) -> list[ConferenceRead]:
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_prepare_get_conferences_query(
                token,
                criterions=[recordings.status == RecordingStatus.FINISHED],
                orders=[(conferences.start_time, Order.asc)]
            ))
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


@pg_connection()
def get_conference(
    conn: connection, token: str, conference_id: int
) -> ConferenceRead:
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_prepare_get_conferences_query(
                token, criterions=[conferences.id == conference_id]
            ))

            item = cur.fetchone()

            return ConferenceRead(
                settings=SettingsBase(**item),
                recording=Recording(**item),
                **item
            )
    except Error as e:
        log.exception(e)


def _prepare_get_conferences_query(
    token: str, 
    *,
    criterions: Iterable[Criterion] = None,
    orders: Iterable[tuple[Field, Order]] = None
) -> str:
    query = (Query
        .from_(conferences)
        .inner_join(conference_settings)
        .on(conferences.id == conference_settings.conference_id)
        .inner_join(recordings)
        .on(conferences.id == recordings.conference_id)
        .inner_join(sessions)
        .on(conferences.user_id == sessions.user_id)
        .select(
            conferences.id, conferences.user_id, conferences.title,
            conferences.invite_link, conferences.start_time,
            conferences.end_time, conferences.platform,
            conference_settings.participant_name,
            conference_settings.disclaimer_message,
            recordings.filename, recordings.status
        )
        .where(sessions.token == token)
    )

    if criterions:
        query = reduce(
            lambda query, criterion: query.where(criterion), criterions, query
        )

    if orders:
        query = reduce(
            lambda query, order: query.orderby(order[0], oreder=order[1]),
            orders,
            query
        )

    return query.get_sql()


@pg_connection()
def delete_conference(
    conn: connection, token: str, conference_id: int
) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .from_(conferences)
                .delete()
                .where(
                    conferences.user_id == sessions.select(sessions.user_id)
                    .where(sessions.token == token)
                )
                .where(conferences.id == conference_id).get_sql()
            )
    except Error as e:
        log.exception(e)


@pg_connection()
def stop_recording(
    conn: connection, token: str, conference_id: int
) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .update(conferences)
                .set(conferences.end_time, datetime.now())
                .where(
                    conferences.user_id == sessions.select(sessions.user_id)
                    .where(sessions.token == token)
                )
                .where(conferences.id == conference_id).get_sql()
            )
    except Error as e:
        log.exception(e)