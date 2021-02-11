from pathlib import Path

from django.http.request import HttpRequest
from django.http.response import FileResponse, HttpResponse
from django.shortcuts import render


def redoc_schema_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'redoc.html', {'schema_url': 'api-schema-yml'})


def api_schema_yml_view(request: HttpRequest) -> FileResponse:
    return FileResponse(open(Path(__file__).resolve().parent / 'schema.yml', 'rb'))
