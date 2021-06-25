# To setup e2e testing environment

you'll have to run the tests/e2e directory from your localhost rather than docker exec into the container

1. (OPTIONAL if completed) create a virtual environment `python3 -m venv .`
2. if using windows, then create bin folder and move new files in scripts there 
3. activate the virtual environment `source bin/activate`
4. (OPTIONAL if completed) Install required dependencies `pip install -r selenium/requirements.txt`
5. (OPTIONAL if completed) you'll have to start your containers, e.g. web & postgres
6. (OPTIONAL if completed) set environment variables for testing. CANVAS_SSO_USERNAME, CANVAS_SSO_PASSWORD, CANVAS_BASE_URL
7. run the tests with bin/pytest <OPTIONS> tests/e2e