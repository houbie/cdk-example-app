from connexion.mock import Resolver

NOT_IMPLEMENTED = "_not_implemented_"


class PartialImplementationResolver(Resolver):
    """Resolver that does not require that all operations defined in the OpenAPI have an implementation
    This allows for some operations to be handled elsewhere (f.e. by another lambda).
    Calling an unresolved operation results in a 501 'not implemented' response
    """

    def __init__(
        self,
    ):
        self.counter = 0
        super().__init__()

    def resolve_operation_id(self, operation):
        self.counter += 1
        return super().resolve_operation_id(operation) or f"_not_implemented_{self.counter}"

    def resolve_function_from_operation_id(self, operation_id):
        if operation_id.startswith(NOT_IMPLEMENTED):
            operation_id = f"{self.__class__.__module__}.not_implemented"
        return super().resolve_function_from_operation_id(operation_id)


def not_implemented(*_args, **_kwargs):
    return "not implemented", 501
