from django.urls import path
from . import views

urlpatterns = [
    path('order/', views.order_form, name='order_form'),
    path('order/success/', views.order_success, name='order_success'),
]
