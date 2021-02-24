# from https://github.com/ucfopen/lti-template-flask
# default flask port is 5000, or set in SERVER_NAME config variable
FROM python:3.8.7
COPY . /app
WORKDIR /app

# Make /app/* available to be imported by Python globally to better support several use cases like Alembic migrations.
ENV PYTHONPATH=/app

RUN pip3 install -r requirements.txt && \
    pip3 install git+https://github.com/ucfcdl/pylti.git@roles#egg=PyLTI \
                 pytest \
                 selenium \
                 psutil

ENV FLASK_APP=nbgrader_to_canvas

RUN pip install -e .
CMD while true; do flask run --host 0.0.0.0; sleep 5; done