from django.urls import path
from . import views

app_name = 'irisApp'

urlpatterns = [
    path('', views.predictor, name = 'predictor'),
]