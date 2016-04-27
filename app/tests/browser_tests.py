from app.main import app


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pytest
# Currently just used for the temporary hack to quit the phantomjs process
# see below in quit_driver.
import signal


@pytest.fixture(scope="module")
def driver(request):
    driver = webdriver.PhantomJS()
    driver.set_window_size(1120, 550)
    def finalise():
        driver.close()
        # A bit of hack this but currently there is some bug I believe in
        # the phantomjs code rather than selenium, but in any case it means that
        # the phantomjs process is not being killed so we do so explicitly here
        # for the time being. Obviously we can remove this when that bug is
        # fixed. See: https://github.com/SeleniumHQ/selenium/issues/767
        driver.service.process.send_signal(signal.SIGTERM)
        driver.quit()
    request.addfinalizer(finalise)
    return driver


def get_url(local_url):
    # Obviously this is not the same application instance as the running
    # server and hence the LIVESERVER_PORT could in theory be different,
    # but for testing purposes we just make sure it this is correct.
    port = app.config['LIVESERVER_PORT']
    url = 'http://localhost:{0}'.format(port)
    return "/".join([url, local_url])

def assertCssSelectorExists(driver, css_selector):
    """ Asserts that there is an element that matches the given
    css selector."""
    # We do not actually need to do anything special here, if the
    # element does not exist we fill fail with a NoSuchElementException
    # however we wrap this up in a pytest.fail because the error message
    # is then a bit nicer to read.
    try:
        driver.find_element_by_css_selector(css_selector)
    except NoSuchElementException:
        pytest.fail("Element {0} not found!".format(css_selector))


def assertCssSelectorNotExists(driver, css_selector):
    """ Asserts that no element that matches the given css selector
    is present."""
    with pytest.raises(NoSuchElementException):
        driver.find_element_by_css_selector(css_selector)


def test_frontpage_loads(driver):
    """ Just make sure we can go to the front page and that
    the main menu is there and has at least one item."""
    driver.get(get_url('/'))
    main_menu_css = 'nav .container #navbar'
    assertCssSelectorExists(driver, main_menu_css)

