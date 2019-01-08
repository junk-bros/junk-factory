from django.urls import path
from . import views

urlpatterns = [
    path('', views.FileOperate().index, name='index'),
    path('upload/', views.FileOperate().upload, name='upload'),
    path('download/', views.FileOperate().download, name='download'),
    path('delete/', views.FileOperate().delete, name='delete'),
    path('getfiles/', views.FileOperate().files_overview, name='getfiles')
]
