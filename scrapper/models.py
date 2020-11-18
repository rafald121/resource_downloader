import os
from io import BytesIO
from urllib.error import URLError

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models, transaction, IntegrityError

import requests
from bs4 import BeautifulSoup

# Create your models here.
from requests import RequestException
from rest_framework.exceptions import ParseError, ValidationError
import urllib.request
from django.core.files import File


class Website(models.Model):

    domain = models.CharField(max_length=128, unique=True)


class Text(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=False, max_length=1000)
    # website = models.ForeignKey(Website, on_delete=models.DO_NOTHING, related_name="texts")
    content = models.TextField(max_length=10000, blank=False)
    generated_by = models.ForeignKey('ResourceGeneration', on_delete=models.DO_NOTHING, related_name='generated_texts', null=True)


class Image(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=False, max_length=1000)
    # website = models.ForeignKey(Website, on_delete=models.DO_NOTHING, related_name="images")
    file = models.FileField(unique=True, blank=True, null=True)

    generated_by = models.ForeignKey('ResourceGeneration', on_delete=models.DO_NOTHING, related_name='generated_images', null=True)

class ResourceGenerationStatusChoices():

    STARTED_GENERATION = 0
    STARTED_GENERATION_LABEL = 'Started generation'
    GENERATED = 1
    GENERATED_LABEL = 'Generated'
    ERROR = 10
    ERROR_LABEL = 'Error'

    choices = (
        (STARTED_GENERATION, STARTED_GENERATION_LABEL),
        (GENERATED, GENERATED_LABEL),
        (ERROR, ERROR_LABEL),
    )

    @classmethod
    def get_label_for_choice(cls, choice):
        return cls.get_choices_dict()[choice]

    @classmethod
    def get_choices_dict(cls):
        return {
            val[0]: val[1] for val in cls.choices
        }


class ResourceGeneration(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    date_started = models.DateTimeField(auto_now=True)
    date_end = models.DateTimeField(null=True, blank=True)
    status = models.PositiveSmallIntegerField(
        choices=ResourceGenerationStatusChoices.choices,
        default=ResourceGenerationStatusChoices.STARTED_GENERATION
    )
    url = models.CharField(blank=False, max_length=1000)
    directory = models.FilePathField(null=True, blank=True)

    FILE_FORMAT = 'zip'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        self.directory = self.create_and_get_directory_for_resources()
        super().save()

    def start(self):
        self.save_texts()
        self.save_images()
        return True

    def get_status_label(self):
        return ResourceGenerationStatusChoices.get_label_for_choice(self.status)

    def get_directory_images(self, write=False):
        if write:
            return self.directory + 'images/_'
        return self.directory + 'images/'

    def get_file_zipped_name(self):
        return f'resources_{self.id}.zip'

    def get_relative_file_zipped_path(self):
        return settings.MEDIA_ROOT_RESOURCES_RELATIVE.format(self.id)

    def get_path_texts(self):
        return self.directory + 'texts'

    def save_texts(self):
        try:
            html = requests.get(self.url).text
        except RequestException:
            raise ValidationError(detail="Invalid URL provided")

        soup = BeautifulSoup(html, features="html.parser")

        for script in soup(["script", "style"]):
            script.extract()  # rip it out

        html_text = soup.get_text()

        lines = [
            line.strip()
            for line in html_text.splitlines()
            if line
        ]
        text_cleaned = "\n".join(lines)

        self.save_file(text_cleaned)
        self.save_file_objects(lines)

    def save_file(self, file_text_content):
        text_file = open(self.get_path_texts(), "w+")
        text_file.write(file_text_content)
        text_file.close()

    def save_images(self):
        try:
            html = requests.get(self.url).text
        except RequestException:
            raise ValidationError(detail="Invalid URL provided")

        soup = BeautifulSoup(html, features="html.parser")

        images = soup.findAll('img')
        images_sources = [image.attrs['src'] for image in images]

        for url in images_sources:
            image_file = self.get_remote_image(url)
            image_object = Image(url=url, generated_by=self)
            try:
                image_object.save()
            except IntegrityError as e:
                pass
            image_object.file.save(
                self.get_directory_images(write=True),
                image_file,
            )
            image_object.save()

        return True

    def get_remote_image(self, image_url):
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
            pass
        except URLError as e:
            pass
        else:
            return File(open(result[0], 'rb'))

    def create_and_get_directory_for_resources(self):

        resources_path = "".join(
            [settings.MEDIA_ROOT, 'resources/{}/'.format(self.id)]
        )

        if not os.path.exists(resources_path):
            os.mkdir(resources_path)

        return resources_path

    def save_file_objects(self, lines):
        texts = [
            Text(content=line, url=self.url, generated_by=self)
            for line in lines
        ]

        with transaction.atomic():
            result = Text.objects.bulk_create(texts)
            return result
