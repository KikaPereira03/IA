import pygame
from typing import List, Tuple, Optional
from game.utils import load_level_and_scoreboard
from game.utils import save_score_in_level_file
from dataclasses import dataclass
import os

@dataclass
class CakeLayer:
    color: str
    size: int

    def __str__(self):
        return f"{self.color}{self.size}"

class Tube:
    def __init__(self, max_capacity: int = 6):
        self.layers: List[CakeLayer] = []
        self.max_capacity = max_capacity
    
    def can_add(self, layer: CakeLayer) -> bool:
        return (len(self.layers) < self.max_capacity and 
                (self.is_empty() or self.top_layer().color == layer.color))
    
    def add_layer(self, layer: CakeLayer) -> bool:
        if self.can_add(layer):
            self.layers.append(layer)
            return True
        return False
    
    def add_layers_any_color(self, layers: List[CakeLayer]):
        for layer in layers:
            if layer and len(self.layers) < self.max_capacity:
                self.layers.append(layer)

    def clear_if_full_same_color(self) -> bool:
        if len(self.layers) == self.max_capacity:
            first_color = self.layers[0].color
            if all(layer.color == first_color for layer in self.layers):
                self.layers = []  # limpa todas as camadas
                return True  # indica que limpou
        return False


    def remove_layer(self, index: int) -> Optional[CakeLayer]:
        if -len(self.layers) <= index < len(self.layers):
            return self.layers.pop(index)
        return None

    
    def top_layer(self) -> Optional[CakeLayer]:
        return self.layers[-1] if self.layers else None
    
    def is_empty(self) -> bool:
        return len(self.layers) == 0
    
    def is_full(self) -> bool:
        return len(self.layers) == self.max_capacity
    
    def is_complete(self) -> bool:
        if not self.is_full():
            return False
        first_color = self.layers[0].color if self.layers else None
        return all(layer.color == first_color for layer in self.layers)
    
    def __str__(self):
        return " ".join(str(layer) for layer in self.layers)

class CakeGame:
    def __init__(self, width: int = 5, height: int = 4, max_capacity: int = 6):
        self.width = width
        self.height = height
        self.max_capacity = max_capacity
        self.tubes: List[Tube] = [Tube(max_capacity) for _ in range(width * height)]
        self.moves = 0
        self.selected_tube = None
        self.selected_layer_pos = None
        self.score = 0
        self.base_score = 0  

    
    def initialize_level(self, level_file: str):
        self.level_number = int(level_file.replace("game/levels/level", "").replace(".txt", ""))
        self.tubes = [Tube(self.max_capacity) for _ in range(self.width * self.height)]
        self.moves = 0
        
        try:
            grid_lines, self.scoreboard = load_level_and_scoreboard(level_file.replace(".txt", "").replace("level", "lvl"))

            for line in grid_lines:
                if line.startswith('#') or not line.strip():
                    continue

                parts = line.strip().split(':')
                if len(parts) < 2:
                    continue

                tube_idx, layers_str = parts[0], parts[1]
                tube = self.tubes[int(tube_idx)]

                for layer_str in layers_str.split():
                    if not layer_str:
                        continue
                    color = layer_str[0].upper()
                    size = int(layer_str[1:]) if len(layer_str) > 1 else 1
                    tube.add_layer(CakeLayer(color, size))
        except FileNotFoundError:
            print(f"Error: Level file {level_file} not found")
    
    def move_layer(self, from_idx: int, layer_pos: int, to_idx: int) -> bool:
        if from_idx == to_idx:
            return False
        if not (0 <= from_idx < len(self.tubes) and 0 <= to_idx < len(self.tubes)):
            return False
            
        from_tube = self.tubes[from_idx]
        to_tube = self.tubes[to_idx]
        
        layer = from_tube.remove_layer(layer_pos)
        if layer is None:
            return False
            
        if to_tube.add_layer(layer):
            self.moves += 1
            return True
        else:
            from_tube.layers.insert(layer_pos, layer)
            return False
    
    def is_solved(self) -> bool:
        return all(tube.is_complete() or tube.is_empty() for tube in self.tubes)
    
    def get_state_hash(self) -> str:
        return "|".join(str(tube) for tube in self.tubes)
    
    def get_adjacent_tubes(self, tube_idx: int) -> List[int]:
        row = tube_idx // self.width
        col = tube_idx % self.width
        adjacent = []
        
        if row > 0:
            adjacent.append(tube_idx - self.width)
        if row < self.height - 1:
            adjacent.append(tube_idx + self.width)
        if col > 0:
            adjacent.append(tube_idx - 1)
        if col < self.width - 1:
            adjacent.append(tube_idx + 1)
            
        return adjacent
    
    def merge_all_possible_layers(self):
        print("🔁 A correr merge_all_possible_layers()")
        merge_happened = True
        cycle_count = 0  # proteção contra ciclos infinitos

        while merge_happened:
            print("🔄 Novo ciclo de merge...")
            merge_happened = False
            cycle_count += 1

            if cycle_count > 100:
                print("❌ Merge parou: ciclo infinito evitado!")
                break

            for i, tube_a in enumerate(self.tubes):
                for j in self.get_adjacent_tubes(i):
                    if i == j:
                        continue
                    tube_b = self.tubes[j]

                    # Verifica se têm cores em comum, mesmo que não no topo
                    colors_a = [layer.color for layer in tube_a.layers]
                    colors_b = [layer.color for layer in tube_b.layers]
                    common_colors = set(colors_a) & set(colors_b)

                    for color in common_colors:
                        # Junta todas as camadas dessa cor dos dois tubos
                        layers_a = [l for l in tube_a.layers if l.color == color]
                        layers_b = [l for l in tube_b.layers if l.color == color]
                        total = layers_a + layers_b

                        # Decide para onde mover
                        if len(layers_a) >= len(layers_b):
                            dest = tube_a
                            src = tube_b
                        else:
                            dest = tube_b
                            src = tube_a

                        # Espaço disponível
                        space = dest.max_capacity - len(dest.layers)
                        to_add = total[:space]

                        if to_add:
                            # Remove as do src
                            count = 0
                            for layer in list(src.layers):
                                if layer.color == color and count < len(to_add):
                                    src.layers.remove(layer)
                                    count += 1

                            # Adiciona ao dest
                            dest.layers.extend(to_add[:count])
                            merge_happened = True

        # Após merges, remove pratos completos
        for tube in self.tubes:
            if len(tube.layers) == 6 and all(l.color == tube.layers[0].color for l in tube.layers):
                print(f"💥 Removido prato cheio de {tube.layers[0].color}")

                # ✅ Adiciona 100 pontos e guarda imediatamente no ficheiro
                if hasattr(self, 'score'):
                    self.score += 100
                    if (self.score - self.base_score) >= 200 and self.level_number < 3:
                        next_level = self.level_number + 1
                        print(f"🎯 Score chegou a {self.score}! A mudar para o nível {next_level}")
                        self.ui_level_switch(next_level)

                else:
                    self.score = 100

                print(f"💾 A guardar score no nível {self.level_number} para {getattr(self, 'player_name', 'Tropa')} com {self.score} pontos")
                
                level = int(self.level_number) if hasattr(self, 'level_number') else 1
                if hasattr(self, "player_name"):
                    save_score_in_level_file(level, (self.player_name, self.score))
                else:
                    save_score_in_level_file(level, ("Tropa", self.score))

                # Animação
                if hasattr(self, 'ui_callback') and callable(self.ui_callback):
                    self.ui_callback(self.tubes.index(tube))
                tube.layers.clear()

                # ✅ Podes deixar este print, mas sem guardar novamente
                if self.is_solved():
                    print("✅ Puzzle resolvido!")


    
    def try_merge_tubes(self, idx1, idx2):
        tube1 = self.tubes[idx1]
        tube2 = self.tubes[idx2]

        if tube1.is_empty() and tube2.is_empty():
            return False

        # Agrupar todas as fatias por cor
        all_layers = tube1.layers + tube2.layers
        color_groups = {}
        for layer in all_layers:
            color_groups.setdefault(layer.color, []).append(layer)

        # Ordenar as cores pela quantidade de fatias (maior primeiro)
        sorted_colors = sorted(color_groups.items(), key=lambda x: len(x[1]), reverse=True)

        # Distribuir pelas duas células
        new_tube1 = []
        new_tube2 = []

        for color, layers in sorted_colors:
            for layer in layers:
                if len(new_tube1) < tube1.max_capacity:
                    new_tube1.append(layer)
                elif len(new_tube2) < tube2.max_capacity:
                    new_tube2.append(layer)
                else:
                    # Não há espaço suficiente para reorganizar
                    return False

        # Só faz merge se algo mudar
        if new_tube1 == tube1.layers and new_tube2 == tube2.layers:
            return False

        # Aplicar a nova organização
        tube1.layers = new_tube1
        tube2.layers = new_tube2
        return True




    # ✅ Função nova para mover todas as fatias
    def move_all_layers(self, from_idx: int, to_idx: int) -> bool:
        """Move todas as fatias possíveis do tubo origem para o tubo destino."""
        if from_idx == to_idx:
            return False

        from_tube = self.tubes[from_idx]
        to_tube = self.tubes[to_idx]

        if from_tube.is_empty() or to_tube.is_full():
            return False

        layers_to_move = from_tube.layers[::-1]
        space_available = to_tube.max_capacity - len(to_tube.layers)

        layers_to_transfer = []
        for layer in layers_to_move:
            if len(layers_to_transfer) < space_available:
                layers_to_transfer.append(layer)
            else:
                break

        for layer in reversed(layers_to_transfer):
            to_tube.add_layer(layer)

        from_tube.layers = from_tube.layers[:-len(layers_to_transfer)]
        self.moves += 1
        return True
    
        