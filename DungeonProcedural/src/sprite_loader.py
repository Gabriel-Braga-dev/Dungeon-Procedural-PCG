# src/sprite_loader.py
import pygame

TILE_SIZE = 32
TILE_SIZE_ORIGINAL = 16

SPRITES = {
    # 1. TIPO POSIÇÃO: Corta da folha padrão
    'hero':       {'pos': (0, 2)},
    'wall':       {'pos': (0, 0)},
    'wall_inner': {'pos': (2, 0)},
    'floor':      {'pos': (2, 2)},
    'dragon':     {'pos': (0, 1)},
    'potion':     {'pos': (1, 1)},
    'key':        {'pos': (2, 1)},
    'door':       {'pos': (1, 0)},
    'treasure':   {'pos': (1, 2)},
    
    # 2. TIPO BASE: Gera imagem dinamicamente (Recolorindo)
    'start': {'base': 'floor', 'color': (60, 60, 60),   'blend': pygame.BLEND_RGB_ADD},
    'exit':  {'base': 'floor', 'color': (100, 100, 100), 'blend': pygame.BLEND_RGB_SUB},
    
    # 3. TIPO ARQUIVO (EXEMPLO FUTURO): Lê uma imagem que está num arquivo separado!
    # 'trap': {'file': 'assets/sprites/trap_spikes.png'},
    # 'boss': {'file': 'assets/sprites/boss_sheet.png', 'pos': (0, 0), 'tamanho_original': 64}
}

class SpriteLoader:
    def __init__(self, default_sheet_path="assets/sprites/PCG-sprites-dungeon.png"):
        self.default_sheet_path = default_sheet_path
        self.tile_size_original = TILE_SIZE_ORIGINAL
        self._cache_imagens = {}
        self._cache_sheets = {} 
        self._carregar_todos_os_sprites()

    def _obter_sheet(self, caminho_arquivo):
        """Busca o spritesheet no cache ou carrega do disco se for novo."""
        if caminho_arquivo not in self._cache_sheets:
            try:
                self._cache_sheets[caminho_arquivo] = pygame.image.load(caminho_arquivo).convert_alpha()
            except FileNotFoundError:
                raise FileNotFoundError(f"Erro Crítico: Arquivo de imagem não encontrado -> {caminho_arquivo}")
        return self._cache_sheets[caminho_arquivo]

    def _carregar_todos_os_sprites(self):
        """Lê o dicionário e constrói TODAS as imagens automaticamente baseando-se no tipo de config."""
        
        # PASSO 1: Carregar imagens brutas (Arquivos separados ou cortes de spritesheet)
        for nome, config in SPRITES.items():
            if 'file' in config and 'pos' not in config:
                # É uma imagem única separada (ex: trap.png)
                img = self._obter_sheet(config['file'])
                self._cache_imagens[nome] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                
            elif 'pos' in config:
                # É um recorte de um spritesheet (padrão ou arquivo externo se fornecido)
                caminho = config.get('file', self.default_sheet_path)
                sheet = self._obter_sheet(caminho)
                
                # Suporta tamanhos diferentes (ex: Boss 64x64)
                tamanho = config.get('tamanho_original', self.tile_size_original)
                self._cache_imagens[nome] = self._cortar_sprite(sheet, config['pos'][0], config['pos'][1], tamanho)

        # PASSO 2: Gerar os sprites derivados (que precisam que as bases do Passo 1 já existam)
        for nome, config in SPRITES.items():
            if 'base' in config:
                if config['base'] not in self._cache_imagens:
                    raise ValueError(f"Sprite base '{config['base']}' para '{nome}' não foi encontrado!")
                
                img_base = self._cache_imagens[config['base']].copy()
                img_base.fill(config['color'], special_flags=config['blend'])
                self._cache_imagens[nome] = img_base

    def get_sprite(self, nome_sprite):
        """Oculta completamente a complexidade do resto do jogo."""
        if nome_sprite not in self._cache_imagens:
            raise ValueError(f"Sprite '{nome_sprite}' não configurado no dicionário SPRITES.")
        return self._cache_imagens[nome_sprite]

    def _cortar_sprite(self, sheet, col, row, tamanho_corte):
        """Corta de uma folha específica com tamanho dinâmico."""
        rect = pygame.Rect(col * tamanho_corte, row * tamanho_corte, tamanho_corte, tamanho_corte)
        sprite = pygame.Surface((tamanho_corte, tamanho_corte), pygame.SRCALPHA)
        sprite.blit(sheet, (0, 0), rect)
        return pygame.transform.scale(sprite, (TILE_SIZE, TILE_SIZE))