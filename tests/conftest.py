
def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="chrome")
    parser.addoption("--headless", action="store_true", default=False)
    parser.addoption("--stayopen", action="store_true", default=False)
