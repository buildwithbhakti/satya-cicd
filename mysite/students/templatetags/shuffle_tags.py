# templatetags/shuffle_tags.py
import random
from django import template

register = template.Library()

@register.filter
def shuffle_if(value, should_shuffle):
    
    lst = list(value)

    if should_shuffle:
        random.shuffle(lst)
  
    return lst
