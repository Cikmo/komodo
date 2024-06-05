"""
Here we define the database tables.
"""

from piccolo.columns import Text, Serial
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model


class Nation(Table):
    """
    A table to store information about nations in the game.
    """

    id = Serial(primary_key=True)
    name = Text()


NationModel = create_pydantic_model(Nation)
