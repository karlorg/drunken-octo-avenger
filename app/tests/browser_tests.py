from app.main import app, flash_bootstrap_category


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


def get_url(local_url='/'):
    # Obviously this is not the same application instance as the running
    # server and hence the LIVESERVER_PORT could in theory be different,
    # but for testing purposes we just make sure it this is correct.
    port = app.config['TESTSERVER_PORT']
    return 'http://localhost:{}/{}'.format(port, local_url)

# Note, we could write these additional assert methods in a class which
# inherits from webdriver.PhantomJS, however if we did that it would be more
# awkward to allow choosing a different web driver. Since we only have a couple
# of these I've opted for greater flexibility.
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

def wait_for_element_to_be_clickable(driver, selector):
    wait = WebDriverWait(driver, 5)
    element_spec = (By.CSS_SELECTOR, selector)
    condition = expected_conditions.element_to_be_clickable(element_spec)
    element = wait.until(condition)
    return element

def click_element_with_css(driver, selector):
    element = driver.find_element_by_css_selector(selector)
    element.click()

def fill_in_text_input_by_css(driver, input_css, input_text):
    input_element = driver.find_element_by_css_selector(input_css)
    input_element.send_keys(input_text)

def fill_in_and_submit_form(driver, fields, submit):
    for field_css, field_text in fields.items():
        fill_in_text_input_by_css(driver, field_css, field_text)
    click_element_with_css(driver, submit)

def check_flashed_message(driver, message, category):
    category = flash_bootstrap_category(category)
    selector = 'div.alert.alert-{0}'.format(category)
    elements = driver.find_elements_by_css_selector(selector)
    if category == 'error':
        print("error: messages:")
        for e in elements:
            print(e.text)
    assert any(message in e.text for e in elements)

def test_frontpage_loads(driver):
    """ Just make sure we can go to the front page and that
    the main menu is there and has at least one item."""
    driver.get(get_url('/'))
    main_menu_css = 'nav .container #navbar'
    assertCssSelectorExists(driver, main_menu_css)

def test_feedback(driver):
    """Tests the feedback mechanism."""
    driver.get(get_url())
    wait_for_element_to_be_clickable(driver, '#feedback-link')
    click_element_with_css(driver, '#feedback-link')
    wait_for_element_to_be_clickable(driver, '#feedback_submit_button')
    feedback = {'#feedback_email': "example_user@example.com",
                '#feedback_name': "Avid User",
                '#feedback_text': "I hope your feedback form works."}
    fill_in_and_submit_form(driver, feedback, '#feedback_submit_button')
    check_flashed_message(driver, "Thanks for your feedback!", 'info')
