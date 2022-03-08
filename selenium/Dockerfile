FROM python:3.8.7

# create the user that the container runs as
RUN groupadd -g 1018 -r nbgrader2canvas && useradd --no-log-init -u 1018 -m -r -g nbgrader2canvas nbgrader2canvas

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .
ENV PYTHONPATH=/app

RUN apt-get update && \
    apt-get install -y lsb-release

RUN pip install -r requirements.txt 

USER nbgrader2canvas
