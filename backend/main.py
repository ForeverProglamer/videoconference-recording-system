import logging

from fastapi import FastAPI

from app.routers import api, pages

app = FastAPI(title='Backend')

logging.basicConfig(
    format='[%(asctime)s]:%(levelname)s:%(name)s:%(module)s:%(message)s',
    level=logging.DEBUG
)

app.include_router(api.router)
app.include_router(pages.router)
