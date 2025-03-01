import logging
import shutil
import sys

from api.client import ApiClient
from ui.fixtures import *


def pytest_addoption(parser):
    parser.addoption('--url', default='https://education.mail.ru/')
    parser.addoption('--selenoid', action='store_true')
    parser.addoption('--vnc', action='store_true')
    parser.addoption('--browser', default='chrome')
    parser.addoption('--debug_log', action='store_true')


@pytest.fixture(scope='session')
def credentials():
    with open('/tmp/user', 'r') as f:
        user = f.readline().strip()
        password = f.readline().strip()

    return user, password


@pytest.fixture(scope='session')
def second_credentials():
    with open('/tmp/user2', 'r') as f:
        user = f.readline().strip()
        password = f.readline().strip()

    return user, password


@pytest.fixture(scope='function')
def api_client(config):
    return ApiClient(config['url'])


@pytest.fixture(scope='function')
def second_user(config, second_credentials):
    second_api_client = ApiClient(config['url'])
    second_api_client.post_login(*second_credentials)
    return second_api_client


@pytest.fixture(scope='session')
def config(request):
    url = request.config.getoption('--url')
    if request.config.getoption('--selenoid'):
        selenoid = 'http://127.0.0.1:4444'
        if request.config.getoption('--vnc'):
            vnc = True
        else:
            vnc = False
    else:
        selenoid = None
        vnc = False

    browser = request.config.getoption('--browser')
    debug_log = request.config.getoption('--debug_log')
    return {'url': url, 'browser': browser, 'debug_log': debug_log, 'selenoid': selenoid, 'vnc': vnc}


@pytest.fixture(scope='session')
def repo_root():
    return os.path.abspath(os.path.join(__file__, os.pardir))


def pytest_configure(config):
    if sys.platform.startswith('win'):
        base_test_dir = 'C:\\tests'
    else:
        base_test_dir = '/tmp/tests'

    if not hasattr(config, 'workerinput'):  # execute only once on main worker
        if os.path.exists(base_test_dir):
            shutil.rmtree(base_test_dir)
        os.makedirs(base_test_dir)

    # save to config for all workers
    config.base_test_dir = base_test_dir


@pytest.fixture(scope='function')
def test_dir(request):
    test_name = request._pyfuncitem.nodeid.replace('/', '_').replace(':', '_')
    test_dir = os.path.join(request.config.base_test_dir, test_name)
    os.makedirs(test_dir)
    return test_dir


@pytest.fixture(scope='function', autouse=True)
def logger(test_dir, config):
    log_formatter = logging.Formatter('%(asctime)s - %(filename)-15s - %(levelname)-6s - %(message)s')
    log_file = os.path.join(test_dir, 'test.log')

    log_level = logging.DEBUG if config['debug_log'] else logging.INFO

    file_handler = logging.FileHandler(log_file, 'w')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)

    log = logging.getLogger('test')
    log.propagate = False
    log.setLevel(log_level)
    log.handlers.clear()
    log.addHandler(file_handler)

    yield log

    for handler in log.handlers:
        handler.close()

    with open(log_file, 'r') as f:
        allure.attach(f.read(), 'test.log', attachment_type=allure.attachment_type.TEXT)
