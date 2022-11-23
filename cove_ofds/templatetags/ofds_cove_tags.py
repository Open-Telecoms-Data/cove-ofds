from django import template

register = template.Library()


@register.filter(name="error_instance_display")
def error_instance_display(input):
    if isinstance(input, str):
        return '"' + input + '"'
    else:
        return str(input)
