from ariadne_codegen.plugins.base import Plugin
from graphql import Node


class KomodoAriandePlugin(Plugin):
    def process_name(self, name: str, node: Node | None = None) -> str:
        return name
