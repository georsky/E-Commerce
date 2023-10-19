from django import template

#CART SUM!#

register = template.Library()

@register.filter
def total_price(cart_items):
    return sum(item.subtotal for item in cart_items)

