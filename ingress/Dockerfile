FROM python:3.6-alpine

WORKDIR /app

COPY requirements.txt /app
RUN apk add --no-cache bash
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /app
COPY ingress.py /app

CMD ["bash", "entrypoint.sh"]