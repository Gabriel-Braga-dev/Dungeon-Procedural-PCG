# src/components.py
from dataclasses import dataclass

@dataclass
class Tiles:
    WALL = 0
    FLOOR = 1

@dataclass
class Position:
    x: int
    y: int

@dataclass
class Renderable:
    image: any 

@dataclass
class IntencaoMovimento:
    dx: int = 0
    dy: int = 0

@dataclass
class Health:
    current: int
    maximum: int 

@dataclass
class Inventory:
    key: int 
    treasure: int 

@dataclass
class MovementStats:
    cooldown: float = 0.12
    wait_timer: float = 0.0

@dataclass
class GameStatus:
    is_dead: bool = False
    has_escaped: bool = False

@dataclass
class Interactable:
    tipo: str

@dataclass
class LevelObjectives:
    total_restantes: int = 0
    
@dataclass
class TagPlayer: 
    pass