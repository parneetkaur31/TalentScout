from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('filter_candidates', views.feature1, name='feature1'),
    path('check_eligibility', views.feature2, name='feature2'),
]