import django_filters
from django_filters import NumberFilter, CharFilter
from .models import Product, Category
from django import forms


class ProductFilter(django_filters.FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains', label=False,
                      widget=forms.TextInput(attrs={
                          'placeholder': 'Product name',
                          'class': 'nameField',
                      }))
    price = NumberFilter(field_name='price', lookup_expr='lte', label=False,
                         widget=forms.NumberInput(attrs={
                          'placeholder': 'Price',
                          'class': 'priceField',
                      }))

    class Meta:
        model = Product
        fields = ['category']