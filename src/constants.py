# src/constants.py
class Cores:
    # Paleta Principal
    FUNDO_MENU = (50, 50, 60)
    FUNDO_HUD = (20, 20, 25)
    
    # Textos
    TITULO = (0, 255, 255)
    TEXTO_PADRAO = (220, 220, 220)
    SUBTITULO = (200, 200, 200)
    
    # Feedbacks e Avisos
    ERRO_ALERTA = (255, 50, 50)
    SUCESSO = (50, 255, 50)
    DESTAQUE_VITORIA = (255, 215, 0)
    INFO = (50, 200, 255)
    
    # Mini-mapa
    PAREDE = (60, 60, 70)
    CHAO =   (20, 20, 25)
    HEROI =  (0, 200, 255)    
    SAIDA =  (200, 0, 200)    
    ITENS = {
        'dragon':   (255, 50, 50),   
        'potion':   (50, 255, 50),   
        'treasure': (255, 255, 255), 
        'door':     (139, 69, 19),     
        'key':      (200, 200, 0),     
    }

class Textos:
    # Menu Principal
    TITULO_JOGO = "DUNGEON PROCEDURAL"
    BTN_NOVO_JOGO = "NOVA PARTIDA"
    BTN_CRIATIVO = "MODO CRIATIVO"
    BTN_SAIR = "SAIR"
    
    # Textos do Modo Criativo
    TOPO_TITULO = "1. Gerar Topologia do Mapa"
    TOPO_BTN_GERAR = "GERAR TOPOLOGIA"
    TOPO_BTN_AVANCAR = "AVANÇAR ->"
    
    POP_TITULO = "2. Distribuir Elementos"
    POP_BTN_VALIDAR = "DISTRIBUIR E VALIDAR"
    POP_BTN_JOGAR = "JOGAR (Bloqueado)"
    POP_BTN_VOLTAR = "VOLTAR"
    
    # Telas de Estado
    TELA_PAUSA = "PAUSA"
    MSG_PAUSA = "[P] Continuar | [R] Reiniciar | [ESC] Menu"
    
    TELA_GAME_OVER = "GAME OVER"
    MSG_GAME_OVER = "Pressione [R] para Reiniciar ou [ESC]"
    
    TELA_VITORIA = "A MASMORRA FOI CONQUISTADA!"
    MSG_VITORIA_1 = "Você sobreviveu aos andares principais."
    MSG_VITORIA_2 = "Deseja descer para as profundezas infinitas?"
    MSG_CONTINUAR = "[ESPAÇO] continuar  |  [ESC] voltar ao Menu"

class Layout:
    BTN_LARGURA = 200
    BTN_ALTURA = 50
    BTN_ALTURA_PEQ = 40
    TILE_SIZE = 32

class UI_CONFIG:
    # 'id': {'texto apresentado' = z: 'val_inicial': X, 'range': (min, max), 'lbl_x': posX, 'lbl_w': largura}
    TOPOLOGIA_SLIDERS  = {

        'width':     {'texto': 'Tamanho',       'val': 30, 'range': (20, 40), 'lbl_x': 130, 'lbl_w': 100},
        'rooms':     {'texto': 'Qtd Salas',     'val': 15, 'range': (3, 25),  'lbl_x': 110, 'lbl_w': 120},
        'tam_rooms': {'texto': 'Tam. Máx Sala', 'val': 3,  'range': (3, 10),  'lbl_x': 100, 'lbl_w': 130}
    }

    POPULACAO_SLIDERS = {
       
        'dragon':   {'texto': 'Dragões',  'val': 1, 'range': (1, 10), 'lbl_x': 110, 'lbl_w': 160},
        'potion':   {'texto': 'Poções',   'val': 1, 'range': (1, 10), 'lbl_x': 110, 'lbl_w': 160},
        'treasure': {'texto': 'Tesouros', 'val': 1, 'range': (1, 10), 'lbl_x': 110, 'lbl_w': 160},
        'door':     {'texto': 'Portas',   'val': 1, 'range': (1, 10), 'lbl_x': 110, 'lbl_w': 160},
        'key':      {'texto': 'Chaves',   'val': 1, 'range': (1, 10), 'lbl_x': 110, 'lbl_w': 160}
    }

