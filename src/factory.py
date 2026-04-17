# src/factory.py
from src.sprite_loader import SpriteLoader
from .rules import MechanicsRules
from src.systems import*
from src.components import (
    Position, Renderable, TagPlayer, LevelObjectives,  
    Health, MovementStats, GameStatus,
    Inventory, Interactable, IntencaoMovimento, Tiles
    )



class EntityFactory:
    def __init__(self, world):
        self.world = world
        self.loader = SpriteLoader()
    
    def preparar_jogo(self, shared_data):
        ent_game_manager = self.world.create_entity()
        layout_aprovado = shared_data.get('layout', {})
        total_objetivos = sum(1 for sprite in layout_aprovado.values() if MechanicsRules.eh_objetivo_de_fase(sprite))
        self.world.add_component(ent_game_manager, LevelObjectives(total_restantes=total_objetivos))
        
        self.spawn_map(shared_data['grid'])
        self.spawn_game_objects(layout_aprovado, shared_data['h_pos'], shared_data['e_pos'])

    def preparar_sistemas(self,  ui_manager,  screen, shared_data):
        world = self.world
        
        handler = InteractionHandler(world)

        ctrl_sys = PlayerControlSystem(shared_data) 
        world.add_processor(ctrl_sys) 

        move_sys = MovementSystem(handler, shared_data)
        world.add_processor(move_sys)

        render_sys = RenderSystem(ui_manager, screen)
        world.add_processor(render_sys)

        hud_sys = HUDSystem(ui_manager, screen, shared_data)
        world.add_processor(hud_sys)

        flow_sys = GameFlowSystem(shared_data)
        world.add_processor(flow_sys)
        
        return move_sys, render_sys

    def spawn_map(self, grid):
        height, width = len(grid), len(grid[0])
        for y in range(height):
            for x in range(width):
                if grid[y][x] == Tiles.FLOOR:
                    self._build_entity((x, y), 'floor')
                else:
                    is_border = False
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == Tiles.FLOOR:
                                is_border = True
                                break
                        if is_border: break
                    self._build_entity((x, y), 'wall' if is_border else 'wall_inner') 

    def spawn_game_objects(self, layout_aprovado, hero_pos, exit_pos):
        """Cria o herói e os objetos do nível com os novos componentes tipados."""
        self._build_entity(hero_pos, 'start')
        self._build_entity(exit_pos, ('exit'), Interactable('exit'))

        self._build_entity(
            hero_pos, 
            'hero', 
            TagPlayer(), 
            IntencaoMovimento(),
            Health(current=2, maximum=2),
            Inventory(key=0, treasure=0 ),
            MovementStats(cooldown=0.12, wait_timer=0.0),
            GameStatus(is_dead=False, has_escaped=False)
        )

        for pos, nome_sprite in layout_aprovado.items():
            self._build_entity(pos, nome_sprite, Interactable(nome_sprite))

    def _build_entity(self, pos, sprite_name, *components):

        image = self.loader.get_sprite(sprite_name)
        ent = self.world.create_entity()

        self.world.add_component(ent, Position(*pos))
        self.world.add_component(ent, Renderable(image))

        for comp in components:
            if comp is not None:
                self.world.add_component(ent, comp)
        return ent