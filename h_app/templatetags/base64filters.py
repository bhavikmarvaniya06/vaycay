import base64
from django import template

register = template.Library()

@register.filter
def b64encode(data):
    return base64.b64encode(data).decode()
