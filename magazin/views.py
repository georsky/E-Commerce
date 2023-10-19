from django.shortcuts import render, get_object_or_404, redirect, HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy, reverse
from django.core.mail import send_mail
from .forms import CheckoutForm
from .models import Category, Product, Cart, Order , OrderItem, Invoice
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.db import transaction
from .utils.pdf_utils import generate_invoice_pdf, generate_unique_invoice_number
from django.core.files.base import ContentFile
from django.utils import timezone

# Create your views here.

####################################################################### PRODUCT LIST!!! ############################################################################
def product_list(request):
    selected_category_id = request.GET.get('category')
    if selected_category_id:
        selected_category = get_object_or_404(Category, id=selected_category_id)
        products = Product.objects.filter(category=selected_category)
    else:
        products = Product.objects.all()
        selected_category = None
    
    categories = Category.objects.all()
    context = {
        'products': products,
        'selected_category': selected_category,
        'categories': categories,
    }
    return render(request, 'product_list.html', context)

def home(request):
    return render(request, 'home.html')

####################################################################### HOME!!! ############################################################################
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        #Check password if is True!
        if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
            messages.error(request, "Your password must contain both letters and digits.")
            return render(request, 'register.html', {'username': username, 'email': email})

        if len(password) < 8:
            messages.error(request, "Your password must contain at least 8 characters.")
            return render(request, 'register.html', {'username': username, 'email': email})

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html', {'username': username, 'email': email})
        
        # Check if the username or email is already taken
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'register.html', {'email': email})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already taken.")
            return render(request, 'register.html', {'username': username})
        
         # Create a new user and save to the database
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # After successful registration, redirect to the confirmation page
        return redirect('confirmation') 

    return render(request, 'register.html')

####################################################################### CART!!! ############################################################################
def cart(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        total_quantity = sum(item.quantity for item in cart_items)

        for item in cart_items:
            item.subtotal = item.product.price * item.quantity

        context = {
            'cart_items': cart_items,
            'cart_count': total_quantity,
        }
    else:
        context = {
            'cart_items': [],
            'cart_count': 0,
        }

    return render(request, 'cart.html', context)

####################################################################### ADD_TO_CART!!! ############################################################################
def add_to_cart(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        
        try:
            cart = Cart.objects.get(user=request.user, product=product)
        except Cart.DoesNotExist:
            # If the cart item doesn't exist, create a new one
            cart = Cart(user=request.user, product=product, quantity=0, subtotal=0)

        # Calculate the subtotal
        subtotal = product.price

        cart.quantity += 1
        cart.subtotal += subtotal  # Update the subtotal
        cart.save()

        return redirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect('login')

####################################################################### REMOVE_FROM_CART!!! ############################################################################

def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(Cart, user=request.user, product=product)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.subtotal -= product.price
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('cart')

####################################################################### CONFIRMATION!!! ############################################################################
def confirmation(request):
    if request.method == 'POST':
        
        return redirect('confirmation')  # 'confirmation' is the URL name for the confirmation page

    return render(request, 'confirmation.html')

####################################################################### USER-LOGIN!!! ############################################################################
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to the user's profile page or another page
        else:
            messages.error(request, "Invalid login credentials.")
            return render(request, 'login.html', {'username': username})
        
    return render(request, 'login.html')

####################################################################### LOGOUT!!! ############################################################################
def user_logout(request):
    logout(request)
    return redirect('home') # Redirect to the home

####################################################################### PROFILE!!! ############################################################################

@login_required
def profile(request):
    return render(request, 'profile.html') # Redirect to the profile page

####################################################################### CHECKOUT ##################################################################
###################################################################################################################################################

@login_required
def checkout(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)  # Calculate total price

    error_message = ""

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            total_order_price = total_price
            payment_method = form.cleaned_data['payment_method']

            if payment_method == 'credit-card':
                # Display a message indicating that Credit Card payment is not available
                error_message = "Credit Card payment is not available. Please choose another payment method."
            else:
                try:
                    with transaction.atomic():
                        # Create the order within a database transaction
                        order = Order.objects.create(
                            user=user,
                            shipping_address=form.cleaned_data['shipping_address'],
                            payment_method=payment_method,
                            total_price=total_order_price,  # Use the updated total price
                            full_name=full_name,
                        )

                    for cart_item in cart_items:
                        order_item = OrderItem.objects.create(
                            order=order,
                            product=cart_item.product,
                            quantity=cart_item.quantity,
                            subtotal=cart_item.subtotal
                        )
                        order.products.add(cart_item.product)  # Associate the product with the order

                    cart_items.delete()
                    
                    # Generate the invoice PDF and get the next invoice number
                    pdf_buffer, invoice_number = generate_invoice_pdf(order, full_name)

                    # Save the PDF to the invoice
                    invoice = Invoice(order=order, invoice_number=invoice_number)
                    invoice.pdf.save(f'invoice_{invoice_number}.pdf', ContentFile(pdf_buffer.read()))
                    invoice.save()

                    # Send confirmation email to the customer
                    customer_email = form.cleaned_data['email']
                    send_confirmation_email(customer_email, order, pdf_buffer, invoice_number)

                    # Send office notification email
                    send_office_notification_email(order)

                    return redirect('confirmation')

                except Exception as e:
                    # Handle any exceptions here
                    messages.error(request, f"An error occurred: {str(e)}")
                    return redirect('checkout')

    else:
        # Create a blank form for rendering on the page
        form = CheckoutForm()

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,  # Update total_price with the calculated value
        'error_message': error_message,
    }

    return render(request, 'checkout.html', context)

####################################################################  SEND CONFIRMATION EMAIL! #########################################################################

def send_confirmation_email(customer_email, order, pdf_buffer, invoice_number):
    try:
        subject = 'Order Confirmation'
        from_email = 'blgeo.adrian@gmail.com'
        recipient_list = [customer_email]

        # Initialize a list to store product information
        product_info = []

        # Iterate through order items and build product information list
        for order_item in order.orderitem_set.all():
            product_info.append({
                'name': order_item.product.name,
                'price': order_item.product.price,
                'quantity_ordered': order_item.quantity,
                'subtotal': order_item.subtotal,
            })

        # Calculate the total order price (including shipping) within this function
        total_order_price = order.total_price

        # Pass the order, product information, and total_order_price to the email template
        email_context = {
            'order': order,
            'product_info': product_info,
            'invoice_number': invoice_number,
            'total_order_price': total_order_price,
        }

        message_html = render_to_string('order_confirmation_email.html', email_context)

        # Create a text/plain message for email clients that don't support HTML
        message_text = strip_tags(message_html)

        email = EmailMultiAlternatives(subject, message_text, from_email, recipient_list)
        email.attach_alternative(message_html, "text/html")  

        # Attach the invoice PDF
        pdf_filename = f'invoice_{invoice_number}.pdf'
        email.attach(pdf_filename, pdf_buffer.getvalue(), 'application/pdf')

        # Attach images
        for order_item in order.orderitem_set.all():
            if order_item.product.image:
                email.attach_file(order_item.product.image.path)

        email.send()

        # Log success
        print(f'Successfully sent order confirmation email to {customer_email}')
    except Exception as e:
        # Log the error
        print(f'Error sending order confirmation email: {str(e)}')


####################################################################  SEND CONFIRMATION OFFICE EMAIL! #########################################################################

def send_office_notification_email(order):
    try:
        subject = 'New Order Received'
        message = f'An order with order ID {order.id} has been received. Please check the order details.'
        from_email = 'blgeo.adrian@gmail.com'
        recipient_list = ['blgeo.adrian@gmail.com']  # Replace with the actual email address of your office

        email = EmailMultiAlternatives(subject, message, from_email, recipient_list)
        email.send()

        # Log success
        print(f'Successfully sent office notification email for order ID {order.id}')
    except Exception as e:
        # Log the error
        print(f'Error sending office notification email: {str(e)}')  

####################################################################  ORDER HISTORY! #########################################################################

def order_history(request):
    user = request.user  # Get the current user
    orders = Order.objects.filter(user=user).order_by('-id')  # Get the user's orders, ordered by creation date (most recent first)

    # Create a list of dictionaries, each containing an order and its associated products
    orders_with_products = []

    for order in orders:
        products = order.products.all()
        orders_with_products.append({'order': order, 'products': products})

    context = {'user': user, 'orders_with_products': orders_with_products}
    return render(request, 'order_history.html', context)

####################################################################  GENERATE INVOICE! #########################################################################
####################################################################  GENERATE INVOICE! #########################################################################
@login_required
def generate_invoice(request, order_id):
    try:
        # Check if the order belongs to the current user
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return HttpResponse("Order not found or doesn't belong to the current user.", status=404)

    # Get the current date and time
    current_datetime = timezone.now()

    # Generate a unique invoice number
    invoice_number = generate_unique_invoice_number(order)

    # Generate the invoice PDF with the current_datetime
    invoice_pdf_buffer, invoice_number = generate_invoice_pdf(order, current_datetime)

    if invoice_pdf_buffer:
        # Create and save the invoice with the current date
        invoice = Invoice(order=order, invoice_number=invoice_number, date=current_datetime)
        invoice.pdf.save(f'invoice_{invoice_number}.pdf', ContentFile(invoice_pdf_buffer.read()), save=True)

        # Redirect to the invoice detail page
        return redirect('invoice_detail', invoice_id=invoice.id)
    else:
        return HttpResponse("Failed to generate the invoice PDF.", status=500)
    
####################################################################  INVOICE! #########################################################################
####################################################################  INVOICE! #########################################################################    

def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    return render(request, 'invoice_detail.html', {'invoice': invoice})

####################################################################  INVOICE! #########################################################################
####################################################################  INVOICE! #########################################################################

def invoice_list(request):
    invoices = Invoice.objects.order_by('-created_at')

    return render(request, 'invoice_list.html', {'invoices': invoices})

####################################################################  RESET PASSWORD LOGIC! #########################################################################
####################################################################  RESET PASSWORD LOGIC! #########################################################################

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'

def send_password_reset_email(customer_email, reset_link):
    try:
        subject = 'Password Reset'
        from_email = 'blgeo.adrian@gmail.com'
        recipient_list = [customer_email]

        # Create the email message with HTML content
        email = EmailMultiAlternatives(subject, '', from_email, recipient_list)
        email.content_subtype = 'html'

        # Render the HTML email template
        html_message = render_to_string('password_reset_email.html', {'reset_link': reset_link})

        # Attach the HTML content to the email
        email.attach_alternative(html_message, 'text/html')

        email.send()

        print(f'Successfully sent password reset email to {customer_email}')
    except Exception as e:
        print(f'Error sending password reset email: {str(e)}')



