# main.py
import pygame
from src.ui_manager import GameUIManager
from src.states import EstadoMenuInicial
from src.input_manager import InputManager
from src.rules import LevelBalancer

LARGURA_TELA = 600
ALTURA_TELA = 600
FPS = 30

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA)) 
        pygame.display.set_caption("Dungeon Procedural")
        self.clock = pygame.time.Clock()
        
        self.ui = GameUIManager((LARGURA_TELA, ALTURA_TELA))
        self.im = InputManager() 
        self.balancer = LevelBalancer()

        self.shared_data = {} 
        self.estado_atual = None

        self.change_state(EstadoMenuInicial(self))
        self.running = True

    def change_state(self, novo_estado):
        if self.estado_atual:
            self.estado_atual.exit()
        self.estado_atual = novo_estado
        self.estado_atual.enter()

    def run(self):
        while self.running:
            time_delta = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.running = False
                self.estado_atual.handle_event(event)

            self.estado_atual.update(time_delta)
            self.estado_atual.draw(self.screen)
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    Game().run()