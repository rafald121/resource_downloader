import shutil
from urllib.error import URLError
from wsgiref.util import FileWrapper

from django.http import HttpResponse

# Create your views here.
from django.utils.datetime_safe import datetime
from rest_framework import mixins, renderers
from rest_framework.decorators import api_view, action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, GenericViewSet

from scrapper.models import Text, Image, ResourceGeneration, ResourceGenerationStatusChoices
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

    serializer_class = ResourceGenerationCreateSerializer

    def get_queryset(self):
        return ResourceGeneration.objects.all()

    @action(detail=False, methods=['POST'])
    def save_resources(self, request):
        serializer = ResourceGenerationCreateSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)

        resource_generator = serializer.save()

        try:
            resource_generator.save_resources()
        except (ValidationError, ValueError, URLError) as e:
            response_msg = f"Error occurred: {e}"
            resource_generator.status = ResourceGenerationStatusChoices.ERROR
        except Exception as e:
            response_msg = f"Unexpected error occurred: {e}"
            resource_generator.status = ResourceGenerationStatusChoices.ERROR
        else:
            resource_generator.status = ResourceGenerationStatusChoices.GENERATED
            response_msg = "Generated"

        resource_generator.date_end = datetime.now()
        resource_generator.save()

        response = {
            "message": response_msg,
            "id": f"{resource_generator.id}",
            "status": f"{resource_generator.get_status_label()}",
        }

        return Response(response)

    @action(
        detail=True,
        methods=['GET'],
        renderer_classes=(PassthroughRenderer, )
    )
    def download(self, *args, **kwargs):
        instance = self.get_object()
        if not instance.can_download():
            return HttpResponse({"message": f"Resources with id: {instance.pk} were not generated properly so you cannot download it, try again"})

        try:
            file_name = shutil.make_archive(
                instance.get_relative_file_zipped_path(),
                instance.FILE_FORMAT,
                instance.directory
            )
        except FileNotFoundError:
            return HttpResponse({"message": "Downloaded file's resources could not be found. Try to download it again"})

        with open(file_name, 'rb') as file:

            response = HttpResponse(FileWrapper(file), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="%s"' % instance.get_file_zipped_name()

            return response
