from django.urls import path
from .views import upload_file
from .views import convert_file

urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('convert/', convert_file, name='convert_file'),
]
