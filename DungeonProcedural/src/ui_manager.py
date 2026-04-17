# src/ui_manager.py
import pygame
import pygame_gui
from src.sprite_loader import SPRITES, SpriteLoader
from src.rules import UIRules
from src.components import Tiles
from src.constants import Cores, Textos, Layout, UI_CONFIG

class GameUIManager:
    def __init__(self, screen_size):
        self.manager = pygame_gui.UIManager(screen_size)
        self.elementos_fase_top = []
        self.elementos_fase_pop = []
        self.mapa_eventos_sliders = {}

        self.labels_topologia = {}
        self.sliders_topologia = {}
        self.prefixos_topologia = {}
        
        self.labels_populacao = {}
        self.sliders_populacao = {}
        self.prefixos_população = {}    
        
        self._fontes = {
            'sprites': pygame.font.SysFont(None, 16),
            'titulo': pygame.font.SysFont(None, 72),
            'sub': pygame.font.SysFont(None, 36),
            'hud': pygame.font.SysFont(None, 28)
        }

        self._load_legend_sprites()
        self._hud_cache_superficies = []
        self._hud_cache_dados_antigos = None
        self._zoom_cache = 1.0
        self._image_cache = {}
        
    
    def limpar_interface(self):
        self.manager.clear_and_reset()
    
    def _criar_label(self, rect_pos, rect_size, texto):
        return pygame_gui.elements.UILabel(relative_rect=pygame.Rect(rect_pos, rect_size), text=texto, manager=self.manager)

    def _criar_botao(self, rect_pos, rect_size, texto):
        return pygame_gui.elements.UIButton(relative_rect=pygame.Rect(rect_pos, rect_size), text=texto, manager=self.manager)

    def _criar_slider(self, rect_pos, rect_size, valor_inicial, limite):
        return pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(rect_pos, rect_size), start_value=valor_inicial, value_range=limite, manager=self.manager)

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self, screen):
        self.manager.draw_ui(screen)

    def processar_eventos_base(self, event):
        self.manager.process_events(event)

    def verificar_cliques_botoes(self, event, mapa_botoes):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            comando = mapa_botoes.get(event.ui_element)
            if comando:
                comando()

    def processar_eventos_sliders(self, event):
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            slider_movido = event.ui_element
            comando = self.mapa_eventos_sliders.get(slider_movido)
            if comando:
                comando(slider_movido)
        
    # ==========================================
    # TELAS DO MENU
    # ==========================================

    def build_menu_inicial(self):
        centro_x = self.manager.window_resolution[0] // 2 
        self.lbl_titulo = self._criar_label((centro_x - 150, 100), (300, Layout.BTN_ALTURA), Textos.TITULO_JOGO)
        self.lbl_titulo.text_colour = Cores.TITULO
        self.lbl_titulo.rebuild() 
        
        self.btn_novo_jogo = self._criar_botao((centro_x - (Layout.BTN_LARGURA//2), 200), (Layout.BTN_LARGURA, Layout.BTN_ALTURA), Textos.BTN_NOVO_JOGO)
        self.btn_criativo = self._criar_botao((centro_x - (Layout.BTN_LARGURA//2), 270), (Layout.BTN_LARGURA, Layout.BTN_ALTURA), Textos.BTN_CRIATIVO)
        self.btn_sair = self._criar_botao((centro_x - (Layout.BTN_LARGURA//2), 340), (Layout.BTN_LARGURA, Layout.BTN_ALTURA), Textos.BTN_SAIR)

    def preparar_fase_criativo(self):
        self.limpar_interface()
        self._build_fase_top()
        self._build_fase_pop()
        self.show_fase_top()

    def _load_legend_sprites(self):
        loader = SpriteLoader()
        self.legendas_menu = [(nome, loader.get_sprite(nome)) for nome in SPRITES.keys()]

    # ==========================================
    # MODO CRIATIVO
    # ==========================================
    
     # ESTADO TOPOLOGIA
    def show_fase_top(self):
        for el in self.elementos_fase_pop: el.hide()
        for el in self.elementos_fase_top: el.show()
        self.btn_avancar.hide() 

    def _build_fase_top(self):
        self.lbl_titulo_topo = self._criar_label((150, 30), (300, 30), Textos.TOPO_TITULO)
        self.elementos_fase_top = [self.lbl_titulo_topo]

        y_offset = 70
        for id_tec, cfg in UI_CONFIG.TOPOLOGIA_SLIDERS.items():
            lbl = self._criar_label((cfg['lbl_x'], y_offset), (cfg['lbl_w'], 30), f"{cfg['texto']}: {cfg['val']}")
            sld = self._criar_slider((240, y_offset), (200, 30), cfg['val'], cfg['range'])
            
            self.labels_topologia[id_tec] = lbl
            self.sliders_topologia[id_tec] = sld
            self.prefixos_topologia[id_tec] = cfg['texto']
            self.elementos_fase_top.extend([lbl, sld])
            self.mapa_eventos_sliders[sld] = self._atualizar_texto_slider_topologia
            y_offset += 40

        self.btn_gerar_topologia = self._criar_botao((200, y_offset + 10), (Layout.BTN_LARGURA, Layout.BTN_ALTURA_PEQ), Textos.TOPO_BTN_GERAR)
        self.lbl_tentativas_topo = self._criar_label((100, y_offset + 60), (400, 30), "")
        self.btn_avancar = self._criar_botao((200, y_offset + 100), (Layout.BTN_LARGURA, Layout.BTN_ALTURA_PEQ), Textos.TOPO_BTN_AVANCAR)
        self.btn_avancar.hide() 
        self.elementos_fase_top.extend([self.btn_gerar_topologia, self.lbl_tentativas_topo, self.btn_avancar])

    def mostrar_erro_topologia(self):
        self.lbl_tentativas_topo.set_text("🛑 CRASH EVITADO. Tamanho/Salas inviável!")
        self.btn_avancar.hide()

    def mostrar_sucesso_topologia(self, tentativas):
        self.lbl_tentativas_topo.set_text(f"Topologia OK em {tentativas} tentativa(s)!")
        self.btn_avancar.show()

    def _atualizar_texto_slider_topologia(self, evento_slider):
        for id_tec, sld in self.sliders_topologia.items():
            if evento_slider == sld:
                prefixo = self.prefixos_topologia[id_tec]
                valor = int(sld.get_current_value())
                self.labels_topologia[id_tec].set_text(f"{prefixo}: {valor}")
                break
    
    def get_topologia_config(self):
        return {id_tec: int(sld.get_current_value()) for id_tec, sld in self.sliders_topologia.items()}

    # ESTADO POPULAÇAO

    def show_fase_pop(self):
        for el in self.elementos_fase_top: el.hide()
        for el in self.elementos_fase_pop: el.show()

    def _build_fase_pop(self):
        self.lbl_titulo_pop = self._criar_label((150, 5), (300, 30), Textos.POP_TITULO)
        self.lbl_info_mapa = self._criar_label((50, 30), (500, 30), "Tiles Livres: 0")
        self.elementos_fase_pop = [self.lbl_titulo_pop, self.lbl_info_mapa]
        
        y_offset = 60

        for id_tec, cfg in UI_CONFIG.POPULACAO_SLIDERS.items():
            
            lbl = self._criar_label((cfg['lbl_x'], y_offset), (cfg['lbl_w'], 30), f"{cfg['texto']} : {cfg['val']}")
            sld = self._criar_slider((280, y_offset), (200, 30), cfg['val'], cfg['range'])
            
            self.labels_populacao[id_tec] = lbl
            self.sliders_populacao[id_tec] = sld
            self.prefixos_população[id_tec] = cfg['texto']
            self.elementos_fase_pop.extend([lbl, sld]) 
            self.mapa_eventos_sliders[sld] = self._sincronizar_sliders_automaticamente
            
            y_offset += 30

        self.lbl_analise = self._criar_label((50, y_offset + 5), (500, 30), "Análise: Seguro")
        self.btn_validar = self._criar_botao((200, y_offset + 35), (Layout.BTN_LARGURA, Layout.BTN_ALTURA_PEQ), Textos.POP_BTN_VALIDAR)
        self.btn_jogar = self._criar_botao((60, y_offset + 80), (160, Layout.BTN_ALTURA_PEQ), Textos.POP_BTN_JOGAR)
        self.btn_voltar = self._criar_botao((380, y_offset + 80), (160, Layout.BTN_ALTURA_PEQ), Textos.POP_BTN_VOLTAR)
        
        self.txt_log = pygame_gui.elements.UITextBox(
            html_text="Aguardando validação...", 
            relative_rect=pygame.Rect((50, y_offset + 130), (500, 70)), 
            manager=self.manager
        )

        self.btn_jogar.disable()
        self.elementos_fase_pop.extend([self.lbl_analise, self.btn_validar, self.btn_jogar, self.btn_voltar, self.txt_log])

    def _sincronizar_sliders_automaticamente(self, evento_slider):
        id_tec_alterado = next((id_tec for id_tec, sld in self.sliders_populacao.items() if evento_slider == sld), None)
        if not id_tec_alterado: return


        valor_tentado = int(evento_slider.get_current_value())
        valores_atuais = {id_tec: int(sld.get_current_value()) for id_tec, sld in self.sliders_populacao.items()}
        atualizacoes = UIRules.calcular_sincronizacao_populacao(id_tec_alterado, valor_tentado, valores_atuais)

        for id_tec, novo_valor in atualizacoes.items():
            if id_tec in self.sliders_populacao:
                self.sliders_populacao[id_tec].set_current_value(novo_valor)
                prefixo = self.prefixos_população[id_tec]
                self.labels_populacao[id_tec].set_text(f"{prefixo}: {novo_valor}")
        
        config_atual = self.get_populacao_config() 
        
        seguro, combinacoes_maximo = UIRules.avaliar_risco_ia(config_atual) 
        self.exibir_painel_risco(seguro, combinacoes_maximo)
    
    def get_populacao_config(self):
        return {id_tec: int(sld.get_current_value()) for id_tec, sld in self.sliders_populacao.items()}

    def exibir_painel_risco(self, seguro, combinacoes_maximo):
        if not seguro:
            self.lbl_analise.set_text(f"🛑 RISCO CRÍTICO: {combinacoes_maximo} combinações possíveis. Melhor reduzir!")
            #self.btn_validar.disable()
        else:
            self.lbl_analise.set_text(f"✅ Seguro: Max {combinacoes_maximo} combinações.")
            self.btn_validar.enable()

    def preparar_validacao_ia(self, screen):
        self.btn_validar.set_text("PENSANDO...")
        self.txt_log.set_text("Rodando Simulação de IA. Aguarde...")
        self.draw(screen)
        pygame.display.flip()

    def exibir_resultado_ia(self, sucesso, tentativas, log):
        self.txt_log.set_text("<br>".join(log))
        self.btn_validar.set_text(Textos.POP_BTN_VALIDAR)
        aviso_excesso = next((msg for msg in log if msg.startswith("Aviso:")), None)

        if sucesso:
            self.btn_jogar.enable()
            self.btn_jogar.set_text('JOGAR FASE APROVADA')
            if aviso_excesso:
                self.lbl_info_mapa.set_text(f"⚠️ {aviso_excesso}")
            else:
                self.lbl_info_mapa.set_text(f"✅ Layout Perfeito em {tentativas} tentativas!")
        else:
            self.lbl_info_mapa.set_text("🛑 IMPOSSÍVEL de Vencer! Veja o Log abaixo.")
            self.btn_jogar.disable()
            self.btn_jogar.set_text('FALHA DE LEVEL DESIGN')

    # ==========================================
    # DESENHO DE TELAS 
    # ==========================================

    def desenhar_fundo_menu(self, screen):
        screen.fill(Cores.FUNDO_MENU)

    def _desenhar_fundo_escurecido(self, screen, alpha=180):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha)) 
        screen.blit(overlay, (0, 0))

    def _desenhar_texto_centralizado(self, screen, texto, fonte, cor, pos_y):
        superficie = fonte.render(texto, True, cor)
        centro_x = screen.get_width() // 2
        pos_x = centro_x - superficie.get_width() // 2
        screen.blit(superficie, (pos_x, pos_y))

    def desenhar_tela_carregamento(self, screen, nivel):
        self.desenhar_fundo_menu(screen)
        fonte = pygame.font.SysFont(None, 48)
        self._desenhar_texto_centralizado(screen, f"GERANDO NÍVEL {nivel}...", fonte, Cores.TITULO, screen.get_height() // 2)
        pygame.display.flip() 

    def desenhar_tela_pausa(self, screen):
        self._desenhar_fundo_escurecido(screen, alpha=150)
        self._desenhar_texto_centralizado(screen, Textos.TELA_PAUSA, self._fontes['titulo'], (255, 255, 255), 250)
        self._desenhar_texto_centralizado(screen, Textos.MSG_PAUSA, self._fontes['sub'], Cores.SUBTITULO, 330)

    def desenhar_tela_derrota(self, screen):
        self._desenhar_fundo_escurecido(screen, alpha=180)
        self._desenhar_texto_centralizado(screen, Textos.TELA_GAME_OVER, self._fontes['titulo'], Cores.ERRO_ALERTA, 250)
        self._desenhar_texto_centralizado(screen, Textos.MSG_GAME_OVER, self._fontes['sub'], Cores.SUBTITULO, 350)

    def desenhar_tela_vitoria(self, screen):
        self._desenhar_fundo_escurecido(screen, alpha=210)
        fonte_vitoria = pygame.font.SysFont(None, 45)
        self._desenhar_texto_centralizado(screen, Textos.TELA_VITORIA, fonte_vitoria, Cores.DESTAQUE_VITORIA, 140)
        self._desenhar_texto_centralizado(screen, Textos.MSG_VITORIA_1, self._fontes['sub'], Cores.SUCESSO, 260)
        self._desenhar_texto_centralizado(screen, Textos.MSG_VITORIA_2, self._fontes['sub'], (255, 255, 255), 300)
        self._desenhar_texto_centralizado(screen, Textos.MSG_CONTINUAR, self._fontes['sub'], (150, 150, 150), 500)

    def desenhar_tela_andar_concluido(self, screen, nivel):
        self._desenhar_fundo_escurecido(screen, alpha=190)
        self._desenhar_texto_centralizado(screen, f"ANDAR {nivel} CONCLUÍDO!", self._fontes['titulo'], Cores.INFO, 230)
        self._desenhar_texto_centralizado(screen, "Pressione [ESPAÇO] para descer mais fundo...", self._fontes['sub'], Cores.SUBTITULO, 320)

    # ==========================================
    # DESENHOS AUXILIARES 
    # ==========================================

    def draw_legend(self, screen):
        start_x, start_y, espaco_x, espaco_y = 50, 480, 85, 55
        for i, (nome, img) in enumerate(self.legendas_menu):
            x, y = start_x + ((i % 6) * espaco_x), start_y + ((i // 6) * espaco_y)
            screen.blit(img, (x, y))
            texto_surf = self._fontes['sprites'].render(nome, True, Cores.TEXTO_PADRAO)
            screen.blit(texto_surf, (x + 16 - (texto_surf.get_width() // 2), y + 36))

    def desenhar_hud(self, screen, lista_strings):
        fundo_rect = pygame.Rect(0, 0, screen.get_width(), 40)
        pygame.draw.rect(screen, (20, 20, 20, 200), fundo_rect)

        pos_x = 30
        for texto in lista_strings:
            cor = Cores.TEXTO_PADRAO
            
            if texto.startswith("HP:"):
                try:
                    valores = texto.replace("HP: ", "").split("/")
                    atual, maximo = int(valores[0]), int(valores[1])
                    if atual < maximo:
                        cor = Cores.ERRO_ALERTA 
                except:
                    pass 

            surf = self._fontes['hud'].render(texto, True, cor)
            screen.blit(surf, (pos_x, 10))
            pos_x += surf.get_width() + 60

    def desenhar_cenario(self, screen, camera_offset,  objetos_visiveis):
        screen.fill((0, 0, 0))
        for img, x, y in objetos_visiveis:
            screen.blit(img, (x + camera_offset[0], y + camera_offset[1]))
    
    def _obter_imagem_escalada(self, imagem_original, tamanho):
        chave = (imagem_original, tamanho)
        if chave not in self._image_cache:
            self._image_cache[chave] = pygame.transform.scale(imagem_original, (tamanho, tamanho))
        return self._image_cache[chave]

    def desenhar_preview_mapa(self, screen, grid_data):

        grid = grid_data.get('grid')
        if not grid: 
            return
            
        layout = grid_data.get('layout')
        h_pos = grid_data.get('h_pos')
        e_pos = grid_data.get('e_pos')
        
        rows, cols = len(grid), len(grid[0])

        margem_topo_mapa = 420
        margem_lateral = 20
        max_w = screen.get_width() - (margem_lateral * 2)
        max_h = screen.get_height() - margem_topo_mapa - 10 
        
        if max_h < 50: max_h = 150 
    
        map_surface = pygame.Surface((max_w, max_h))
        map_surface.fill(Cores.FUNDO_MENU) 

        tile_size = min(max_w // cols, max_h // rows)
        if tile_size < 1: tile_size = 1

        start_x = (max_w - (cols * tile_size)) // 2
        start_y = max(0, (max_h - (rows * tile_size)) // 2)
        
        for y, row in enumerate(grid):
            for x, val in enumerate(row):
                cor = Cores.PAREDE if val == Tiles.WALL else Cores.CHAO
                rect = pygame.Rect(start_x + x * tile_size, start_y + y * tile_size, tile_size, tile_size)
                pygame.draw.rect(map_surface, cor, rect)
        
        if layout:
            for (x, y), item in layout.items():
                cor = Cores.ITENS.get(item, (255, 255, 255))
                margem = 1 if tile_size > 2 else 0
                rect = pygame.Rect(start_x + x * tile_size + margem, start_y + y * tile_size + margem, 
                                   tile_size - (margem*2), tile_size - (margem*2))
                pygame.draw.rect(map_surface, cor, rect)
                
        if h_pos:
            margem = 1 if tile_size > 2 else 0
            rect = pygame.Rect(start_x + h_pos[0] * tile_size + margem, start_y + h_pos[1] * tile_size + margem, 
                               tile_size - (margem*2), tile_size - (margem*2))
            pygame.draw.rect(map_surface, Cores.HEROI, rect)
            
        if e_pos:
            margem = 1 if tile_size > 2 else 0
            rect = pygame.Rect(start_x + e_pos[0] * tile_size + margem, start_y + e_pos[1] * tile_size + margem, 
                               tile_size - (margem*2), tile_size - (margem*2))
            pygame.draw.rect(map_surface, Cores.SAIDA, rect)

        screen.blit(map_surface, (margem_lateral, margem_topo_mapa))