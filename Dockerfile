FROM python:3.9-slim AS build-env

RUN pip install gunicorn==20.0.4

ADD . /app
WORKDIR /app
RUN python setup.py install

FROM python:3.9-slim

# Copy the installed packages from the build environment
COPY --from=build-env /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

CMD ["python", \
     "-m", "gunicorn.app.wsgiapp", \
     "--bind=[::]:8080", \
     "--timeout=300", \
     "--access-logfile=-", \
     "munievents.main:server"]

EXPOSE 8080

# Run as "nobody"
USER 65534:65534
