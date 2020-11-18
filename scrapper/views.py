import os
import shutil
import zipfile
from datetime import timezone, datetime
from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework import mixins, renderers
from rest_framework.decorators import api_view, action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, GenericViewSet

from scrapper.models import Text, Image, ResourceGeneration, Website
from scrapper.serializers import TextSerializer, ResourceGenerationCreateSerializer, ImageSerializer


class PassthroughRenderer(renderers.BaseRenderer):
    """
        Return data as-is. View should supply a Response.
    """
    media_type = ''
    format = ''
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


@api_view(http_method_names=['GET'])
def hello_world(request):
    return Response({"message": "Hello, world!"})


class TextResourcesViewSet(ViewSet):

    def get_queryset(self):
        return Text.objects.all()

    def list(self, request):
        serializer = TextSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)


class ImageResourcesViewSet(ViewSet):

    def get_queryset(self):
        return Image.objects.all()

    def list(self, request):
        serializer = ImageSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)


class GenerateResourcesViewSet(GenericViewSet, mixins.RetrieveModelMixin):

    def get_queryset(self):
        return ResourceGeneration.objects.all()

    @action(detail=False, methods=['POST'])
    def save_resources(self, request):
        serializer = ResourceGenerationCreateSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        result = obj.start()
        if result:
            obj.date_end = datetime.now()

        response_msg = f"Resources dispatched to be generated. Id: {obj.id}, Status: {obj.get_status_label()}"

        return Response({"Result": response_msg})

    @action(methods=['get'], detail=True, renderer_classes=(PassthroughRenderer,))
    def download(self, *args, **kwargs):
        instance = self.get_object()

        file_name = shutil.make_archive(
            instance.get_relative_file_zipped_path(),
            instance.FILE_FORMAT,
            instance.directory
        )
        file = open(file_name, 'rb')
        response = HttpResponse(FileWrapper(file), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="%s"' % instance.get_file_zipped_name()
        return response
