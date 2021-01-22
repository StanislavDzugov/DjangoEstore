from random import randint

from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .models import *
from .filters import ProductFilter
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import CreateUserForm
import json


# Create your views here.
def register(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account was created for {username}')
            return redirect('store')
    context = {'form': form}
    return render(request, 'store/register.html', context)


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('store')
        else:
            messages.info(request, 'Username or Password is incorrect!')
    context = {}
    return render(request, 'store/login.html', context)


def logout_user(request):
    logout(request)
    return redirect('store')


def store(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            id = request.POST.get('product')
            product = Product.objects.get(id=id)
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
            if not created:
                order_item.quantity += 1
            else:
                order_item.quantity = 1
            order_item.save()

        else:
            return redirect('login')

    products = Product.objects.all()

    myFilter = ProductFilter(request.GET, queryset=products)
    products = myFilter.qs

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)

    context = {
        'page_obj': page_obj,
        'products': products,
        'myFilter': myFilter,
    }

    return render(request, 'store/store.html', context)


@login_required(login_url='login')
def cart(request):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    if request.method == 'POST':
        if request.POST.get('delete'):
            order.delete()
        else:
            id = request.POST.get('product')
            product = Product.objects.get(id=id)
            item = OrderItem.objects.get(product=product)
            if request.POST.get('+'):
                item.quantity += 1
                item.save()
            elif request.POST.get('-'):
                item.quantity -= 1
                item.save()
                if item.quantity == 0:
                    item.delete()

    context = {
        'items': items,
        'order': order
    }

    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    cart_items = order.get_cart_items_quantity
    if request.method == 'POST':
        shipping_address = ShippingAddress.objects.create(customer=customer,
                                                          order=order,
                                                          address=request.POST.get('address'),
                                                          city=request.POST.get('city'),
                                                          postcode=request.POST.get('postcode'))
        shipping_address.save()

    context = {
        'items': items,
        'order': order,
        'cart_items': cart_items
    }
    return render(request, 'store/checkout.html', context)
