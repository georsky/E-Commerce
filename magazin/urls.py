from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetCompleteView
from django.contrib.auth import views as auth_views
from .views import *


urlpatterns = [
    #BASE
    path('', home, name='home'),
    #Products
    path('product', product_list, name='product'),
    #Register
    path('register', register, name='register'),
    #Cart
    path('cart', cart, name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    #Checkout
    path('checkout', checkout, name='checkout'),
    path('confirmation', confirmation, name='confirmation'),
    #Login
    path('login', user_login, name='login'),
    #Logout
    path('logout', user_logout, name='logout'),
    #Profile
    path('profile', profile, name='profile'),
    #Order-History
    path('order_history', order_history, name='order_history'),
    #Reset Password Logic!
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    #Invoice
    path('generate_invoice/<int:order_id>/', generate_invoice, name='generate_invoice'),
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', invoice_detail, name='invoice_detail'),
]+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
