from datetime import timezone, datetime

from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from scrapper.models import Text, Image, ResourceGeneration
from scrapper.serializers import TextSerializer, ResourceGenerationCreateSerializer, ImageSerializer


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


class GenerateResourcesViewSet(ViewSet):


    @action(detail=False, methods=['POST'])
    def save_resources(self, request):
        serializer = ResourceGenerationCreateSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        result = obj.start()
        if result:
            obj.date_end = datetime.now()

        response_msg = "id: {}, status{}".format(
            obj.id,
            obj.get_status_label()
        )
        return Response({"started generation ": response_msg})