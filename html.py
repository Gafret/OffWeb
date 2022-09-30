import requests
from urllib.parse import urljoin, urlparse
import json
import os
import time

from bs4 import BeautifulSoup
from cleantext import clean
from PIL import Image


#get around javascript built sites



class HTMLObject:
    
    def __init__(self, start_url) -> None:
        self.url = start_url
        self.html = self.get_document()
        self.domain = urlparse(start_url).netloc
        self._depth = 0


    def _get_html(self):
        response = requests.get(self.url)
        if response.status_code != 200:
            raise ConnectionError("Invalid response")
        
        html_page = BeautifulSoup(response.text, "html.parser")

        return html_page
    

    def _strip_html(self, html):

        for script in html.find_all("script"):
            script.extract()
        
        for link in html.find_all("link", rel=True):
            if link["rel"][0] != "stylesheet":
                link.extract()

        return html

    
    def get_document(self):
        html_page = self._get_html()
        stripped_html = self._strip_html(html_page)

        return stripped_html

    
    def get_title(self):
        despaced_title = "".join(self.html.find("title").text.split()).replace("|", "")
        title = clean(despaced_title, no_emoji=True, no_punct=True, 
                      no_currency_symbols=True, no_line_breaks=True)
        
        return title

    
    def get_interdom_links(self):
        # add support of relative links via regex 
        # save ABSOLUTE links
        links = []
        for link in self.html.find_all("a", href=True):
            if self.domain in link["href"] or link["href"].startswith("/") or link["href"].startswith("./"):
                links.append(link)
        
        return links

    def set_depth(self, depth):
        self._depth = depth

    
    # def load_sublinks(self):
    #     sub_links = self.get_interdom_links()

    #     dir = os.path.join(os.curdir, f"level{self.depth}")
    #     if not os.path.exists(dir):
    #         os.makedirs(dir)
    #     os.chdir(dir)

    #     for link in sub_links:
    #         if link["href"] not in loaded:
    #             html_obj = HTMLObject(urljoin(self.url, link["href"]))
    #             css_obj = CSSObject(html_obj)

    #             html_obj.set_depth(self.depth + 1)
                

                
    #             sub_dir = self.create_subdir(link)
    #             self._change_href(link)
    #             os.chdir(sub_dir)    

    #             html_obj.download_html()
    #             css_obj.donwload_css()
    #             css_obj.change_css_paths()
    #             time.sleep(1)
    #             print(os.getcwd())
    #             os.chdir("../")
    #             print(os.getcwd())
    #             time.sleep(1)


    def _change_href(self, link):
        link["href"] = f".//level{self.depth}//{link['href'].split('/')[-1]}"


    def create_subdir(self, link):
        dir = os.path.join(os.curdir, f"{link['href'].split('/')[-1]}")
        if not os.path.exists(dir):
            os.makedirs(dir)
        
        return dir


    
    def download_html(self):
        title = self.get_title()

        dir = os.path.join(os.curdir, f"{self.url.split('/')[-1]}")
        if not os.path.exists(dir):
            os.makedirs(dir)
        
        os.chdir(dir)

        with open(f"{title}.html", "w", encoding="utf-8") as html_file:
            html_file.write(self.html.prettify())

        




class CSSObject:

    def __init__(self, html_obj) -> None:
        self.html_obj = html_obj
        self.url = html_obj.url
        self.css_links = self._get_css_links()

    
    def _get_css_links(self):
        links = []

        for link in self.html_obj.html.find_all("link", rel=True):
            if "https" not in link["href"]:
                link["href"] = urljoin(self.url, link["href"])
                links.append(link)
            else:
                links.append(link)
            
        return links
            
    
    def donwload_css(self):
        title = self.html_obj.get_title()

        for i in range(len(self.css_links)):
            css_page = requests.get(self.css_links[i]["href"])
            with open(f"{title + str(i)}.css", "w") as css_file:
                css_file.write(css_page.text)
            
    
    def download_images(self):
        images = self.html_obj.html.find_all("img")
        title = self.html_obj.get_title()

        for i in range(len(images)):
            img_url = images[i]["src"]
            img = Image.open(requests.get(img_url, stream=True).raw)
            img.save(f"{title + str(i)}.jpg")
        

    def change_css_paths(self):
        title = self.html_obj.get_title()

        for i in range(len(self.css_links)):
            self.css_links[i]["href"] = "./" + title + str(i) + ".css"


LOADED_PAGES = []

def get_abs_urls(base_url, links):
    abs_links = []

    for link in links:
        if link["href"].startswith("http"):
            abs_links.append(link)
        else:
            abs_link = urljoin(base_url, link["href"])
            abs_links.append(abs_link)
    
    return abs_links

def create_subdir(depth):
    dir = os.path.join(os.curdir, f"level{depth}")
    if not os.path.exists(dir):
        os.makedirs(dir)
    
    return dir
    
    

def download_subpages(html_obj: HTMLObject, depth: int) -> None:
    interdom_links = get_abs_urls(html_obj.url, html_obj.get_interdom_links())
    path = create_subdir(1)
    os.chdir(path)

    for link in interdom_links:
        if link not in LOADED_PAGES:
            print(os.getcwd())
            sub_page = HTMLObject(link)
            sub_page.set_depth(1)
            
            
            sub_page.download_html()
            os.chdir("../")
            #download_subpages(sub_page, depth-1)
            #download_subpages(link, depth-1)
        time.sleep(2)
    
    if depth == -1:
        return 




url = "https://peps.python.org/pep-0008"
html_obj = HTMLObject(url)
html_obj.download_html()
download_subpages(html_obj, 1)




