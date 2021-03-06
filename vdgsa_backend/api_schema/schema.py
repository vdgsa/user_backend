# """
# Contains classes used to customize how schema.yml is generated.
# """

# from typing import Any, Dict, Mapping, Type

# from rest_framework.schemas.openapi import AutoSchema  # type: ignore
# from rest_framework.serializers import Serializer


# class CustomSchema(AutoSchema):  # type: ignore
#     # Usage: operation_data should contain key/value
#     # pairs where the key is an HTTP method (GET, POST, etc.) and the
#     # value is an OpenAPI Operation object dictionary.
#     #
#     # The OpenAPI dicts will be used to update the schema data
#     # generated by AutoSchema, replacing keys that already exist.
#     # See the OpenAPI spec links for valid data:
#     # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#operationObject
#     #
#     # The "register_serializer" argument should be a dictionary of
#     # "<component name>": <serializer class>. The components specified
#     # will be added to the "components" section of the generated API schema.

#     def __init__(
#         self,
#         *args: Any,
#         register_serializers: Mapping[str, Type[Serializer]] = {},
#         operation_data: Dict[str, Any] = {},
#         **kwargs: Any
#     ):
#         super().__init__(*args, **kwargs)
#         self.operation_data = operation_data
#         self.register_serializers = register_serializers

#     def get_operation(self, path: str, method: str) -> Any:
#         operation = super().get_operation(path, method)
#         if method in self.operation_data:
#             operation.update(self.operation_data[method])

#         return operation

#     def get_components(self, path: str, method: str) -> Any:
#         components = super().get_components(path, method)
#         for name, serializer_class in self.register_serializers.items():
#             components[name] = self.map_serializer(serializer_class())

#         return components
