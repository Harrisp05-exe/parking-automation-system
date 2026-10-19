from django.urls import path
from parking import views
urlpatterns = [path('', views.home, name='home'), path('api/check-in/', views.check_in), path('api/availability/', views.availability), path('visit/<uuid:token>/', views.visit, name='visit'), path('visit/<uuid:token>/checkout/', views.checkout, name='checkout')]
