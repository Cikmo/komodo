import ast

from ariadne_codegen.client_generators.constants import ALIAS_KEYWORD
from ariadne_codegen.codegen import generate_constant, generate_pydantic_field
from ariadne_codegen.plugins.base import Plugin
from graphql import ExecutableDefinitionNode, FieldNode


class KomodoAriandePlugin(Plugin):
    """
    Ariadne plugin that generates Pydantic models with alias support.
    """

    def generate_result_field(
        self,
        field_implementation: ast.AnnAssign,
        operation_definition: ExecutableDefinitionNode,
        field: FieldNode,
    ) -> ast.AnnAssign:
        if field.alias and not field.alias.value.startswith("_"):
            alias = generate_constant(field.name.value)
            if isinstance(field_implementation.value, ast.Call):
                field_implementation.value.keywords.append(
                    ast.keyword(arg=ALIAS_KEYWORD, value=alias)
                )
            else:
                field_implementation.value = generate_pydantic_field(
                    {ALIAS_KEYWORD: alias}
                )
        return field_implementation
