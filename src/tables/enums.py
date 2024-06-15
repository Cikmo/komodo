from enum import StrEnum


class Color(StrEnum):
    """Represents the colors in the game."""

    AQUA = "aqua"
    BLACK = "black"
    BLUE = "blue"
    BROWN = "brown"
    GREEN = "green"
    LIME = "lime"
    MAROON = "maroon"
    OLIVE = "olive"
    ORANGE = "orange"
    PINK = "pink"
    PURPLE = "purple"
    RED = "red"
    WHITE = "white"
    YELLOW = "yellow"
    BEIGE = "beige"
    GRAY = "gray"


class Continent(StrEnum):
    """Enum representing the continents in the game."""

    NORTH_AMERICA = "na"
    SOUTH_AMERICA = "sa"
    ASIA = "as"
    ANTARCTICA = "an"
    EUROPE = "eu"
    AFRICA = "af"
    AUSTRALIA = "au"


class WarPolicy(StrEnum):
    """Enum representing the war policies of the nations in the game."""

    ATTRITION = "ATTRITION"
    TURTLE = "TURTLE"
    BLITZKRIEG = "BLITZKRIEG"
    FORTRESS = "FORTRESS"
    MONEYBAGS = "MONEYBAGS"
    PIRATE = "PIRATE"
    TACTICIAN = "TACTICIAN"
    GUARDIAN = "GUARDIAN"
    COVERT = "COVERT"
    ARCANE = "ARCANE"


class DomesticPolicy(StrEnum):
    """Enum representing the domestic policies of the nations in the game."""

    MANIFEST_DESTINY = "MANIFEST_DESTINY"
    OPEN_MARKETS = "OPEN_MARKETS"
    TECHNOLOGICAL_ADVANCEMENT = "TECHNOLOGICAL_ADVANCEMENT"
    IMPERIALISM = "IMPERIALISM"
    URBANIZATION = "URBANIZATION"
    RAPID_EXPANSION = "RAPID_EXPANSION"


class TreatyType(StrEnum):
    """Enum representing the types of alliance treaties in the game."""

    MDP = "MDP"
    MDOAP = "MDoAP"
    ODP = "ODP"
    ODOAP = "ODoAP"
    PROTECTORATE = "Protectorate"
    PIAT = "PIAT"
    NAP = "NAP"
    NPT = "NPT"
    EXTENSION = "Extension"
