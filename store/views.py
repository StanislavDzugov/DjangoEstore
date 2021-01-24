from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from djangoEshop import settings
from .models import *
from .filters import ProductFilter
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import CreateUserForm
import stripe


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
            order, created = Order.objects.get_or_create(customer=customer, status='Not Paid')
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
    order, created = Order.objects.get_or_create(customer=customer, status='Not Paid')
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
    order, created = Order.objects.get_or_create(customer=customer, status='Not Paid')
    items = order.orderitem_set.all()
    cart_items = order.get_cart_items_quantity
    if request.method == 'POST':
        shipping_address = ShippingAddress.objects.update_or_create(customer=customer,
                                                                    order=order,
                                                                    defaults={
                                                                        'country': request.POST.get('country'),
                                                                        'address': request.POST.get('address'),
                                                                        'city': request.POST.get('city'),
                                                                        'postcode': request.POST.get('postcode')
                                                                    })
        context = {
            'items': items,
            'order': order,
            'cart_items': cart_items,
            'shipping_address': shipping_address
        }
        return render(request, 'store/checkout.html', context)

    context = {
        'items': items,
        'order': order,
        'cart_items': cart_items
    }
    return render(request, 'store/checkout.html', context)


def product_details(request, pk):
    product = Product.objects.get(pk=pk)
    if request.method == 'POST':
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, status='Not Paid')
            order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
            if not created:
                order_item.quantity += 1
            else:
                order_item.quantity = 1
            order_item.save()
            messages.success(request, 'Product added to cart successfully')

    context = {'product': product}

    return render(request, 'store/product_detail.html', context)


@login_required(login_url='login')
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


@login_required(login_url='login')
@csrf_exempt
def create_checkout_session(request):
    order = Order.objects.get(customer=request.user.customer, status='Not Paid')
    amount = int(order.get_cart_total * 100)
    print(amount)
    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                line_items=[
                    {
                        'name': f'Your Order: #{order.id}',
                        'quantity': 1,
                        'currency': 'usd',
                        'amount': amount,
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})


@login_required(login_url='login')
def success(request):
    order = Order.objects.get(customer=request.user.customer, status='Not Paid')
    order.status = 'Paid'
    order.save()
    messages.success(request, 'Your payment succeeded')
    return redirect('store')


@login_required(login_url='login')
def cancelled(request):
    messages.error(request, 'Your payment was cancelled.')
    return redirect('cart')
