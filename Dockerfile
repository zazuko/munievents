FROM python:3.9-slim

WORKDIR /app

# install dependencies
RUN pip install gunicorn==20.0.4 poetry==1.1
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install

# get source code
COPY munievents munievents

EXPOSE 8080

# run as "nobody"
USER 65534:65534

CMD ["python", \
     "-m", "gunicorn.app.wsgiapp", \
     "--bind=[::]:8080", \
     "--timeout=300", \
     "--access-logfile=-", \
     "munievents.main:server"]
