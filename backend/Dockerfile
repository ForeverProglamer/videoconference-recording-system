FROM python:3.11.2-alpine3.16

RUN apk update && apk add gcc python3-dev postgresql-dev musl-dev curl

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 - && \
    cd /usr/local/bin && \
    ln -s /etc/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /app

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

ARG INSTALL_DEV=false
RUN sh -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

COPY main.py main.py
COPY app/ app/

CMD ["uvicorn", "main:app", "--reload", "--proxy-headers", "--host", "0.0.0.0"]