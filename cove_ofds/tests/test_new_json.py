import os

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from libcoveweb2.tests.lib_functional import browser, server_url  # noqa


@pytest.mark.parametrize(
    ("json_data"),
    [
        ("{}",),
    ],
)
def test_new_json(server_url, browser, json_data):  # noqa
    browser.get(os.path.join(server_url, "new_json"))
    browser.find_element_by_id("id_paste").send_keys(json_data)
    browser.find_element_by_css_selector("#collapseTwo form").submit()

    # This simply waits until we end up on the data page. If we get there, the test passed.
    # If we didn't, it will timeout after 30 seconds and error.
    WebDriverWait(browser, 30).until(
        EC.presence_of_element_located((By.ID, "download-panel"))
    )
