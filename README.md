# IA

# Cake Sort Puzzle AI Solver

## Project Overview

This project implements an AI solver for a one-player solitaire-style puzzle game inspired by “Cake Sort Puzzle.” The game involves stacking colored cake slices onto plates according to specific rules, aiming to group matching colors and clear full stacks.

The application supports both:

- **Human mode**: Play the game manually and request hints.
- **Bot mode**: Let the computer solve the puzzle using search algorithms.

---

## Implemented Search Algorithms

We implemented two heuristic search methods:

- **Greedy Best-First Search**  
  Selects moves that give the highest immediate heuristic value. Fast but short-sighted.

- **A\* Search**  
  Combines actual cost with heuristic estimates for better long-term planning. More accurate but slower.

---

## Benchmarking & Evaluation

We measure and compare each algorithm based on:

- Total score
- Steps taken
- Time elapsed
- Peak memory usage
- Number of states explored

All results are saved automatically in the `results/` folder.

---

## Project Structure

```
.
├── game/
│   ├── core.py            # Game logic
│   ├── solver.py          # Greedy and A* logic
│   ├── models.py          # CakeSlice, Plate classes
│   ├── utils.py           # Heuristic function, file loaders
│   └── levels/            # Level files (text-based)
├── main.py                # Game runner with GUI
├── menu.py                # Menu interface with bot selector
├── benchmark_level.py     # Script for evaluating solvers
├── metrics_collector.py   # Tracks time, memory, steps, score
├── results/               # Benchmark output files
```

---

## Running the Game

### Human Mode

```bash
python menu.py
```

- Click "Start Game" to play manually.
- Click "Bot Hint" for help from the AI.

### 🤖 Bot Mode (in game)

- In the menu, click "Choose Bot".
- Select **Greedy** or **A\*** and watch the AI play.

### Benchmark Mode (metrics & results)

```bash
python benchmark_level.py game/levels/level1.txt --algorithm greedy
python benchmark_level.py game/levels/level1.txt --algorithm a*
```

---


