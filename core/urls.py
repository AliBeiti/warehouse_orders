from django.urls import path
from . import views

urlpatterns = [
    path('order/', views.order_form, name='order_form'),
    path('order/success/', views.order_success, name='order_success'),
    path('order/confirm/', views.order_confirm, name='order_confirm'),     # NEW
    path('orders/<int:order_id>/csv/', views.order_csv_admin, name='order_csv_admin'), 
    path("orders/<int:order_id>/receipt/pdf/", views.order_receipt_pdf, name="order_receipt_pdf",),
    path("orders/<int:order_id>/picking.pdf",views.order_picking_pdf,name="order_picking_pdf",),
]
