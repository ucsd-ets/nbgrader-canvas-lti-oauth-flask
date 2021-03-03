# from https://github.com/ucfopen/lti-template-flask
# default flask port is 5000, or set in SERVER_NAME config variable
FROM python:3.8.7

COPY . /app
WORKDIR /app

# create the user that the container runs as
RUN groupadd -g 1018 -r nbgrader2canvas && useradd --no-log-init -u 1018 -m -r -g nbgrader2canvas nbgrader2canvas

ENV PYTHONPATH=/app
ENV FLASK_APP=nbgrader_to_canvas

RUN apt-get update && \
    apt-get install -y lsb-release \
                       sqlite3

# https://www.postgresql.org/download/linux/debian/
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && apt-get install -y postgresql

RUN pip install -r requirements.txt && \
    pip install -e .

# used for creating development environment. /mnt/nbgrader will need to be overridden at runtime for production
# TODO find cleaner solution
COPY scripts/init-flask.sh /
COPY scripts/start-flask.sh /
COPY mocks /tmp/nbgrader
RUN chmod +x /*.sh && \
    /init-flask.sh

USER nbgrader2canvas

CMD /start-flask.sh
