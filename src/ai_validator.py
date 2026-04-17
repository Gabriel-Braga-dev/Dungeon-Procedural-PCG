# src/ai_validator.py
import random
import heapq
import itertools
from collections import deque
from src.components import  Tiles 
from src.rules import AIRules, LayoutRules


# ==========================================
# CRIAÇÃO DA IA VALIDADORA(A* Manhattan, COM VERIFICAÇAO INICIAL CASO TENHA MAPAS QUEBRADOS)
# ==========================================

class AgentAvaliador:
    @classmethod
    def _teste_conectividade_basica(cls, grid, start_pos, exit_pos, layout):
        visited = {start_pos}
        queue = deque([start_pos])
        alvos = set(layout.keys())
        alvos.add(exit_pos)
        alcançados = 1 if start_pos in alvos else 0

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = x+dx, y+dy
                if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == Tiles.FLOOR:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
                        if (nx, ny) in alvos:
                            alcançados += 1
                            if alcançados == len(alvos): return True
        return alcançados == len(alvos)

    @staticmethod
    def heuristica(x, y, exit_pos, restantes):
        """
        O Faro do Agente (Heurística Gulosa Customizada).
        Em vez de procurar cegamente a saída, a IA atua como um "cão de caça".
        """
        # Enquanto a Regra de 100% não for atingida, o peso atrai a IA para o item mais próximo.
        if restantes:
            # Distância de Manhattan até o item relevante
            distancias = [abs(x - rx) + abs(y - ry) for rx, ry in restantes]
            # O peso "+50" afasta ativamente a IA da saída prematura.
            return min(distancias) + 50 
            
        # Quando a lista 'restantes' está vazia (100% coletado), a IA aponta direto para a Saída.
        return abs(x - exit_pos[0]) + abs(y - exit_pos[1])

    @classmethod
    def simular(cls, grid, start_pos, exit_pos, layout, tipos_relevantes):
        # 1. Poda rápida: Se o mapa tá quebrado, corta a validação na hora!
        #COMO O MAPA JÁ FOI BEM CONSTRUIDO, NÃO É NECESSARIO, 
        #VISTO QUE QUALQUER DISTRIBUIÇÃO DE INTENS É ACESSÍVEL
        #if not cls._teste_conectividade_basica(grid, start_pos, exit_pos, layout):
        #   return False, 1 

        itens_rastreados = {pos for pos, tipo in layout.items() if tipo in tipos_relevantes}
        
        # Setup do A* e Priority Queue
        counter = itertools.count() # Desempata custos iguais no Heap

        # STATE-SPACE SEARCH (Busca no Espaço de Estados):
        # O BFS explodiria a RAM. Por isso usamos A* e a tupla não é apenas X e Y.
        # O "Estado" do Agente salva também as variáveis matemáticas do jogo naquele momento!
        estado_inicial_core = (start_pos[0], start_pos[1], 2, 0, frozenset(itens_rastreados))
        
        g_cost = 0
        h_cost = cls.heuristica(start_pos[0], start_pos[1], exit_pos, itens_rastreados)
        
        # A Fila agora é estruturada por: (Custo Total, Custo Real, ID, X, Y, HP, Chaves, Restantes)
        queue = []
        heapq.heappush(queue, (h_cost, g_cost, next(counter), start_pos[0], start_pos[1], 2, 0, frozenset(itens_rastreados)))
        
        visited = {estado_inicial_core}
        estados_explorados = 0

        while (queue and  estados_explorados < 4000000):
            
            estados_explorados += 1
            _, g, _, x, y, hp, chaves, restantes = heapq.heappop(queue)
            
            # CONDIÇÃO DE VITÓRIA: 100% DE LIMPEZA
            if (x, y) == exit_pos:
                if len(restantes) == 0:
                    return True, estados_explorados
                    
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = x + dx, y + dy
                
                if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == Tiles.FLOOR:
                    novos_restantes = set(restantes)
                    mov_valido = True
                    novo_hp, novas_chaves = hp, chaves
                    
                    if (nx, ny) in novos_restantes:
                        tipo = layout[(nx, ny)]
                        
                        # Simula as restrições da regra de jogo sem gerar novas classes (Otimização O(1))
                        bloqueia, deletar, novo_hp, novas_chaves = AIRules.simular_interacao_ia(tipo, hp, chaves)
                        
                        if bloqueia: mov_valido = False
                        elif deletar: novos_restantes.remove((nx, ny))
                            
                    if mov_valido:
                        est_core = (nx, ny, novo_hp, novas_chaves, frozenset(novos_restantes))
                        if est_core not in visited:
                            visited.add(est_core)
                            novo_g = g + 1
                            h = cls.heuristica(nx, ny, exit_pos, novos_restantes)
                            
                            # A* empurra para o início da fila quem tem a melhor chance matemática!
                            heapq.heappush(queue, (novo_g + h, novo_g, next(counter), nx, ny, novo_hp, novas_chaves, frozenset(novos_restantes)))
                            
        return False, estados_explorados

# ==========================================
# GERAÇÃO DE LAYOUTS 
# ==========================================

class DistribuidorItens:

    def __init__(self, rooms, corridors, leaf_rooms):
        
        self.rooms = rooms
        self.corridors = corridors
        self.leaf_rooms = leaf_rooms
        self.start_pos = None
        self.exit_pos = None

        self.rooms_para_trancar = []
        self.rooms_cofre = []
        self.available_corridors = []

    def _preparar_terreno(self):
        leaves = self.leaf_rooms.copy()
        if len(leaves) < 2:
            leaves = self.rooms.copy()

        random.shuffle(leaves)
        sala_start = leaves.pop()
        sala_exit = leaves.pop()
        
        self.start_pos = sala_start.center()
        self.exit_pos = sala_exit.center()

        # 1. Pega as leaves normais que sobraram
        self.rooms_para_trancar = [s for s in leaves if s.door_pos is not None]

        # ---------------------------------------------------------
        #LEMRA DE ALTERAR NOTIFICAÇÕES DE rooms COFRES no UIRules
        # Se quiser que a SAÍDA possa ter porta (Sala do Boss):
        if sala_exit.door_pos is not None:
            self.rooms_para_trancar.append(sala_exit)

        # Se quiser que o INÍCIO possa ter porta (Prisão):
        if sala_start.door_pos is not None:
            self.rooms_para_trancar.append(sala_start)
        # ---------------------------------------------------------

        self.available_corridors = self.corridors.copy()
        random.shuffle(self.available_corridors)
    
    def gerar_layout(self, config_pop):
        layout = {}
        avisos = []
        estrategias = LayoutRules._ESTRATEGIAS
        self._preparar_terreno()

        itens_ordenados = sorted(
            config_pop.items(),
            key=lambda item: estrategias.get(item[0], {'prioridade': 99})['prioridade']
        )

        limite_fisico_portas = 0

        for id_tecnico, qtd_pedida in itens_ordenados:
            sprite = id_tecnico 
            estrategia = estrategias.get(id_tecnico)

            if not estrategia: continue

            metodo_arquitetura = getattr(self, estrategia['metodo'])
            qtd_real = LayoutRules.restricao_cofre(
                id_tecnico, qtd_pedida, 
                len(self.rooms_para_trancar), limite_fisico_portas, 
                len(self.rooms_cofre)
                )
                
            alocados = 0
            for _ in range(qtd_real):
                posicao = metodo_arquitetura(layout)
                if posicao:
                    layout[posicao] = sprite
                    alocados += 1

            if LayoutRules.eh_porta(id_tecnico):
                limite_fisico_portas = alocados
                if qtd_pedida > limite_fisico_portas:
                    avisos.append(f"Aviso: Limite físico excedido! Só foi possível colocar {limite_fisico_portas} portas, chaves e tesouros.")

        return layout, avisos

    def _achar_posicao_porta(self, layout):
        if self.rooms_para_trancar:
            room = self.rooms_para_trancar.pop(0)
            pos = room.door_pos
            if pos not in layout and pos != self.start_pos and pos != self.exit_pos:

                # prenvine que tesouros sejam colocados na room de incio e fim
                if room.center() != self.start_pos and room.center() != self.exit_pos:  
                    self.rooms_cofre.append(room)
                return pos
        return None

    def _achar_posicao_tesouro(self, layout):
        if self.rooms_cofre:
            room = self.rooms_cofre.pop(0)
            pos = room.center()
            if pos not in layout and pos != self.start_pos and pos != self.exit_pos:
                return pos
        return self._achar_posicao_sala(layout)

    def _achar_posicao_corredor(self, layout):
        while self.available_corridors:
            pos = self.available_corridors.pop()
            if pos not in layout and pos != self.start_pos and pos != self.exit_pos:
                return pos
        return self._achar_posicao_aleatoria(layout)

    def _achar_posicao_sala(self, layout):
        # PROTEÇÃO 3: Previne falhas se a sala for minúscula e já estiver cheia
        rooms_disp = self.rooms.copy()
        random.shuffle(rooms_disp)
        
        for room in rooms_disp:
            available = [pos for pos in room.get_free_tiles() if pos not in layout and pos != self.start_pos and pos != self.exit_pos]
            if available:
                return random.choice(available)       
        return self._achar_posicao_aleatoria(layout)

    def _achar_posicao_aleatoria(self, layout):
        # OTIMIZAÇÃO: Em vez de varrer o Grid inteiro, nós apenas pedimos os tiles
        # às rooms e corridors que já estão guardados na memória!
        all_tiles = []
        for room in self.rooms:
            all_tiles.extend(room.get_free_tiles())
        all_tiles.extend(self.corridors)
        
        # Filtra os ocupados
        tiles_available = [pos for pos in all_tiles if pos not in layout 
                        and pos != self.start_pos and pos != self.exit_pos]
                        
        if tiles_available:
            return random.choice(tiles_available)
        return None

# ==========================================
# SIMULANDO O AGENTE NO LAYOUT
# ==========================================

def tentar_distribuicoes_validas(grid, meta, config_pop):
    rooms = meta.get('rooms', [])
    corridors = meta.get('corridors', [])
    leaf_rooms = meta.get('leaf_rooms', [])
    
    distribuidor = DistribuidorItens(rooms, corridors, leaf_rooms)
    max_tentativas = 101
    num_visitados_totais = 0
    for tentativas in range(1, max_tentativas):
        
        resultado_layout = distribuidor.gerar_layout(config_pop)
        
        if resultado_layout[0] is None: 
            return None, None, None, tentativas, ["Falha de layout."]
            
        layout, avisos = resultado_layout

        tipos_relevantes = AIRules.obter_tipos_relevantes_ia()
        
        sucesso, num_visitados = AgentAvaliador.simular(
            grid, distribuidor.start_pos, distribuidor.exit_pos, layout, tipos_relevantes
        )

        num_visitados_totais += num_visitados
        if sucesso:
            log = [f"Sucesso na tentativa {tentativas}."] + avisos + [f"Estados explorados: { num_visitados_totais}"]
            return layout, distribuidor.start_pos, distribuidor.exit_pos, tentativas, log
            
    return None, None, None, tentativas, [f"Falha: Limite de tentativas atingido. {tentativas}"]