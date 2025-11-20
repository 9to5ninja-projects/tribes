# Tribes: Ecological Strategy Simulator

A complex ecosystem simulation game featuring dynamic climate, diverse biomes, and detailed predator-prey interactions.

## Features

- **Procedural World Generation**: Creates unique maps with realistic elevation, temperature, and moisture gradients.
- **Dynamic Climate Engine**: Simulates seasons, weather events (storms, droughts), and long-term climate shifts.
- **Complex Ecology**:
  - **Vegetation**: Grows dynamically based on biome and climate conditions.
  - **Herbivores**: 10+ species with unique stats, habitat preferences, and behaviors.
  - **Predators**: 10+ species with complex hunting logic, pack behaviors, and metabolism.
  - **Full Food Chain**: Includes insects, birds (avian), fish (aquatic), and scavengers.
- **Deep Observability**:
  - Track every death (Predation, Starvation, Old Age, Disease, Disaster).
  - View the complete "Food Chain" to see who is eating whom.
  - Real-time population graphs and statistics.
- **SRPG-Style Stats**: Entities use HP, Attack, Defense, and Speed stats for deterministic interactions.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the game:
    ```bash
    python game_ui.py
    ```

## Controls

- **Pan**: Click and drag with the mouse.
- **Zoom**: Mouse wheel.
- **UI**: Use the sidebar to Play/Pause, Step Turns, and view Statistics.
- **Statistics Overlay**: Click "Statistics" to view detailed graphs, food chain matrices, and death reports.

## Development

- `game_controller.py`: Main game loop and state management.
- `game_ui.py`: Pygame-based frontend.
- `events_ecology.py`: Handles birds, fish, insects, and random events.
- `predator_system.py` / `animal_system.py`: Core AI logic for wildlife.
