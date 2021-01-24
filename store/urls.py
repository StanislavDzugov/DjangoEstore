from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('product-details/<str:pk>', views.product_details, name='product-details'),
    path('config/', views.stripe_config, name='config'),
    path('create-checkout-session/', views.create_checkout_session, name='create-checkout-session'),
    path('success/', views.success, name='success'),
    path('cancelled/', views.cancelled, name='cancelled')
]