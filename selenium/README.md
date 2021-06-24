# To setup e2e testing environment

you'll have to run the tests/e2e directory from your localhost rather than docker exec into the container

1. (OPTIONAL if completed) create a virtual environment `python3 -m venv .`
2. activate the virtual environment `source bin/activate`
3. (OPTIONAL if completed) Install required dependencies `pip install selenium/requirements.txt`
4. (OPTIONAL if completed) you'll have to start your containers, e.g. web & postgres
5. (OPTIONAL if completed) set environment variables for testing. CANVAS_SSO_USERNAME, CANVAS_SSO_PASSWORD, CANVAS_BASE_URL
6. run the tests with bin/pytest <OPTIONS> tests/e2e