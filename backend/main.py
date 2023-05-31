import logging
from datetime import datetime

from fastapi import FastAPI

from app.routers import api

app = FastAPI()

logging.basicConfig(
    format='[%(asctime)s]:%(levelname)s:%(name)s:%(module)s:%(message)s',
    level=logging.DEBUG
)
log = logging.getLogger(__name__)

app.include_router(api.router)


@app.get('/')
def root():
    log.info('Root test')
    return {'data': 'test'}


@app.get('/timestamp')
def get_timestamp():
    log.info('Timestamp test')
    return {'timestamp': datetime.now()}
