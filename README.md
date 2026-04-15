# Dungeon-Procedural-PCG
1. Arquitetura do Mapa:
   
  Para atender às restrições topológicas de salas retangulares conectadas por corredores únicos, optou-se por um algoritmo de Spanning Tree (Carving) em vez de Ruído de Perlin ou Wave Function Collapse (WFC).Essa decisão foi tomada, pois algoritmos de ruído criam formas orgânicas demais, dificultando o controle de caminhos, e o WFC, embora excelente para micro-detalhes, exige backtracking oneroso para garantir conectividade macro sem loops. Enquanto que, com carving o algoritmo "escava" corredores de largura 1 a partir de uma sala raiz, validando colisões antes da construção, garantindo uma árvore, em que existe um, e apenas um, caminho entre duas salas. Essa estrutura elimina atalhos e cria "gargalos" estratégicos para o combate. Naturalmente, o algoritmo gera salas com apenas uma conexão, utilizadas como "cofres" para itens valiosos protegidos por portas. No modo de criação é possível escolher o tamanho do mapa, a quantidade de salas e o tamanho das salas, já no modo jogo, o tamanho do mapa e a quantidade de salas crescem em relação ao nível da fase, enquanto o tamanho da sala é fixo.

2. Economia Punitiva e Balanceamento Lógico:
   
  O design do jogo opera sob uma economia 1:1, onde cada recurso é vital para a sobrevivência, em que suas regras de consumo são: O herói possui no máximo 2 HP, em que dragões causam 1 de dano e poções curam 1 de vida; As poções só liberam a passagem se o herói estiver ferido, criando uma dinâmica entre poções e dragões, visto que dois dragões consecutivos matam o herói; E, cada porta consome exatamente 1 chave, sendo que no inicio não se tem nenhuma. A validade do mapa depende da coleta de 100% dos itens, porém, para a IA foram definidos itens relevantes, desconsiderando os tesouros, visto que, eles serão conseguidos sempre que uma porta for aberta. A distribuição estratégica do itens são: Tesouros e portas são alocados em cofres, enquanto dragões e poções são posicionados em corredores estreitos para forçar a interação e as chaves são posicionadas aleatoriamente em qualquer sala. Além disso, para evitar mapas muito custosos, foi estabelecido uma relação que limita o número de itens ativos, garantindo que a complexidade combinatória (2^N), sendo N os itens relevantes, não inviabilize a validação computacional, pois foi observado que quanto maior o mapa maior a exigência. No modo criação é possível escolher de 1 a 10 itens, que estão previamente sincronizados para facilitar a criação, junto com um aviso de risco de combinações excessivas. No modo jogo, o número de itens é aleatório e cresce junto com o nível do mapa até determinado momento, evitando a possibilidade de gerar fases muito demoradas. Nele o numero de poções pode ser 1 a menos que o numero de dragões e o numero de chaves pode ser 1 a mais que o numero de portas, já os tesouros são diretamente relacionado com o numero de portas, podendo ser um pouco menor caso a entrada e a saída estejam trancados.

3. Agente Avaliador - Busca no Espaço de Estados com A*:
   
  A validação do mapa não é um problema de rota (pathfinding comum), mas de Estado de Jogo, em que o agente precisa considerar a posição, o HP atual, o inventário de chaves e os itens restantes. Não foi utilizado uma busca em largura (BFS), pois sofreria com uma explosão combinatória, gerando exaustão de memória. Diante disso, foi implementado o A* com uma Heurística de Busca Gulosa baseada na Distância Manhattan. A IA prioriza o item coletável mais próximo, e, para isso, o agente ignora a saída até que o contador de itens chegue a zero, caso encontre uma porta sem chaves, o caminho é podado.


EXEMPLO DE MAPAS 1:

<p align="center">
   <img src="https://github.com/user-attachments/assets/45cd4f34-f5ba-4e14-a7a6-d1fcba899213"alt="PreviewMap1" width="45%">
  <img src="https://github.com/user-attachments/assets/b5127a59-839c-483f-bece-4ab80fb80f57" alt="Map1inGame"  width="45%">
</p>

EXEMPLO DE MAPAS 2:

<p align="center">
  <img src="https://github.com/user-attachments/assets/6eed3275-d649-4c4d-bef2-5a0a3514b9e1" alt="PreviewMap2" width="45%">
  <img src="https://github.com/user-attachments/assets/b142cf15-1c7a-4ed4-bd80-81ecb1919ddb" alt="Map2inGame" width="45%">
</p>



