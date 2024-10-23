from django.urls import path

from scraper.views import BrandProductsView

urlpatterns = [
    path('', BrandProductsView.as_view(), name='brand-products'),
]
