# src/map_generator.py
import random
from src.components import Tiles

class Room:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.connected_corridors = 0
        self.door_pos = None
        
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other, margin=1):
        # Métrica de Colisão: Garante que as salas não se toquem, 
        # mantendo a topologia clara e evitando paths paralelos indesejados.
        return (self.x - margin < other.x + other.w + margin and
                self.x + self.w + margin > other.x - margin and
                self.y - margin < other.y + other.h + margin and
                self.y + self.h + margin > other.y - margin)

    def get_free_tiles(self):
        return [(x, y) for x in range(self.x, self.x + self.w) 
                       for y in range(self.y, self.y + self.h)]


class MapGenerator:
    """
    Algoritmo construtivo baseado em Carving direcional (Spanning Tree).
    Garante matematicamente a ausência de atalhos (loops) e a criação de gargalos obrigatórios.
    """
    def __init__(self, width, height, num_rooms, tam_max_rooms):
        self.width = width
        self.height = height
        self.num_rooms = num_rooms
        self.tam_max_rooms = tam_max_rooms
        self.grid = [[Tiles.WALL for _ in range(self.width)] for _ in range(self.height)]
        self.rooms = []
        self.corridors = []
        
    def generate(self):
        start_room = Room(self.width // 2 - 2, self.height // 2 - 2, 5, 5)
        self._carve_room(start_room)
        self.rooms.append(start_room)
        
        tentativas_totais = 0
        while len(self.rooms) < self.num_rooms and tentativas_totais < 1000:
            self._grow()
            tentativas_totais += 1
            
        # Leaf Rooms (Salas Folha): Componente vital da topologia.
        # "Cofres" para trancar tesouros.
        leaf_rooms = [r for r in self.rooms if r.connected_corridors == 1]
        
        if len(leaf_rooms) < 2:
            leaf_rooms = self.rooms[1:] if len(self.rooms) > 1 else [self.rooms[0]]
            
        return self.grid, self.rooms, self.corridors, leaf_rooms

    def _carve_room(self, room):
        for x in range(max(0, room.x), min(self.width, room.x + room.w)):
            for y in range(max(0, room.y), min(self.height, room.y + room.h)):
                self.grid[y][x] = Tiles.FLOOR
                
    def _grow(self):
        """Tenta ramificar a dungeon a partir de uma sala existente (Árvore Geradora)."""
        if not self.rooms: return
        
        room = random.choice(self.rooms)
        dx, dy = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
        corr_len = random.randint(2, 6) 
        rw = random.randint(3, self.tam_max_rooms)
        rh = random.randint(3, self.tam_max_rooms) 
        
        cx, cy = self._calcular_inicio_corridor(room, dx, dy)
        
        sucess_corridor, path_corridor  = self._tracar_corridor(cx, cy, dx, dy, corr_len)
        if not sucess_corridor: return
            
        new_room = self._criar_sala_no_fim(path_corridor [-1][0], path_corridor [-1][1], dx, dy, rw, rh)
        
        # Teste de Look-ahead: Só constrói a sala se não colidir com o mapa existente.
        # É isso que previne os atalhos (loops)!
        if not self._sala_eh_valida(new_room): return
            
        self._conectar_e_construir(room, new_room, path_corridor )

    # --- Métodos de Apoio ao Crescimento ---

    def _calcular_inicio_corridor(self, room, dx, dy):
        """Define onde o corridor vai 'nascer' nas bordas da sala."""
        if dx == 1:   return room.x + room.w, random.randint(room.y, room.y + room.h - 1)
        elif dx == -1: return room.x - 1, random.randint(room.y, room.y + room.h - 1)
        elif dy == 1:  return random.randint(room.x, room.x + room.w - 1), room.y + room.h
        else:          return random.randint(room.x, room.x + room.w - 1), room.y - 1

    def _tracar_corridor(self, start_x, start_y, dx, dy, length):
        """Tenta "andar" pelo grid. Retorna (Sucesso, Lista de Posições)."""
        path_corridor  = []
        curr_x, curr_y = start_x, start_y
        
        for _ in range(length):
            # Guard Clauses de Validação do path_corridor 
            if not (1 < curr_x < self.width - 2 and 1 < curr_y < self.height - 2): 
                return False, []
            
            if self.grid[curr_y][curr_x] == Tiles.FLOOR: 
                return False, [] 
            
            # Checar pisos adjacentes para evitar "paredes duplas" esquisitas
            adj = sum(1 for ax, ay in [(0,1),(0,-1),(1,0),(-1,0)] 
                      if self.grid[curr_y+ay][curr_x+ax] == Tiles.FLOOR)
            if adj > 1: return False, []
            
            path_corridor .append((curr_x, curr_y))
            curr_x += dx
            curr_y += dy
            
        return True, path_corridor 

    def _criar_sala_no_fim(self, cx, cy, dx, dy, rw, rh):
        """Faz a matemática para posicionar a sala colada no fim do corredor."""
        # Posição teórica do próximo tile a seguir ao fim do corredor
        curr_x, curr_y = cx + dx, cy + dy
        
        if dx == 1:   rx, ry = curr_x, curr_y - rh//2
        elif dx == -1: rx, ry = curr_x - rw + 1, curr_y - rh//2
        elif dy == 1:  rx, ry = curr_x - rw//2, curr_y
        else:          rx, ry = curr_x - rw//2, curr_y - rh + 1
            
        return Room(rx, ry, rw, rh)

    def _sala_eh_valida(self, new_room):
        """Garante que não fica fora do mapa nem por cima de outra."""
        if not (1 <= new_room.x and new_room.x + new_room.w < self.width - 1 and
                1 <= new_room.y and new_room.y + new_room.h < self.height - 1): 
            return False
            
        for r in self.rooms:
            if new_room.intersects(r, margin=1): return False
            
        return True

    def _conectar_e_construir(self, room_origem, new_room, path_corridor):
        """Efetiva a criação no mapa gravando no Grid."""
        room_origem.connected_corridors += 1
        new_room.connected_corridors += 1
        new_room.door_pos = path_corridor[-1] 
        
        for tx, ty in path_corridor:
            self.grid[ty][tx] = Tiles.FLOOR
            self.corridors.append((tx, ty))
            
        self._carve_room(new_room)
        self.rooms.append(new_room)

# ==========================================
# FUNÇÕES EXTERNAS DE UTILIDADE
# ==========================================

def gerar_mapa_valido( config_topo, max_tentativas=2000):
    """Tenta várias vezes até a MapGenerator criar um layout aceitável."""
    width = config_topo.get('width', 30)
    height =  width
    target_room = config_topo.get('rooms', 8)
    tam_max = config_topo.get('tam_rooms', 3)
    
    for tent in range(1, max_tentativas):
        gen = MapGenerator(width, height, target_room, tam_max)
        grid, rooms, corridors, leaf_rooms = gen.generate()
        
        if _mapa_atende_requisitos(rooms, leaf_rooms, target_room):
            free = [(x, y) for y in range(height) for x in range(width) if grid[y][x] == Tiles.FLOOR]
            meta = {'rooms': rooms, 'corridors': corridors, 'leaf_rooms': leaf_rooms, 'start_room': rooms[0], 'free':free}
            
            return grid, meta, tent
            
    return None, None, max_tentativas

def _mapa_atende_requisitos(rooms, leaf_rooms, target_room):
    tem_folhas_suficientes = len(leaf_rooms) >= 2
    tem_tamanho_exato = len(rooms) == target_room
    return tem_folhas_suficientes and tem_tamanho_exato