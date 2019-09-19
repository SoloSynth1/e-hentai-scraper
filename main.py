import argparse
import os
import json
import re

import unicodedata

from requests_html import HTMLSession

class DownloadManager:

    def __init__(self):
        self.session = HTMLSession()
        self.__load_cookie()
        self.download_path = ""

    def __load_cookie(self):
        with open("cookie.json", 'r') as f:
            self.headers = json.load(f)

    def get_image_links(self, url):
        response = self.session.get(url, headers=self.headers)
        title_elements = response.html.find('h1')
        link_elements = response.html.find('a')
        image_set_name = get_image_set_name(title_elements)
        assert image_set_name
        image_links = filter_links(link_elements, 'href', '/s/')
        page_links = filter_links(link_elements, 'href', '?p=')
        if page_links:
            for link in page_links:
                response = self.session.get(link, headers=self.headers)
                link_elements = response.html.find('a')
                image_links += filter_links(link_elements, 'href', '/s/')
        return image_links, image_set_name

    def create_image_dir(self, dir_name):
        dir_name = slugify(dir_name)
        full_dir_path = os.path.join(download_dir, dir_name)
        if dir_name not in os.listdir(download_dir) and not os.path.isdir(full_dir_path):
            os.mkdir(full_dir_path)
        self.download_path = full_dir_path
        assert self.download_path

    def download_image(self, image_link):
        response = self.session.get(image_link, headers=self.headers)
        full_img_links = filter_links(response.html.find('a'), 'href', 'fullimg')
        if full_img_links:
            for full_img_link in full_img_links:
                self.write_image_to_file(full_img_link)
        else:
            lowres_img_links = filter_links(response.html.find('img'), 'src', '/h/')
            for lowres_img_link in lowres_img_links:
                self.write_image_to_file(lowres_img_link)

    def write_image_to_file(self, img_link):
        print(img_link)
        response = self.session.get(img_link, headers=self.headers)
        print(response)
        print(response.status_code)
        print(response.headers)
        if is_valid_image_response(response):
            image = response.content
            if 'Content-Disposition' in response.headers:
                filename = response.headers['Content-Disposition'].split('filename=')[-1]
            else:
                filename = img_link.split('/')[-1]
            with open(os.path.join(self.download_path, filename), 'wb') as f:
                f.write(image)
                print("{} written".format(filename))
        else:
            print("failed to download file. quota is likely to be exceeded.")

def filter_links(link_elements, attr_keys, substring):
    return [link_element.attrs[attr_keys] for link_element in link_elements if attr_keys in link_element.attrs and substring in link_element.attrs[attr_keys]]

def get_image_set_name(title_elements):
    image_set_name = [element.text for element in title_elements if 'id' in element.attrs and element.attrs['id'] == 'gj'][0]
    if not image_set_name:
        image_set_name = [element.text for element in title_elements if 'id' in element.attrs and element.attrs['id'] == 'gn'][0]
    return image_set_name

def is_valid_image_response(response):
    if response.status_code < 400 and 'Content-Type' in response.headers and 'image' in response.headers['Content-Type']:
        return True
    else:
        return False

def is_a_valid_start_url(url):
    if "https://e-hentai.org/g/" in url:
        return True
    else:
        return False

def slugify(value):
    # From django text utils
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    value = unicodedata.normalize('NFKC', value)
    value = re.sub(r'[^\(\)\[\]\w\s-]', '', value).strip().lower()
    # return re.sub(r'[-\s]+', '-', value)
    return value

download_dir = "./downloads"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='e-hentai gallery scraper')
    parser.add_argument('url', help='URL to e-hentai gallery')
    args = parser.parse_args()
    assert is_a_valid_start_url(args.url)

    manager = DownloadManager()

    image_links, image_set_name = manager.get_image_links(args.url)
    manager.create_image_dir(image_set_name)

    for image_link in image_links:
        manager.download_image(image_link)



