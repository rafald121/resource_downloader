from urllib.error import URLError

import requests
from bs4 import BeautifulSoup
from django.core.files import File
from requests import RequestException
from rest_framework.exceptions import ValidationError
import urllib.request


def get_text_lines_for_url(url):
    try:
        html = requests.get(url).text
    except RequestException:
        raise ValidationError(detail="Invalid URL provided")

    soup = BeautifulSoup(html, features="html.parser")

    for script in soup(["script", "style"]):
        script.extract()  # rip it out

    html_text = soup.get_text()

    return [
        line.strip()
        for line in html_text.splitlines()
        if line
    ]


def get_image_sources(url):
    try:
        html = requests.get(url).text
    except RequestException:
        raise ValidationError(detail="Invalid URL provided")

    soup = BeautifulSoup(html, features="html.parser")

    images = soup.findAll('img')
    return [image.attrs['src'] for image in images]


def get_remote_image(image_url):
    image_url = image_url.strip()
    if image_url.startswith('https'):
        image_url_replaced = image_url.replace('https', 'http')
    elif image_url.startswith("//"):
        image_url_replaced = ''.join(
            ["http:", image_url]
        )
    else:
        image_url_replaced = image_url

    try:
        result = urllib.request.urlretrieve(image_url_replaced)  # image_ur
    except ValueError as e:
        raise
    except URLError as e:
        raise
    else:
        return File(open(result[0], 'rb'))


def save_texts_file(file_text_content, path):
    text_file = open(path, "w+")
    text_file.write(file_text_content)
    text_file.close()
