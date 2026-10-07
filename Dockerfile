FROM python:3.11-slim

ARG R8DIUM_UID=1000
ARG R8DIUM_GID=1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    R8DIUM_CONFIG_FILE=/config/r8dium.cfg \
    R8DIUM_BOT_TOKEN_FILE=/run/secrets/r8dium_bot_token \
    RUN8_CONTROL_SOCKET=/run8-control/control.sock

RUN groupadd --gid "${R8DIUM_GID}" r8dium \
    && useradd --create-home --uid "${R8DIUM_UID}" --gid "${R8DIUM_GID}" --shell /usr/sbin/nologin r8dium \
    && mkdir -p /app /config /run8 /run8-control /state \
    && chown -R r8dium:r8dium /config /run8 /run8-control /state

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY *.py /app/
RUN ln -s /app/run8ControlClient.py /usr/local/bin/run8-control \
    && chmod 0755 /app/run8ControlClient.py

USER r8dium
WORKDIR /state

CMD ["python", "/app/r8dium.py"]
