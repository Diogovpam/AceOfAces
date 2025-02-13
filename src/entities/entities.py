from enum import Enum
from typing import Union, List, Optional

from pydantic import BaseModel

from src.entities.move_content import MoveNames, MoveDescriptions

STATUS_TEMPLATE = '''You are in page %s, %s.

You currently have %s health

Your enemy is at %s distance.
You are %s tailing your enemy.
You are %s firing at your enemy.
Your enemy is %s firing at you.'''


class Factions(str, Enum):
    GERMAN = "german"
    ALLIES = "allies"

    @classmethod
    def get_faction(cls, selection):
        return {
            '1': cls.ALLIES,
            '2': cls.GERMAN
        }.get(selection)

    @classmethod
    def get_opposing_faction(cls, player_faction: "Factions") -> "Factions":
        """Returns the opposing faction based on the player's faction."""
        return cls.GERMAN if player_faction == cls.ALLIES else cls.ALLIES


class Distance(str, Enum):
    LONG = "long"
    MEDIUM = "medium"
    CLOSE = "close"


class FireType(str, Enum):
    OUT = "out"
    IN = "in"
    MUTUAL = "mutual"
    NONE = "none"


class Direction(str, Enum):
    LEFT = "left"
    STRAIGHT = "straight"
    RIGHT = "right"


class Movement(BaseModel):
    index: int
    next_page: Optional[int] = None
    descent: bool = False
    flair: bool = False
    modifier: int
    direction: Direction


class DetailedMovement(Movement):
    name: MoveNames
    description: MoveDescriptions


class Page(BaseModel):
    faction: Factions
    page_num: int
    distance: Distance
    tail: bool = False
    fire: FireType
    moves: List[Movement]


class PlayerInfo(BaseModel):
    player_name: str
    faction: Factions
