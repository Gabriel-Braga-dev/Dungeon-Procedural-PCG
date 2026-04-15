# src/input_manager.py
import pygame
from enum import auto

class Acao:
    CIMA = "CIMA"
    BAIXO = "BAIXO"
    ESQUERDA = "ESQUERDA"
    DIREITA = "DIREITA"
    PAUSA = "PAUSA"
    CONFIRMAR = "CONFIRMAR"
    VOLTAR = "VOLTAR"
    REINICIAR = "REINICIAR"
    CHEAT_PROXIMO_NIVEL = "CHEAT_PROXIMO_NIVEL"
    ZOOM_IN = auto()
    ZOOM_OUT = auto()

class InputManager:
    def __init__(self):
        self.mapeamento = {
            pygame.K_w: Acao.CIMA,
            pygame.K_UP: Acao.CIMA,
            pygame.K_s: Acao.BAIXO,
            pygame.K_DOWN: Acao.BAIXO,
            pygame.K_a: Acao.ESQUERDA,
            pygame.K_LEFT: Acao.ESQUERDA,
            pygame.K_d: Acao.DIREITA,
            pygame.K_RIGHT: Acao.DIREITA,
            pygame.K_p: Acao.PAUSA,
            pygame.K_SPACE: Acao.CONFIRMAR,
            pygame.K_RETURN: Acao.CONFIRMAR,
            pygame.K_ESCAPE: Acao.VOLTAR,
            pygame.K_r: Acao.REINICIAR,
            pygame.K_n: Acao.CHEAT_PROXIMO_NIVEL 
        }

    def obter_movimento_continuo(self):
  
        teclas = pygame.key.get_pressed()
        dx, dy = 0, 0

        if teclas[pygame.K_w] or teclas[pygame.K_UP]: 
            dy = -1
        elif teclas[pygame.K_s] or teclas[pygame.K_DOWN]: 
            dy = 1
        elif teclas[pygame.K_a] or teclas[pygame.K_LEFT]: 
            dx = -1
        elif teclas[pygame.K_d] or teclas[pygame.K_RIGHT]: 
            dx = 1

        return dx, dy

    def traduzir_evento_discreto(self, event):
       
        if event.type == pygame.KEYDOWN:
            return self.mapeamento.get(event.key, None)
    
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                return Acao.ZOOM_IN
            elif event.y < 0:
                return Acao.ZOOM_OUT
                
        return None 