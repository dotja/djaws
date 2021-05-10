FROM python:3.8.5-alpine

RUN pip install --upgrade pip

COPY ./requirements.txt .

RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

COPY ./myproject /myproject

COPY ./entrypoint.sh /myproject

WORKDIR /myproject

ENTRYPOINT ["sh", "./entrypoint.sh"]
