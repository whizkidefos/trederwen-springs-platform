from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def abs_value(value):
    """Return the absolute value of a number"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def add_class(field, css_classes):
    """Add CSS classes to a form field"""
    return field.as_widget(attrs={"class": css_classes})
