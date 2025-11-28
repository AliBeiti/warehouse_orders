from django.urls import path
from . import views

urlpatterns = [
    path('order/', views.order_form, name='order_form'),
    path('order/success/', views.order_success, name='order_success'),
    path('order/confirm/', views.order_confirm, name='order_confirm'),     # NEW
    path('orders/<int:order_id>/csv/', views.order_csv_admin, name='order_csv_admin'), 
    path("orders/<int:order_id>/receipt/pdf/", views.order_receipt_pdf, name="order_receipt_pdf",),
    path("orders/<int:order_id>/picking.pdf",views.order_picking_pdf,name="order_picking_pdf",),
    path("api/orders-to-print/", views.orders_to_print, name="orders_to_print"),
    path("api/orders/<int:order_id>/picking-pdf/", views.order_picking_pdf_for_print, name="order_picking_pdf_for_print"),
    path("api/orders/<int:order_id>/mark-printed/", views.mark_order_printed, name="mark_order_printed"),
]
