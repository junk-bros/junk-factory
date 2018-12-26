from django.urls import path
from . import views

urlpatterns = [
    path('', views.OverViews().overview, name='overview'),
    path('quatile/', views.Quantile().quant, name='quatile'),
]
