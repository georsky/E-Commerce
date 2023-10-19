from django.db.models import Sum
from .models import Cart

##################### COUNTER 

def cart_counter(request):
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    else:
        cart_count = 0 
    return {'cart_count': cart_count}
