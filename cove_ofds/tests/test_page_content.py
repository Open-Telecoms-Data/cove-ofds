import pytest

from libcoveweb2.tests.lib_functional import browser, server_url  # noqa


@pytest.mark.parametrize(
    ("link_text", "url"),
    [
        (
            "Open Fibre Data Standard Documentation",
            "https://open-fibre-data-standard.readthedocs.io/en/latest/",
        ),
    ],
)
def test_footer_ofds(server_url, browser, link_text, url):  # noqa
    browser.get(server_url)
    footer = browser.find_element_by_id("footer")
    link = footer.find_element_by_link_text(link_text)
    href = link.get_attribute("href")
    assert href == url
