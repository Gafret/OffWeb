import requests
import re
import sys
import Lib.queue
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from cleantext import clean



URL = "https://kworkuw.github.io/task2/index.html"
DOMAIN = urlparse(URL).netloc
    
    

def get_html(url):
    webpage = requests.get(url)
    if(webpage.status_code != requests.codes.ok):
        raise ConnectionError("Bad response")

    html_page = BeautifulSoup(webpage.content, "html.parser")

    return html_page


def strip_html(html):

    for script in html.select("script"):
        script.extract()
    
    for link in html.find_all("link", rel=True):
        if link["rel"][0] != "stylesheet":
            link.extract()
    
    return html


def get_interdom_links(html, domain):
    links = []

    for link in html.find_all("a", href=True):
        
        if domain in link.attrs["href"] or "./" in link.attrs["href"]:
            links.append(link)
    
    return links          


def get_css_links(html, url):
    links = []

    for link in html.select("link"):
        link = urljoin(url, link.attrs.get("href"))
        links.append(link)
    
    return links


def change_css_paths(html: BeautifulSoup):
    title = clean("".join(html.find("title").text.split()), lower=True, no_punct=True, no_currency_symbols=True, no_line_breaks=True, no_emoji=True)
    css_links = html.find_all("link")

    for i in range(len(css_links)):
        css_links[i].attrs["href"] = "../css/" + title + str(i) + ".css"


def download_html(html):
    name = clean("".join(html.find("title").text.split()), lower=True, no_punct=True, no_currency_symbols=True, no_line_breaks=True, no_emoji=True)

    with open(f"{name}.html", "w", encoding="utf-8") as file:
        file.write(html.prettify())
        

def download_css(links):
    title = clean("".join(html.find("title").text.split()), lower=True, no_punct=True, no_currency_symbols=True, no_line_breaks=True, no_emoji=True)

    for i in range(len(links)):
        css_page = requests.get(links[i])
        with open(f"{title + str(i)}.css", "wb") as file:
            file.write(css_page.content)


