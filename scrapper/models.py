from django.db import models

# Create your models here.


class Website(models.Model):

    domain = models.CharField(max_length=128, unique=True)


class Text(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    website = models.ForeignKey(Website, on_delete=models.DO_NOTHING, related_name="texts")
    content = models.TextField(max_length=10000, blank=False)
    generated_by = models.ForeignKey('ResourceGeneration', on_delete=models.DO_NOTHING, related_name='generated_texts', null=True)


class Image(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    website = models.ForeignKey(Website, on_delete=models.DO_NOTHING, related_name="images")
    image = models.ImageField()
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

    def start(self):
        return True

    def get_status_label(self):
        return ResourceGenerationStatusChoices.get_label_for_choice(self.status)