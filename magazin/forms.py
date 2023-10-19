from django import forms

################# FORMS VALIDATION for Checkout! #################

class CheckoutForm(forms.Form):
    full_name = forms.CharField(label='Full Name', required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter your full name'}))
    city = forms.CharField(label='City', required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter your city'}))
    shipping_address = forms.CharField(label='Shipping Address', required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter your shipping address'}))
    email = forms.EmailField(label='Email Address', required=True, widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address'}))
    phone = forms.CharField(label='Phone Number', required=True, widget=forms.TextInput(attrs={'type': 'tel', 'placeholder': 'Enter your phone number'}))
    payment_method = forms.ChoiceField(
        label='Payment Method',
        required=True,
        widget=forms.RadioSelect,
        choices=[
            ('credit-card', 'Credit Card'),
            ('cash', 'Cash'),
        ]
    )

