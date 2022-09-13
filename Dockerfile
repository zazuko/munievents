FROM python:3.9-slim

WORKDIR /app

# install dependencies
COPY setup.py .
COPY munievents munievents
RUN pip install .
RUN pip install gunicorn==20.1.0 werkzeug==2.0.3 flask==2.1.3

EXPOSE 8080

# run as "nobody"
USER 65534:65534

CMD ["python", \
     "-m", "gunicorn.app.wsgiapp", \
     "--bind=[::]:8080", \
     "--timeout=300", \
     "--access-logfile=-", \
     "munievents.main:server"]
