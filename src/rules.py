# src/rules.py
import random

class UIRules:

    #REGRAS TOPOLOGIA

    @staticmethod
    def contar_salas_cofre_disponiveis(meta):
        """Isola a lógica de contagem de salas folha que podem ser trancadas."""
        leaf_rooms = meta.get('leaf_rooms', [])
        # _preparar_terreno na classe DistribuirItens em AI_validator.py
        # MODIFICAR AQUI QUANDO DECIDIR SE COFRES NO INICIO/FIM  EM ATÉ - 2 
        # NO MOMENTO TANTO INICIO QUANTO FIM SÃO TRANCAVEIS 
        return len([s for s in leaf_rooms if getattr(s, 'door_pos', None) is not None])
    
    def msg_cofres_pop (meta):
        qtd_cofres = UIRules.contar_salas_cofre_disponiveis(meta)
        free_tiles = meta.get('free',[])
        msg = f"Tiles Livres: {len(free_tiles)}  |  Salas Cofre (Máx Portas): {qtd_cofres}"
        return msg
    
    # REGRAS POPULAÇÃO

    @staticmethod
    def calcular_sincronizacao_populacao(nome_alterado, valor_tentado, valores_atuais):
        """Regra de Ouro do Puzzle Tático (Economia 1:1)."""
        atualizacoes = {nome_alterado: valor_tentado}

        estrategias = {
            'door':   lambda v, _: {'key': v , 'treasure': v},
            'key':   lambda v, _: {'door': v , 'treasure': v },
            'treasure': lambda v, _: {'door': v, 'key': v },
            'dragon': lambda v, _: {'potion': v },
            'potion':   lambda v, _: {'dragon': v }
        }

        if nome_alterado in estrategias:
            atualizacoes.update(estrategias[nome_alterado](valor_tentado, valores_atuais))

        return atualizacoes

    @staticmethod
    def avaliar_risco_ia(config_populacao):

        tipos_relevantes = AIRules.obter_tipos_relevantes_ia() 
        total_rastreados = sum(config_populacao.get(tipo, 0) for tipo in tipos_relevantes)
        
        combinacoes = 2 ** total_rastreados
        seguro = total_rastreados <= 24
        
        if combinacoes >= 1000000000:
            texto_combinacoes = f"{combinacoes / 1000000000:.1f}G"
        elif combinacoes >= 1000000:
            texto_combinacoes = f"{combinacoes / 1000000:.1f}M"
        elif combinacoes >= 1000:
            texto_combinacoes = f"{combinacoes / 1000:.1f}K"
        else:
            texto_combinacoes = str(combinacoes)
            
        return seguro, texto_combinacoes

    # REGRAS DO HUD

    @staticmethod
    def extrair_status_hud(health, inventory):
        """Traduz componentes do backend para rótulos da tela."""
        return {
            'HP': health.current,
            'Max_HP': health.maximum,
            'Chaves': inventory.key,
            'Tesouros': inventory.treasure
        }

    @staticmethod
    def formatar_textos_hud(andar, stats, objetivos):
        """Transforma dados brutos em lista de strings formatadas para a UI."""
        textos = [f"Andar: {andar}"]
        
        # Lógica de cor implícita: a UI verificará se o HP não é o máximo
        if 'HP' in stats:
            textos.append(f"HP: {stats['HP']}/{stats['Max_HP']}")
        
        textos.append(f"Chaves: {stats.get('Chaves', 1)}")
        textos.append(f"Objetivos: {objetivos}")
        return textos

class MechanicsRules:

    # ==========================================
    # SIMULAÇÃO PARA INTERAÇÕES DURANTE JOGO
    # ==========================================

    @classmethod
    def simular_interacao(cls, tipo_interagido, health, inventory, game_status, objetivos_restantes=0):
        """
        Delega a interação dinamicamente com base no nome do item recebido.
        """
        nome_metodo = f'_interagir_{tipo_interagido}'
        metodo = getattr(cls, nome_metodo, cls._interagir_padrao)
        return metodo(health, inventory, game_status, objetivos_restantes)

    # MICROSSERVIÇOS DE INTERAÇÃO 

    @staticmethod
    def _interagir_door(_health, inventory, _game_status, _objetivos_restantes):
        if inventory.key > 0:
            inventory.key -= 1
            return False, True 
        return True, False

    @staticmethod
    def _interagir_dragon(health, _inventory, game_status, _objetivos_restantes):
        health.current -= 1
        if health.current <= 0:
            game_status.is_dead = True
            return True, False
        return False, True

    @staticmethod
    def _interagir_key(_health, inventory, _game_status, _objetivos_restantes):
        inventory.key += 1
        return False, True

    @staticmethod
    def _interagir_potion(health, _inventory, _game_status, _objetivos_restantes):
        if health.current < health.maximum:
            health.current = health.maximum
            return False, True
        return True, False

    @staticmethod
    def _interagir_treasure(_health, inventory, _game_status, _objetivos_restantes):
        inventory.treasure += 1
        return False, True

    @staticmethod
    def _interagir_exit(_health, _inventory, game_status, objetivos_restantes):
        if objetivos_restantes == 0:
            game_status.has_escaped = True
            return False, False
        return True, False

    @staticmethod
    def _interagir_padrao(_health, _inventory, _game_status, _objetivos_restantes):
        """Fallback de segurança."""
        return False, False

    # ==========================================
    # REGRAS AUXILIARES 

    @staticmethod
    def eh_objetivo_de_fase(tipo_interagido):
        """Todos os itens são obrigatórios para a vitória no Puzzle."""
        return tipo_interagido in ['dragon', 'potion', 'key', 'door', 'treasure']

    @staticmethod
    def masmorra_esta_limpa(total_objetivos):
        """Retorna True se o jogador completou seus objetivos."""
        return total_objetivos == 0
    
    @staticmethod
    def verificar_ultimo_andar_concluido(nivel_atual, max_niveis=10):
        """Retorna True se o jogador acabou de vencer o andar final da história."""
        return nivel_atual == max_niveis

    @staticmethod
    def avaliar_estado_jogo(game_status):
        if game_status.is_dead: return "GAME_OVER"
        if game_status.has_escaped: return "VICTORY"
        return "PLAYING"

    @staticmethod
    def processar_cooldown(stats, time_delta):
        stats.wait_timer -= time_delta
        return stats.wait_timer <= 0
    

class AIRules:

    @staticmethod
    def obter_tipos_relevantes_ia():
        # Não precisa dos tesouros para calcular o fim do jogo visto que ele é diretamnete associado a porta
        return ['dragon', 'potion', 'door', 'key']
    
    # ==========================================
    # SIMULAÇÃO PARA INTERAÇÕES DA IA
    # ==========================================
    _REGRAS_IA = {
        # Dragão: Se HP > 1, sobrevive (hp-1). Se HP = 1, bloqueia e morre.
        'dragon':   lambda hp, c: (False, True, hp - 1, c) if hp > 1 else (True, False, hp, c),
        
        # Poção: Se HP < 2 cura. Se HP = 2 bloqueia o caminho
        'potion':   lambda hp, c: (False, True, 2, c) if hp < 2 else (True, False, hp, c),
        
        # Porta: Consome chave (c-1) se c > 0.
        'door':     lambda hp, c: (False, True, hp, c - 1) if c > 0 else (True, False, hp, c),
        
        # Chave: Acrescenta na mochila (c+1).
        'key':      lambda hp, c: (False, True, hp, c + 1),
        
        # Tesouro: Apenas coleta (deleta a entidade).
        'treasure': lambda hp, c: (False, True, hp, c)
    }

    @classmethod
    def simular_interacao_ia(cls, tipo_interagido, hp, chaves):
        """Executa a simulação da IA sem instanciar classes, usando dicionário O(1)."""
        regra = cls._REGRAS_IA.get(tipo_interagido)
        if regra:
            return regra(hp, chaves)
        return False, True, hp, chaves # Fallback
    
   
class LayoutRules:

    _ESTRATEGIAS = {
        'door':     {'prioridade': 1, 'metodo': '_achar_posicao_porta'},
        'treasure': {'prioridade': 2, 'metodo': '_achar_posicao_tesouro'},
        'key':      {'prioridade': 3, 'metodo': '_achar_posicao_sala'},
        'dragon':   {'prioridade': 4, 'metodo': '_achar_posicao_corredor'},
        'potion':   {'prioridade': 4, 'metodo': '_achar_posicao_corredor'}
    }

    def restricao_cofre(id_tec, qtd_pedida, rooms_para_trancar, limite_fisico_porta, rooms_cofre):
        if id_tec == 'door':
            qtd_real = min (qtd_pedida, rooms_para_trancar)
                
        elif id_tec == 'key':
            # Chaves: Precisam existir em quantidade de portas mais 1
            qtd_real = min (qtd_pedida, limite_fisico_porta + 1)
                
        elif id_tec == 'treasure':
            # Tesouros: O limite máximo obedece estritamente aos COFRES 
            qtd_real = min (qtd_pedida, rooms_cofre)
        else:
            qtd_real = qtd_pedida

        return qtd_real
    
    def eh_porta(id_tec):
        if id_tec == 'door':
            return True
        return False


class LevelBalancer:
  
    def __init__(self):
        self.regras_populacao = {}
        self._configurar_regras_base()

    def registrar_regra(self, id_tec_interno, regra_func):
        self.regras_populacao[id_tec_interno] = regra_func

    def _configurar_regras_base(self):
        # Economia estrita: 
        # - Poções são dadas com base na quantidade de dragões (garantindo sobrevivência HP 2).
        # - Chaves são dadas na exata proporção (ou levemente acima) das portas.
        # - Tesouros são dados na exata proporção (ou levemente abaixo(inicio e fim trancados)) das portas.
        self.registrar_regra('dragon',   lambda n, pop: random.randint(2, min(6, 2 + (n // 2))))
        self.registrar_regra('potion',   lambda n, pop: max(1, pop.get('dragon', 1) - random.randint(0,1)))
        self.registrar_regra('door',     lambda n, pop: random.randint(1, min(5, 1 + (n // 3))))
        self.registrar_regra('key',      lambda n, pop: pop.get('door', 1) + random.randint(0,1))
        self.registrar_regra('treasure', lambda n, pop: max(1, pop.get('door', 1)))

    def calcular_dificuldade(self, nivel):

        tam_map = min(40, 20 + (nivel//2))
        num_rooms =  min(25, 3 + (nivel//2))

        config_topo = {
            'width': tam_map,
            'rooms': num_rooms,
            'tam_rooms': 3
        }

        config_pop = {}
        for id_tec, regra in self.regras_populacao.items():
            config_pop[id_tec] = regra(nivel, config_pop)

        self._aplicar_seguranca(config_pop)

        return config_topo, config_pop

    def _aplicar_seguranca(self, config_pop):
        
        tipos_relevantes = AIRules.obter_tipos_relevantes_ia() 
        total_rastreados = sum(config_pop.get(id_tec, 0) for id_tec in tipos_relevantes)
        max_relevantes = 20
     
        if total_rastreados > max_relevantes:
            for id_tec in tipos_relevantes:
                config_pop[id_tec] = max(1, config_pop.get(id_tec, 0) - 1)
            print(config_pop)

    def andar_seguranca(self, config_topo, config_pop, tentativas_globais):

        if tentativas_globais > 5:
    
            config_topo = {'width': 30, 'height': 30, 'rooms': 8, 'tam_rooms': 3}
            config_pop = {'dragon': 2, 'potion': 2, 'door': 2, 'key': 2, 'treasure': 2}
               
        return config_topo, config_pop


