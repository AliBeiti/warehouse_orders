from django.shortcuts import render
from .models import Product
# Create your views here.
def order_form(request):
    # For now, GET only: list active products in warehouse pick order
    products = Product.objects.filter(is_active=True).order_by('pick_order', 'name')
    return render(request, 'order_form.html', {'products': products})