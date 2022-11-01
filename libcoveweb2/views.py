from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from libcoveweb2.forms import NewJSONUploadForm
from libcoveweb2.models import SuppliedData, SuppliedDataFile


def index(request):

    return render(request, "libcoveweb2/index.html", {})


def new_json(request):

    forms = {
        "upload_form": NewJSONUploadForm(request.POST, request.FILES)
        if request.POST
        else NewJSONUploadForm()
    }
    form = forms["upload_form"]
    if form.is_valid():
        supplied_data = SuppliedData()
        supplied_data.format = "json"
        supplied_data.save()

        supplied_data.save_file(request.FILES["file_upload"])

        return HttpResponseRedirect(supplied_data.get_absolute_url())

    return render(request, "libcoveweb2/new_json.html", {"forms": forms})


def new_spreadsheet(request):

    forms = {
        "upload_form": NewJSONUploadForm(request.POST, request.FILES)
        if request.POST
        else NewJSONUploadForm()
    }
    form = forms["upload_form"]
    if form.is_valid():
        supplied_data = SuppliedData()
        supplied_data.format = "spreadsheet"
        supplied_data.save()

        supplied_data.save_file(request.FILES["file_upload"])

        return HttpResponseRedirect(supplied_data.get_absolute_url())

    return render(request, "libcoveweb2/new_spreadsheet.html", {"forms": forms})


def explore_data_context(request, pk):
    try:
        data = SuppliedData.objects.get(pk=pk)
    except (
        SuppliedData.DoesNotExist,
        ValidationError,
    ):  # Catches primary key does not exist and badly formed UUID
        return (
            {},
            None,
            render(
                request,
                "error.html",
                {
                    "sub_title": _(
                        "Sorry, the page you are looking for is not available"
                    ),
                    "link": "index",
                    "link_text": _("Go to Home page"),
                    "msg": _(
                        "We don't seem to be able to find the data you requested."
                    ),
                },
                status=404,
            ),
        )

    supplied_data_files = SuppliedDataFile.objects.filter(supplied_data=data)
    for supplied_data_file in supplied_data_files:
        if not supplied_data_file.does_exist_in_storage():
            return (
                {},
                None,
                render(
                    request,
                    "error.html",
                    {
                        "sub_title": _(
                            "Sorry, the page you are looking for is not available"
                        ),
                        "link": "index",
                        "link_text": _("Go to Home page"),
                        "msg": _(
                            "The data you were hoping to explore no longer exists.\n\nThis is because all "
                            "data supplied to this website is automatically deleted after 7 days, and therefore "
                            "the analysis of that data is no longer available."
                        ),
                    },
                    status=404,
                ),
            )

    context = {
        "supplied_data_files": supplied_data_files,
        "created_datetime": data.created.strftime("%A, %d %B %Y %I:%M%p %Z"),
        "created_date": data.created.strftime("%A, %d %B %Y"),
        "created_time": data.created.strftime("%I:%M%p %Z"),
    }

    return (context, data, None)
