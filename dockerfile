FROM python:3.11

WORKDIR /app

ENV FLASK_APP=api8inf349
ENV FLASK_DEBUG=TRUE
ENV PYTHONBUFFERED=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ..

EXPOSE 5000

CMD flask init-db && flask run
