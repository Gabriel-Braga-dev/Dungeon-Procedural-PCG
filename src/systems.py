# src/systems.py
from .ecs_core import Processor
from .rules import MechanicsRules, UIRules
from .components import (
    Position, Renderable, IntencaoMovimento, Health, 
    Inventory, MovementStats, GameStatus, Interactable, 
    LevelObjectives, TagPlayer, Tiles
)


class InteractionHandler:
    def __init__(self, world):
        self.world = world

    def resolve(self, target_ent, player_ent):

        if not self.world.has_component(target_ent, Interactable):
            return False

        interactable = self.world.component_for_entity(target_ent, Interactable)
        tipo = interactable.tipo
        
        health = self.world.component_for_entity(player_ent, Health)
        inv = self.world.component_for_entity(player_ent, Inventory)
        status = self.world.component_for_entity(player_ent, GameStatus)
        
        objetivos = next((comps[0] for _, comps in self.world.get_components(LevelObjectives)), None)
        obj_restantes = objetivos.total_restantes if objetivos else 0
            
        bloqueia, deletar = MechanicsRules.simular_interacao(tipo, health, inv, status, obj_restantes)

        if deletar:
            self.world.delete_entity(target_ent)
    
            if MechanicsRules.eh_objetivo_de_fase(tipo):
                for _, comps in self.world.get_components(LevelObjectives):
                    comps[0].total_restantes = max(0, comps[0].total_restantes - 1)

        return bloqueia
    
    
class MovementSystem(Processor):
    def __init__(self, interaction_handler, shared_data):
        super().__init__() 
        self.grid = shared_data.get('grid')
        self.interaction_handler = interaction_handler
        self.shared_data = shared_data

    def process(self):
        time_delta = self.shared_data.get('time_delta', 0.0)
        for ent, comps in self.world.get_components(Position, MovementStats, IntencaoMovimento):
            pos, m_stats, intencao = comps
            if intencao.dx == 0 and intencao.dy == 0: continue

            if not MechanicsRules.processar_cooldown(m_stats, time_delta):
                continue 
                
            new_x, new_y = pos.x + intencao.dx, pos.y + intencao.dy
            if not self._posicao_eh_valida_no_mapa(new_x, new_y): continue
            
            if self._movimento_esta_bloqueado_por_entidade(new_x, new_y, ent):
                continue
                
            pos.x, pos.y = new_x, new_y
            m_stats.wait_timer = m_stats.cooldown

    def _movimento_esta_bloqueado_por_entidade(self, new_x, new_y, player_ent):
        for target_ent, target_comps in self.world.get_components(Position, Interactable):
            t_pos = target_comps[0]
            if t_pos.x == new_x and t_pos.y == new_y:
                if self.interaction_handler.resolve(target_ent, player_ent):
                    return True
        return False

    def _posicao_eh_valida_no_mapa(self, x, y):
        if not (0 <= y < len(self.grid) and 0 <= x < len(self.grid[0])):
            return False
        return self.grid[y][x] == Tiles.FLOOR


class RenderSystem(Processor):
    def __init__(self, ui_manager, screen):
        super().__init__()
        self.ui_manager = ui_manager
        self.screen = screen
        self.zoom_level = 1.0
        self.zoom_minimo = 0.2
        self.zoom_maximo = 3.0
        self.passo_zoom = 0.1
        self.tile_size = 32

    def aplicar_zoom(self, direcao):
        self.zoom_level += direcao * self.passo_zoom
        self.zoom_level = max(self.zoom_minimo, min(self.zoom_level, self.zoom_maximo))

    def process(self):
        jogador = next((comps[0] for _, comps in self.world.get_components(Position, TagPlayer)), None)
        player_x, player_y = (jogador.x, jogador.y) if jogador else (0, 0)
    
        scaled_tile_size = int(self.tile_size * self.zoom_level)
        screen_center_x = self.screen.get_width() // 2
        screen_center_y = self.screen.get_height() // 2
        
        offset_x = screen_center_x - (player_x * scaled_tile_size)
        offset_y = screen_center_y - (player_y * scaled_tile_size)

        margem_x = (self.screen.get_width() // scaled_tile_size) // 2 + 2
        margem_y = (self.screen.get_height() // scaled_tile_size) // 2 + 2
        
        min_x, max_x = player_x - margem_x, player_x + margem_x
        min_y, max_y = player_y - margem_y, player_y + margem_y

        objetos_visiveis = []
        for _, comps in self.world.get_components(Position, Renderable):
            pos, rend = comps

            if min_x <= pos.x <= max_x and min_y <= pos.y <= max_y:
                img_final = self.ui_manager._obter_imagem_escalada(rend.image, scaled_tile_size)
                objetos_visiveis.append((img_final, pos.x * scaled_tile_size, pos.y * scaled_tile_size))
            
        self.ui_manager.desenhar_cenario(
            self.screen, 
            (offset_x, offset_y),  
            objetos_visiveis
        )


class HUDSystem(Processor):
    def __init__(self, ui_manager, screen, shared_data):
        super().__init__()
        self.ui_manager = ui_manager
        self.screen = screen
        self.shared_data = shared_data

    def process(self):
   
        for _, comps in self.world.get_components(TagPlayer, Health, Inventory):
            _, health, inv = comps 
            
            stats_raw = UIRules.extrair_status_hud(health, inv)
            objetivos = next((obj_comps[0] for _, obj_comps in self.world.get_components(LevelObjectives)), None)
            obj_restantes = objetivos.total_restantes if objetivos else 0
            nivel = self.shared_data.get('nivel_atual', 1)
            
            lista_textos = UIRules.formatar_textos_hud(nivel, stats_raw, obj_restantes)
            self.ui_manager.desenhar_hud(self.screen, lista_textos)


class GameFlowSystem(Processor):
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data

    def process(self):
        for _, comps in self.world.get_components(TagPlayer, GameStatus):
            status = comps[1] 
            
            novo_estado = MechanicsRules.avaliar_estado_jogo(status)
            
            if novo_estado != "PLAYING":
                self.shared_data['status_jogo'] = novo_estado
                return


class PlayerControlSystem(Processor):
 
    def __init__(self, shared_data):
        super().__init__()
        self.shared_data = shared_data

    def process(self):
    
        dx, dy = self.shared_data.get('input_movimento', (0, 0))
        for _, comps in self.world.get_components(TagPlayer, IntencaoMovimento):
            comps[1].dx = dx
            comps[1].dy = dy
            break