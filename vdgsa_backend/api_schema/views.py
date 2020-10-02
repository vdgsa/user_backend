from pathlib import Path

from django.http.response import FileResponse
from django.shortcuts import render


def redoc_schema_view(request):
    return render(request, 'redoc.html', {'schema_url': 'api-schema-yml'})


def api_schema_yml_view(request):
    return FileResponse(open(Path(__file__).resolve().parent / 'schema.yml', 'rb'))
