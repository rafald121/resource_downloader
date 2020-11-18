from rest_framework import serializers

from scrapper.models import Text, ResourceGeneration, Image


class TextSerializer(serializers.ModelSerializer):

    class Meta:
        model = Text
        fields = ['id', 'created', 'url', 'content']


class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = ['id', 'created', 'url', 'file']


class ResourceGenerationCreateSerializer(serializers.ModelSerializer):

    status = serializers.SerializerMethodField()

    class Meta:
        model = ResourceGeneration
        fields = ['url', 'status']

    def get_status(self, instance):
        return instance.get_status_label()

