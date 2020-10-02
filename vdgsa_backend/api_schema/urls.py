from django.urls import path, re_path

from .views import api_schema_yml_view, redoc_schema_view

urlpatterns = [
    path('schema.yml', api_schema_yml_view, name='api-schema-yml'),
    re_path('docs/?', redoc_schema_view, name='redoc'),
]
