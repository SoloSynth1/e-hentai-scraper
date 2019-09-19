import argparse
import os
import json
import hashlib

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
        image_set_names = get_image_set_names(title_elements)
        assert image_set_names
        image_links = filter_links(link_elements, 'href', '/s/')
        page_links = filter_links(link_elements, 'href', '?p=')
        if page_links:
            for link in page_links:
                response = self.session.get(link, headers=self.headers)
                link_elements = response.html.find('a')
                image_links += filter_links(link_elements, 'href', '/s/')
        return image_links, image_set_names

    def create_image_dir(self, image_set_names):
        dir_name = hash(image_set_names['gn'])
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

    def write_metadata(self, image_set_names, image_links):
        assert self.download_path
        meta = {
            "title_en": image_set_names['gn'],
            "title_jp": image_set_names['gj'],
            "img_count": len(image_links)
        }
        with open(os.path.join(self.download_path, "meta.json"), 'w') as f:
            f.write(json.dumps(meta))

def filter_links(link_elements, attr_keys, substring):
    return [link_element.attrs[attr_keys] for link_element in link_elements if attr_keys in link_element.attrs and substring in link_element.attrs[attr_keys]]


def get_image_set_names(title_elements):
    image_set_name_gj = [element.text for element in title_elements if 'id' in element.attrs and element.attrs['id'] == 'gj'][0]
    image_set_name_gn = [element.text for element in title_elements if 'id' in element.attrs and element.attrs['id'] == 'gn'][0]
    image_set_names = {
        'gj': image_set_name_gj,
        'gn': image_set_name_gn
    }
    return image_set_names


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


def hash(string):
    hash = hashlib.sha1(string.encode('utf-8')).hexdigest()
    return hash


download_dir = "./downloads"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='e-hentai gallery scraper')
    parser.add_argument('url', help='URL to e-hentai gallery')
    args = parser.parse_args()
    assert is_a_valid_start_url(args.url)

    manager = DownloadManager()

    image_links, image_set_names = manager.get_image_links(args.url)
    manager.create_image_dir(image_set_names)
    manager.write_metadata(image_set_names, image_links)

    for image_link in image_links:
        manager.download_image(image_link)



