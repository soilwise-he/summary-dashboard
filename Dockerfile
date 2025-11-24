FROM apache/superset:latest

USER root

# Install authlib and flask-session into Superset's venv site-packages using system pip
RUN apt-get update && \
    apt-get install -y python3-pip && \
    /usr/bin/python3 -m pip install --target=/app/.venv/lib/python3.10/site-packages authlib flask-session

USER superset