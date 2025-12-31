from django.urls import path
from . import views

# urlpatterns = [
#     path('', views.customer_info, name='customer_info'),
#     path('order/', views.order_form, name='order_form'),
#     path('order/success/', views.order_success, name='order_success'),
#     path('order/confirm/', views.order_confirm, name='order_confirm'),     # NEW
#     path('orders/<int:order_id>/csv/', views.order_csv_admin, name='order_csv_admin'), 
#     path("orders/<int:order_id>/receipt/pdf/", views.order_receipt_pdf, name="order_receipt_pdf",),
#     path("orders/<int:order_id>/picking.pdf",views.order_picking_pdf,name="order_picking_pdf",),
#     path("api/orders-to-print/", views.orders_to_print, name="orders_to_print"),
#     path("api/orders/<int:order_id>/picking-pdf/", views.order_picking_pdf_for_print, name="order_picking_pdf_for_print"),
#     path("api/orders/<int:order_id>/mark-printed/", views.mark_order_printed, name="mark_order_printed"),
# ]

urlpatterns = [
    path('order/<str:customer_type>/', views.customer_info, name='customer_info'),
    path('order/<str:customer_type>/form/', views.order_form, name='order_form'),
    path('order/<str:customer_type>/success/', views.order_success, name='order_success'),
    path('order/<str:customer_type>/confirm/', views.order_confirm, name='order_confirm'),
    
    
    path('admin/order/<int:order_id>/csv/', views.order_csv_admin, name='order_csv_admin'),
    path('order/<int:order_id>/receipt/', views.order_receipt_pdf, name='order_receipt_pdf'),
    path('order/<int:order_id>/picking/', views.order_picking_pdf, name='order_picking_pdf'),
    
    
    path('api/orders-to-print/', views.orders_to_print, name='orders_to_print'),
    path('api/order/<int:order_id>/picking-pdf/', views.order_picking_pdf_for_print, name='order_picking_pdf_for_print'),
    path('api/order/<int:order_id>/mark-printed/', views.mark_order_printed, name='mark_order_printed'),
]
