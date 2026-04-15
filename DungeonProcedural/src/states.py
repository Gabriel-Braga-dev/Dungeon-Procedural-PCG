# src/states.py
from abc import ABC
from src.ecs_core import World
from src.input_manager import Acao
from src.factory import EntityFactory
from src.rules import UIRules, MechanicsRules
from src.map_generator import gerar_mapa_valido
from src.ai_validator import tentar_distribuicoes_validas 


class State(ABC):
    def __init__(self, game):
        self.game = game 

    def enter(self): pass
    def exit(self): pass
    def handle_event(self, event): pass
    def update(self, time_delta): pass
    def draw(self, screen): pass


class EstadoMenuInicial(State):
    def enter(self):
        self.game.ui.limpar_interface()
        self.game.ui.build_menu_inicial()
        self.mapa_botoes = {
            self.game.ui.btn_novo_jogo: self._iniciar_nova_partida,
            self.game.ui.btn_criativo: self._ir_para_criativo,
            self.game.ui.btn_sair: self._sair_do_jogo
        }

    def handle_event(self, event):
        self.game.ui.processar_eventos_base(event)
        self.game.ui.verificar_cliques_botoes(event, self.mapa_botoes)

    def _iniciar_nova_partida(self):
        self.game.change_state(GeradorNivelState(self.game))
        
    def _ir_para_criativo(self):
        self.game.change_state(EstadoTopologia(self.game))
        
    def _sair_do_jogo(self):
        self.game.running = False

    def update(self, time_delta):
        self.game.ui.update(time_delta)

    def draw(self, screen):
        self.game.ui.desenhar_fundo_menu(screen)
        self.game.ui.draw(screen)
        self.game.ui.draw_legend(screen)


class EstadoTopologia(State):
    def enter(self):
        
        self.game.ui.preparar_fase_criativo()
        self.mapa_botoes = {
            self.game.ui.btn_gerar_topologia: self._gerar_nova_topologia,
            self.game.ui.btn_avancar: self._avancar_fase
        }

    def handle_event(self, event):
        self.game.ui.processar_eventos_base(event)
        self.game.ui.processar_eventos_sliders(event) 
        self.game.ui.verificar_cliques_botoes(event, self.mapa_botoes)

        acao = self.game.im.traduzir_evento_discreto(event)
        if acao == Acao.VOLTAR:
            self.game.change_state(EstadoMenuInicial(self.game))

    def _avancar_fase(self):
        self.game.change_state(EstadoPopulacao(self.game))

    def _gerar_nova_topologia(self):
        raw_config = self.game.ui.get_topologia_config()
        
        config_topo = {**raw_config, 'height': raw_config['width']} 

        grid, free_tiles, meta, tent = gerar_mapa_valido(config_topo)
        
        if grid:
            self.game.shared_data.update({'grid': grid, 'meta': meta})
            self.game.shared_data.pop('layout', None)
            self.game.shared_data.pop('h_pos', None)
            self.game.shared_data.pop('e_pos', None)
            self.game.ui.mostrar_sucesso_topologia(tent)
            
            qtd_cofres = UIRules.contar_salas_cofre_disponiveis(meta)
            msg = f"Tiles Livres: {len(free_tiles)}  |  Salas Cofre (Máx Portas): {qtd_cofres}"
            self.game.ui.lbl_info_mapa.set_text(msg)
        else:
            self.game.ui.mostrar_erro_topologia()
           

    def _configurar_limites_fase_2(self, meta):
        qtd_leafs, qtd_corredores, limites = UIRules.calcular_limites_fase_2(meta)
        self.game.ui.aplicar_limites_dinamicos(qtd_leafs, qtd_corredores, limites)

    def update(self, time_delta):
        self.game.ui.update(time_delta)

    def draw(self, screen):

        self.game.ui.desenhar_fundo_menu(screen)
        self.game.ui.manager.draw_ui(screen)

        grid_data = {'grid': self.game.shared_data.get('grid')}
        self.game.ui.desenhar_preview_mapa(screen, grid_data)


class EstadoPopulacao(State):
    def enter(self):

        self.game.ui.show_fase_2()
        self.mapa_botoes = {
            self.game.ui.btn_validar: self._executar_validacao_ia,
            self.game.ui.btn_jogar: self._iniciar_jogo,
            self.game.ui.btn_voltar: self._voltar_fase
        }

    def handle_event(self, event):
        self.game.ui.processar_eventos_base(event)
        self.game.ui.processar_eventos_sliders(event) 
        self.game.ui.verificar_cliques_botoes(event, self.mapa_botoes)

    def _iniciar_jogo(self):
        self.game.shared_data['nivel_atual'] = 1
        self.game.change_state(JogandoState(self.game))

    def _voltar_fase(self):
        self.game.change_state(EstadoTopologia(self.game))

    def _executar_validacao_ia(self):

        ui = self.game.ui
        params = ui.get_populacao_config()
        ui.preparar_validacao_ia(self.game.screen) 

        layout, h_pos, e_pos, tent, log = tentar_distribuicoes_validas(
            self.game.shared_data['grid'], 
            self.game.shared_data['meta'], 
            params            
        )
        
        if layout:
            self.game.shared_data.update({'layout': layout, 'h_pos': h_pos, 'e_pos': e_pos})
            
        ui.exibir_resultado_ia(sucesso=(layout is not None), tentativas=tent, log=log)
    
    def update(self, time_delta):
        self.game.ui.update(time_delta)

    def draw(self, screen):
        self.game.ui.desenhar_fundo_menu(screen)
        self.game.ui.manager.draw_ui(screen)

        grid_data = {
            'grid': self.game.shared_data.get('grid'),
            'layout': self.game.shared_data.get('layout'),
            'h_pos': self.game.shared_data.get('h_pos'),
            'e_pos': self.game.shared_data.get('e_pos'),
        }
        self.game.ui.desenhar_preview_mapa(screen, grid_data)
        


class GeradorNivelState(State):
   def enter(self):
        nivel = self.game.shared_data.get('nivel_atual', 1)
        self.game.ui.desenhar_tela_carregamento(self.game.screen, nivel)

        config_topo, config_pop = self.game.balancer.calcular_dificuldade(nivel)

        sucesso = False
        tentativas_globais = 0

        grid, _, meta, _ = gerar_mapa_valido(config_topo)

        while not sucesso and tentativas_globais < 6: 

            tentativas_globais += 1
            config_topo, config_pop = self.game.balancer.andar_seguranca(config_topo, config_pop, tentativas_globais)
            resultado_ia = tentar_distribuicoes_validas(grid, meta, config_pop)
            
            if resultado_ia and resultado_ia[0] is not None:
                
                layout, h_pos, e_pos, _, _ = resultado_ia
                self.game.shared_data.update({
                    'grid': grid,
                    'meta': meta, 
                    'layout': layout,
                    'h_pos': h_pos,
                    'e_pos': e_pos
                    }
                )
                sucesso = True

        if  sucesso :
            self.game.change_state(JogandoState(self.game))
        else:
            self.game.change_state(EstadoMenuInicial(self.game))


class JogandoState(State):
    def enter(self):
        self.game.shared_data['status_jogo'] = "PLAYING" 
        self.world = World()
        self._construir_fase()
        
        self.mapa_acoes = {
            Acao.PAUSA: self._pausar_jogo,
            Acao.CHEAT_PROXIMO_NIVEL: self._avancar_nivel,
            Acao.ZOOM_IN: self._zoom_in,
            Acao.ZOOM_OUT: self._zoom_out
        }
        
        self.mapa_transicoes = {
            "GAME_OVER": self._transicao_derrota,
            "VICTORY": self._transicao_vitoria
        }

    def _construir_fase(self):
        factory = EntityFactory(self.world)
        factory.preparar_jogo(self.game.shared_data)
        
        self.move_sys, self.render_sys = factory.preparar_sistemas(
            self.game.shared_data, 
            self.game.screen, 
            self.game.ui
        )

    def handle_event(self, event):
        acao = self.game.im.traduzir_evento_discreto(event)
        comando = self.mapa_acoes.get(acao)
        if comando:
            comando()

    def update(self, time_delta):

        self.game.shared_data['time_delta'] = time_delta
        dx, dy = self.game.im.obter_movimento_continuo()
        self.game.shared_data['input_movimento'] = (dx, dy)  
        self.world.process()
        self._verificar_fim_de_jogo()

    def _verificar_fim_de_jogo(self):
        status_atual = self.game.shared_data.get('status_jogo', "PLAYING")
        comando_transicao = self.mapa_transicoes.get(status_atual)
        if comando_transicao:
            comando_transicao()

    def _transicao_derrota(self):
        self.game.shared_data['estado_jogo_salvo'] = self 
        self.game.change_state(DerrotaState(self.game))

    def _transicao_vitoria(self):
        self.game.shared_data['estado_jogo_salvo'] = self 
        nivel_atual = self.game.shared_data.get('nivel_atual', 1)
        
        if MechanicsRules.verificar_ultimo_andar_concluido(nivel_atual):
            self.game.change_state(VitoriaState(self.game))
        else:
            self.game.change_state(AndarConcluidoState(self.game))

    def _pausar_jogo(self):
        self.game.shared_data['estado_jogo_salvo'] = self
        self.game.estado_atual = PauseState(self.game)
        self.game.estado_atual.enter()

    def _avancar_nivel(self):
        self.game.shared_data['nivel_atual'] = self.game.shared_data.get('nivel_atual', 1) + 1
        self.game.change_state(GeradorNivelState(self.game))

    def _zoom_in(self):
        self.render_sys.aplicar_zoom(1)

    def _zoom_out(self):
        self.render_sys.aplicar_zoom(-1)


class PauseState(State):
    def enter(self):
        self.mapa_acoes = {
            Acao.PAUSA: self._despausar,
            Acao.REINICIAR: self._reiniciar_partida,
            Acao.VOLTAR: self._voltar_menu_topologia
        }

    def handle_event(self, event):
        acao = self.game.im.traduzir_evento_discreto(event)
        comando = self.mapa_acoes.get(acao)
        if comando: comando()

    def _despausar(self):
        self.game.estado_atual = self.game.shared_data['estado_jogo_salvo']

    def _reiniciar_partida(self):
        self.game.change_state(JogandoState(self.game))

    def _voltar_menu_topologia(self):
        self.game.change_state(EstadoTopologia(self.game))

    def draw(self, screen):
        self.game.shared_data['estado_jogo_salvo'].draw(screen)
        self.game.ui.desenhar_tela_pausa(screen)


class AndarConcluidoState(State):
    def enter(self):
        self.mapa_acoes = {
            Acao.CONFIRMAR: self._descer_proximo_andar,
            Acao.VOLTAR: self._voltar_menu_inicial
        }

    def handle_event(self, event):
        acao = self.game.im.traduzir_evento_discreto(event)
        comando = self.mapa_acoes.get(acao)
        if comando: comando()

    def _descer_proximo_andar(self):
        nivel_atual = self.game.shared_data.get('nivel_atual', 1)
        self.game.shared_data['nivel_atual'] = nivel_atual + 1
        self.game.change_state(GeradorNivelState(self.game))

    def _voltar_menu_inicial(self):
        self.game.change_state(EstadoMenuInicial(self.game))

    def draw(self, screen):
        if 'estado_jogo_salvo' in self.game.shared_data:
            self.game.shared_data['estado_jogo_salvo'].draw(screen)
        
        nivel_atual = self.game.shared_data.get('nivel_atual', 1)
        self.game.ui.desenhar_tela_andar_concluido(screen, nivel_atual)


class VitoriaState(State):
    def enter(self):
        self.mapa_acoes = {
            Acao.CONFIRMAR: self._iniciar_modo_infinito,
            Acao.VOLTAR: self._voltar_menu_inicial
        }

    def handle_event(self, event):
        acao = self.game.im.traduzir_evento_discreto(event)
        comando = self.mapa_acoes.get(acao)
        if comando: comando()

    def _iniciar_modo_infinito(self):
        nivel_atual = self.game.shared_data.get('nivel_atual', 1)
        self.game.shared_data['nivel_atual'] = nivel_atual + 1
        self.game.change_state(GeradorNivelState(self.game))

    def _voltar_menu_inicial(self):
        self.game.change_state(EstadoMenuInicial(self.game))

    def draw(self, screen):
        if 'estado_jogo_salvo' in self.game.shared_data:
            self.game.shared_data['estado_jogo_salvo'].draw(screen)
        self.game.ui.desenhar_tela_vitoria(screen)


class DerrotaState(State):
    def enter(self):
        self.mapa_acoes = {
            Acao.VOLTAR: self._voltar_menu_topologia,
            Acao.REINICIAR: self._reiniciar_partida
        }

    def handle_event(self, event):
        acao = self.game.im.traduzir_evento_discreto(event)
        comando = self.mapa_acoes.get(acao)
        if comando: comando()

    def _voltar_menu_topologia(self):
        self.game.change_state(EstadoTopologia(self.game))

    def _reiniciar_partida(self):
        self.game.change_state(JogandoState(self.game))

    def draw(self, screen):
        self.game.ui.desenhar_tela_derrota(screen)







