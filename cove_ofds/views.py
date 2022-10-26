import functools
import json
import logging
from decimal import Decimal

from django.shortcuts import render
from libcove.lib.exceptions import CoveInputDataError

from cove_ofds.process import (
    ChecksAndStatistics,
    ConvertJSONIntoGeoJSON,
    ConvertJSONIntoSpreadsheets,
    ConvertSpreadsheetIntoJSON,
    WasJSONUploaded,
)
from libcoveweb2.views import explore_data_context

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def cove_web_input_error(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except CoveInputDataError as err:
            return render(request, "error.html", context=err.context)

    return wrapper


@cove_web_input_error
def explore_ofds(request, pk):
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error

    PROCESS_TASKS = [
        WasJSONUploaded(db_data),
        ConvertSpreadsheetIntoJSON(db_data),
        ConvertJSONIntoGeoJSON(db_data),
        ConvertJSONIntoSpreadsheets(db_data),
        ChecksAndStatistics(db_data),
    ]

    # Process bit that should be a task in a worker
    process_data = {}
    for task in PROCESS_TASKS:
        try:
            process_data = task.process(process_data)
        except Exception as err:
            print(err)

    # read results
    for task in PROCESS_TASKS:
        try:
            context.update(task.get_context())
        except Exception as err:
            print(err)

    template = "cove_ofds/explore.html"

    return render(request, template, context)
