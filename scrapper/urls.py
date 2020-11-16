from django.urls import path
from rest_framework import routers

from scrapper import views


router = routers.SimpleRouter()
router.register(r'texts', views.TextResourcesViewSet, basename='texts')
router.register(r'images', views.ImageResourcesViewSet, basename='images')
router.register(r'generate', views.GenerateResourcesViewSet, basename='images')

urlpatterns = router.urls