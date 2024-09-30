from django.urls import path
from . import views
app_name = 'places'

urlpatterns = [
    path('', views.place_view, name='place_view'),
    path('toggle-all-places/', views.toggle_all_places, name='toggle_all_places'),
]
