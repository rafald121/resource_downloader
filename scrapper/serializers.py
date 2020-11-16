from rest_framework import serializers

from scrapper.models import Text, Website, ResourceGeneration


class WebsiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Website
        fields = ['id', 'domain']


class TextSerializer(serializers.ModelSerializer):

    website = WebsiteSerializer()

    class Meta:
        model = Text
        fields = ['id', 'created', 'website', 'content']


class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Text
        fields = ['id', 'created', 'website', 'image']


class ResourceGenerationCreateSerializer(serializers.ModelSerializer):

    # status = serializers.CharField(source='get_status_label')
    # website = serializers.CharField(source='website.domain')

    class Meta:
        model = ResourceGeneration
        fields = ['url', ]
        # read_only_fields = ['created', 'date_start', 'date_end', 'status', ]
