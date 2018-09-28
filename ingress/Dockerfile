FROM python:3.6-alpine

WORKDIR /app

RUN apk add --no-cache bash
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["bash", "entrypoint.sh"]