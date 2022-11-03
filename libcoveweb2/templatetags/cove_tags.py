import json
import random

from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("modal_list.html")
def cove_modal_list(**kw):
    return kw


@register.inclusion_tag("modal_errors.html")
def cove_modal_errors(**context):
    if hasattr(settings, "VALIDATION_ERROR_LOCATIONS_LENGTH"):
        context[
            "validation_error_locations_length"
        ] = settings.VALIDATION_ERROR_LOCATIONS_LENGTH
    else:
        context["validation_error_locations_length"] = 1000
    if hasattr(settings, "VALIDATION_ERROR_LOCATIONS_SAMPLE"):
        context[
            "validation_error_locations_sample"
        ] = settings.VALIDATION_ERROR_LOCATIONS_SAMPLE
    return context


@register.filter(name="json_decode")
def json_decode(error_json):
    return json.loads(error_json)


@register.filter(name="concat")
def concat(arg1, arg2):
    return str(arg1) + str(arg2)


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter(name="sample")
def sample(population, k):
    return random.sample(population, k)


@register.filter(name="take_or_sample")
def take_or_sample(population, k):
    if (
        hasattr(settings, "VALIDATION_ERROR_LOCATIONS_SAMPLE")
        and settings.VALIDATION_ERROR_LOCATIONS_SAMPLE
    ):
        if len(population) > k:
            return random.sample(population, k)
        else:
            return population
    else:
        return population[:k]


@register.filter(name="list_from_attribute")
def list_from_attribute(list_of_dicts, key_name):
    return [value[key_name] for value in list_of_dicts]
