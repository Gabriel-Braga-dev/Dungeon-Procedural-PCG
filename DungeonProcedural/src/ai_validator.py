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

        while (queue and  estados_explorados < 2000000):
            
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

    def __init__(self, grid, salas, corredores, leaf_rooms):
        self.grid = grid
        self.salas = salas
        self.corredores = corredores
        self.leaf_rooms = leaf_rooms
        self.start_pos = None
        self.exit_pos = None

        self.salas_para_trancar = []
        self.salas_trancadas = []
        self.corredores_livres = []

    def _preparar_terreno(self):
        folhas = self.leaf_rooms.copy()
        if len(folhas) < 2:
            folhas = self.salas.copy()

        random.shuffle(folhas)
        sala_start = folhas.pop()
        sala_exit = folhas.pop()
        
        self.start_pos = sala_start.center()
        self.exit_pos = sala_exit.center()

        # 1. Pega as folhas normais que sobraram
        self.salas_para_trancar = [s for s in folhas if s.door_pos is not None]

        # ---------------------------------------------------------
        #LEMRA DE ALTERAR NOTIFICAÇÕES DE SALAS COFRES no UIRules
        # Se quiser que a SAÍDA possa ter porta (Sala do Boss):
        if sala_exit.door_pos is not None:
            self.salas_para_trancar.append(sala_exit)

        # Se quiser que o INÍCIO possa ter porta (Prisão):
        if sala_start.door_pos is not None:
            self.salas_para_trancar.append(sala_start)
        # ---------------------------------------------------------

        self.corredores_livres = self.corredores.copy()
        random.shuffle(self.corredores_livres)
    
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
            qtd_real = qtd_pedida

           # E nos IFs de segurança, separamos as lógicas de limite!
            if id_tecnico == 'door':
                qtd_real = min(qtd_pedida, len(self.salas_para_trancar))
                
            elif id_tecnico == 'key':
                # Chaves: Precisam existir em quantidade de portas mais 1
                qtd_real = min(qtd_pedida, limite_fisico_portas + 1)
                
            elif id_tecnico == 'treasure':
                # Tesouros: O limite máximo obedece estritamente aos COFRES 
                qtd_real = min(qtd_pedida, len(self.salas_trancadas))
                
            alocados = 0
            for _ in range(qtd_real):
                posicao = metodo_arquitetura(layout)
                if posicao:
                    layout[posicao] = sprite
                    alocados += 1

            if id_tecnico == 'door':
                limite_fisico_portas = alocados
                if qtd_pedida > limite_fisico_portas:
                    avisos.append(f"Aviso: Limite físico excedido! Só foi possível colocar {limite_fisico_portas} portas, chaves e tesouros.")

        return layout, avisos
    

    def _achar_posicao_porta(self, layout):
        if self.salas_para_trancar:
            sala = self.salas_para_trancar.pop(0)
            pos = sala.door_pos
            if pos not in layout and pos != self.start_pos and pos != self.exit_pos:

                # prenvine que tesouros sejam colocados na sala de incio e fim
                if sala.center() != self.start_pos and sala.center() != self.exit_pos:  
                    self.salas_trancadas.append(sala)
                return pos
        return None

    def _achar_posicao_tesouro(self, layout):
        if self.salas_trancadas:
            sala = self.salas_trancadas.pop(0)
            pos = sala.center()
            if pos not in layout and pos != self.start_pos and pos != self.exit_pos:
                return pos
        return self._achar_posicao_sala(layout)

    def _achar_posicao_corredor(self, layout):
        while self.corredores_livres:
            pos = self.corredores_livres.pop()
            if pos not in layout and pos != self.start_pos and pos != self.exit_pos:
                return pos
        return self._achar_posicao_aleatoria(layout)

    def _achar_posicao_sala(self, layout):
        # PROTEÇÃO 3: Previne falhas se a sala for minúscula e já estiver cheia
        salas_disp = self.salas.copy()
        random.shuffle(salas_disp)
        
        for sala in salas_disp:
            livres = [pos for pos in sala.get_free_tiles() if pos not in layout and pos != self.start_pos and pos != self.exit_pos]
            if livres:
                return random.choice(livres)       
        return self._achar_posicao_aleatoria(layout)

    def _achar_posicao_aleatoria(self, layout):
        # OTIMIZAÇÃO: Em vez de varrer o Grid inteiro, nós apenas pedimos os tiles
        # às salas e corredores que já estão guardados na memória!
        todos_tiles = []
        for sala in self.salas:
            todos_tiles.extend(sala.get_free_tiles())
        todos_tiles.extend(self.corredores)
        
        # Filtra os ocupados
        tiles_livres = [pos for pos in todos_tiles if pos not in layout 
                        and pos != self.start_pos and pos != self.exit_pos]
                        
        if tiles_livres:
            return random.choice(tiles_livres)
        return None

# ==========================================
# SIMULANDO O AGENTE NO LAYOUT
# ==========================================

def tentar_distribuicoes_validas(grid, meta, config_pop):
    salas = meta.get('rooms', [])
    corredores = meta.get('corridors', [])
    leaf_rooms = meta.get('leaf_rooms', [])
    
    distribuidor = DistribuidorItens(grid, salas, corredores, leaf_rooms)
    max_tentativas = 100
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