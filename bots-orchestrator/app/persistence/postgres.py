import logging
import os
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.errors import Error
from pypika import Table, PostgreSQLQuery as Query

from app.schema import RecordingStatus

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
def update_recording_status(
    conn: connection,
    conference_id: int,
    status: RecordingStatus
) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(Query
                .update(recordings)
                .set(recordings.status, status)
                .where(recordings.conference_id == conference_id).get_sql()
            )
    except Error as e:
        log.exception(e)
