import os

from django.conf import settings
from django.db import models, transaction, IntegrityError

from scrapper import utils
from scrapper.choices import ResourceGenerationStatusChoices


class Text(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=False, max_length=1000)
    content = models.TextField(max_length=10000, blank=False)
    generated_by = models.ForeignKey('ResourceGeneration', on_delete=models.DO_NOTHING, related_name='generated_texts', null=True)


class Image(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=False, max_length=1000)
    file = models.FileField(unique=True, blank=True, null=True)
    generated_by = models.ForeignKey('ResourceGeneration', on_delete=models.DO_NOTHING, related_name='generated_images', null=True)


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
        super().save()  # to achieve self.id and then create proper directory
        if not self.directory:
            self.directory = self.create_and_get_directory_for_resources()
            super().save()

    def save_resources(self):
        self.save_texts()
        self.save_images()

    def can_download(self):
        return self.status == ResourceGenerationStatusChoices.GENERATED

    def get_status_label(self):
        return ResourceGenerationStatusChoices.get_label_for_choice(self.status)

    def get_directory_images(self):
        return self.directory + 'images/_'

    def get_file_zipped_name(self):
        return f'resources_{self.id}.zip'

    def get_relative_file_zipped_path(self):
        return settings.MEDIA_ROOT_RESOURCES_RELATIVE.format(self.id)

    def get_path_texts(self):
        return self.directory + 'texts'

    def save_texts(self):
        lines = utils.get_text_lines_for_url(self.url)
        text_cleaned = "\n".join(lines)

        utils.save_texts_file(text_cleaned, path=self.get_path_texts())
        self.save_texts_objects(lines)

    def create_and_get_directory_for_resources(self):

        resources_path = f"{settings.MEDIA_ROOT}resources/{self.id}/"

        if not os.path.exists(resources_path):
            os.mkdir(resources_path)
        return resources_path

    def save_images(self):

        images_sources = utils.get_image_sources(self.url)

        for url in images_sources:
            image_file = utils.get_remote_image(url)
            image_object = Image(url=url, generated_by=self)
            try:
                image_object.save()
            except IntegrityError as e:
                pass  # it was just saved before
            image_object.file.save(
                self.get_directory_images(),
                image_file,
            )
            image_object.save()

        return True

    def save_texts_objects(self, lines):
        texts = [
            Text(content=line, url=self.url, generated_by=self)
            for line in lines
        ]

        with transaction.atomic():
            result = Text.objects.bulk_create(texts)
            return result
