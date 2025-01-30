from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search, name='search'),  # Ensure this line exists
]
