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
        self.hostname = urlparse(start_url).hostname 
        self.local_path = ""
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
        despaced_title = "".join(self.html.find("title").text.split()).replace("|", "") # write more universal regex expression
        title = clean(despaced_title, no_emoji=True, no_punct=True, 
                      no_currency_symbols=True, no_line_breaks=True)
        
        return title

    
    def get_interdom_links(self):
        # add support of relative links via regex 
        links = []
        for link in self.html.find_all("a", href=True):
            if(self.hostname in link["href"] 
            or link["href"].startswith("/") 
            or link["href"].startswith("./")
            or link["href"].startswith("../")): ## add support for links that go up the directory
                links.append(link)
        
        return links


    def get_abs_urls(self, links): # work around other protocols
        abs_links = []

        for link in links:
            if link["href"].startswith("http"):
                abs_links.append(link)
            else:
                abs_link = urljoin(self.url, link["href"])
                abs_links.append(abs_link)
        
        return abs_links

        
    def change_hrefs(self, link_paths: dict):
        with open(self.local_path, "r+", encoding="utf-8") as html_doc:
            html = BeautifulSoup(html_doc.read(), "html.parser")

            for link in html.find_all("a", href=True):
                abs_link = urljoin(self.url, link["href"])
                if abs_link in link_paths.keys():
                    
                    path = os.path.join("../../", link_paths[abs_link])  
                    link["href"] = path
            
            html_doc.seek(0)
            html_doc.write(str(html))
            html_doc.truncate()


    def set_depth(self, depth):
        self._depth = depth

    
    def download_html(self, *, level=None):
        title = self.get_title()
        folder_name = self.url.split('/')[-1] if self.url.split('/')[-1] != "" else self.url.split('/')[-2]
        dir = None

        if level != None:
            
            dir = os.path.join(os.curdir, f"level{level}/{folder_name}")
            if not os.path.exists(dir):
                os.makedirs(dir)
        else:
            dir = os.path.join(os.curdir, f"{folder_name}")
            if not os.path.exists(dir):
                os.makedirs(dir)
            

        with open(f"{dir}//{title}.html", "w", encoding="utf-8") as html_file:
            html_file.write(self.html.prettify())

        self.local_path = dir + "/" + self.get_title() + ".html"

        return self.local_path

        

    


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
        folder_name = self.html_obj.url.split('/')[-1] if self.html_obj.url.split('/')[-1] != "" else self.html_obj.url.split('/')[-2]

        dir = os.path.join(os.curdir, f"statics//{folder_name}")
        if not os.path.exists(dir):
            os.makedirs(dir)

        for i in range(len(self.css_links)):
            css_page = requests.get(self.css_links[i]["href"])
            with open(f".//statics//{folder_name}//{title + str(i)}.css", "w", encoding="utf-8") as css_file:
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
        folder_name = self.html_obj.url.split('/')[-1] if self.html_obj.url.split('/')[-1] != "" else self.html_obj.url.split('/')[-2]

        for i in range(len(self.css_links)):
            self.css_links[i]["href"] = "../../statics/" + f"{folder_name}/" + title + str(i) + ".css"


LOADED_PAGES = {}            
        

def download_subpages(html_obj: HTMLObject, depth: int) -> None:

    if depth == 0:
            return

    interdom_links = [link for link in html_obj.get_abs_urls(html_obj.get_interdom_links()) if type(link) == str]


    for link in interdom_links:
        if link not in LOADED_PAGES.keys():

            sub_page = HTMLObject(link)
            css_obj = CSSObject(sub_page)
            
            sub_page.set_depth(depth)

            css_obj.donwload_css()
            css_obj.change_css_paths()

            path = sub_page.download_html(level=depth)
            
            LOADED_PAGES.update({link:path})
            download_subpages(sub_page, depth-1)

    html_obj.change_hrefs(LOADED_PAGES)
    



url = "https://sourcemaking.com/refactoring/decompose-conditional"
html_obj = HTMLObject(url)
css_obj = CSSObject(html_obj)
css_obj.donwload_css()

css_obj.change_css_paths()

path = html_obj.download_html(level=0)


LOADED_PAGES.update({url:path})



download_subpages(html_obj, 1)
html_obj.change_hrefs(LOADED_PAGES)





