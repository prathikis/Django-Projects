from django.urls import path
from . import views
app_name = 'places'

urlpatterns = [
    path('', views.place_view, name='place_view'),
    path('get_place_hierarchy/', views.get_place_hierarchy, name='get_place_hierarchy'),
]
