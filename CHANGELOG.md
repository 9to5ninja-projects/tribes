# Changelog

All notable changes to this project will be documented in this file.

## [0.16.1] - 2025-11-21
### Fixed
- **Hunt Feedback**: Added a game log message when a hunter tries to hunt but no targets are in range, replacing the browser alert in some cases.

## [0.16.0] - 2025-11-21
### Added
- **Starting Tribe Configuration**: Added options in the New Game dialog to customize the number of starting Gatherers and Hunters.
- **Hunt Target Info**: Hunter target selection dialog now displays the HP and Max HP of potential targets.

### Fixed
- **Gather Action**: Fixed an issue where the "Gather" button would not work despite being on a resource tile. Removed unnecessary confirmation dialog for single-resource gathering.
- **Hunt Messaging**: Improved game log messages for hunting actions. Now explicitly states the target's name and remaining HP if the attack was not fatal.
- **Crash Fixes**: Resolved "White Screen of Death" caused by missing component references (`NewGameDialog`, `SaveLoadDialog`) and TypeScript errors in `App.tsx`.

## [0.15.0] - 2025-11-21
### Added
- **Radial Fog of War**: Changed visibility reveal from square to radial for more realistic exploration.
- **Movement Confirmation**: Added a confirmation dialog when moving units to prevent accidental moves.
- **Hunting Target Selection**: Added a dialog to select specific targets when multiple animals are in range.

### Fixed
- **White Screen Crash**: Fixed a TypeScript error in `App.tsx` related to `LogEntry` type mismatch.
- **Hunting Logic**: Fixed an issue where hunters could not target specific animals due to ID mismatch between frontend (string) and backend (UUID).
- **Entity Removal**: Fixed a bug where killed animals remained on the map until the next turn. They are now removed immediately.
- **Movement Selection**: Fixed an issue where selecting a unit on an occupied tile would trigger a "Unit has already moved" error.

### Changed
- **Backend**: Updated `game_server.py` to return Entity IDs in `get_entities` response.
- **Frontend**: Updated `StatsPanel.tsx` to handle target selection and display debug logs for hunting actions.

## [0.14.0] - 2025-11-21
### Added
- **Unit Movement Confirmation**: Added a confirmation dialog when moving units to prevent accidental moves.
- **Targeted Hunting**: Hunters can now target specific animals via the Tile Inspector UI.
- **Safety Checks**: Added robust frontend error handling to prevent crashes when loading partial game states.

### Changed
- **Role Enforcement**: Hunters can no longer gather resources (Wood, Stone, etc.), enforcing class specialization.
- **Bug Fixes**: Resolved `TypeError: Cannot read properties of undefined` crash in StatsPanel and WorldCanvas.

## [0.13.0] - 2025-11-21
### Added
- **Tribe System Expansion**:
  - **New Unit Class: Crafter**:
    - Specialized unit for advanced construction and research.
    - Recruited at Bonfires (Cost: 50 Food).
  - **New Structures**:
    - **Bonfire**: Restores energy to nearby units (Built by Gatherers & Crafters).
    - **Hut**: Reduces tribe food consumption by 3 per year (Built by Crafters).
    - **Research Stations**:
      - **Weapon/Tools Research**: Generates Weapon Tech points (Built by Crafters).
      - **Clothing/Armor Research**: Generates Armor Tech points (Built by Crafters).
    - **Idols**: Unlocks Shaman class and generates Culture points (Built by Crafters).
- **Gameplay Mechanics**:
  - **Energy System**: Units consume energy to move/act. Bonfires restore energy.
  - **Food Consumption**: Tribe consumes 1 food per unit per year. Starvation causes damage.
  - **Targeted Hunting**: Hunters can now target specific animals.
  - **Build Mode**: UI for placing structures on adjacent tiles.
- **UI/UX Overhaul**:
  - **Loading Screen**: Visual progress bar during world generation.
  - **Tribe Details**: Dedicated dialog for detailed stockpile and unit management.
  - **Stats Panel**: Context-aware actions (Build, Recruit, Hunt, Gather).

## [0.12.0] - 2025-11-20
### Added
- **Full Ecology Integration**:
  - Integrated **Birds (Avian)**, **Fish (Aquatic)**, **Scavengers**, and **Insects** into the core simulation loop.
  - These species now have tracked populations, lifecycles, and death causes.
- **Deep Observability Suite**:
  - **Food Chain Analysis**: New UI tab showing a matrix of "Who Ate Whom" (e.g., Raptor -> Songbird, Bear -> Salmon).
  - **Death Cause Tracking**: New UI tab breaking down mortality by specific causes:
    - Predation (linked to specific predators)
    - Starvation
    - Old Age
    - Disease (by type)
    - Natural Disasters (Wildfire, Flood, Blizzard)
- **Event Logging**:
  - Added detailed logging for "Unknown" events like disease outbreaks and natural disasters to help debug population crashes.
- **UI Enhancements**:
  - Updated Statistics Overlay to support text-based matrices (Food Chain/Deaths) alongside line graphs.
  - Added population counters for all ecological layers (Insects, Avian, Aquatic) to the main sidebar.

## [0.11.0] - 2025-11-20
### Changed
- **Hardcore Ecology**:
  - Disabled "Safety Net" migrations. Extinctions are now permanent and frequent for unadapted species.
  - Simulation results show realistic population crashes for specialists (e.g., Polar Bears, Snow Leopards) if they fail to adapt.
- **Movement Logic Fixes**:
  - Implemented strict terrain traversal checks. Land animals can no longer cross deep ocean or shallow ocean tiles unless they have the `can_swim` trait.
  - Fixed "Bears in the Ocean" bug.
- **Simulation Analysis**:
  - Enhanced `run_simulation.py` to provide detailed annual death reports broken down by cause (Starvation, Predation, Old Age, Cold, Heat).
  - Added stability scoring to the final report.

## [0.10.0] - 2025-11-20
### Added
- **Expanded Bestiary**: Added 11 new species across diverse biomes:
  - Cold: Musk Ox, Polar Bear, Snow Leopard.
  - Temperate/Arid: Red Fox, Boar, Jackal, Rabbit.
  - Reptiles/Amphibians: Crocodile, Snake, Iguana, Frog, Giant Toad.
- **Mortality System**:
  - Implemented `EnvironmentalStats` for all species.
  - Added aging mechanics with `max_age` and probabilistic death.
  - Added environmental stress: Creatures take damage when outside their `min_temp`/`max_temp` comfort zones.
  - Added `cold_blooded` trait for reptiles/amphibians (double damage from cold).
- **Simulation Tool**: Created `run_simulation.py` for headless, long-term (30+ year) ecosystem stability testing with detailed annual reports.
- **Detailed Death Tracking**: System now tracks and reports specific causes of death (Starvation, Predation, Old Age, Cold, Heat).

### Changed
- **Predator AI Overhaul**:
  - Predators now move *before* hunting to close the gap.
  - Increased predator detection range and movement speed to handle fleeing prey.
  - Implemented "Sprint" mechanic for hungry predators.
- **Prey AI Update**:
  - Implemented "Fight or Flight" response.
  - Fast prey (Gazelles, Rabbits) gain evasion bonuses when fleeing.
  - Aggressive prey (Bison, Musk Ox) can counter-attack predators.
- **Balance Tuning**:
  - Adjusted fleeing evasion bonuses to prevent uncatchable prey.
  - Buffed predator accuracy and ambush capabilities in cover biomes (Forest, Jungle).
  - Tuned starvation and reproduction rates to achieve a stable "Predator Dominant" ecosystem.
- **Visuals**: Updated `game_renderer.py` with unique procedural sprites for all new species.

## [0.9.0] - 2025-11-20
### Added
- `srpg_stats.py`: Foundation for deterministic stat-based entity system (HP, ATK, DEF, SPD).
- `srpg_combat.py`: Combat resolution logic for entity interactions and environmental hazards.
- `balance_config.py`: Centralized configuration for ecosystem tuning (metabolism, growth rates, spawn delays).

### Changed
- `game_controller.py`: Integrated balance configuration and improved initialization sequence.
- `animal_system.py`: Refactored to use `srpg_stats` (CombatStats) instead of float-based energy.
- `predator_system.py`: Refactored to use `srpg_stats` and `srpg_combat` for hunting logic.
- `game_ui.py`: Fixed color rendering for scavengers, avian, and aquatic creatures.
- Ecosystem Balance:
  - Reduced predator hunt success and metabolism.
  - Increased vegetation growth and herbivore efficiency.
  - Added establishment phases for vegetation and herbivores before predators spawn.

## [0.8.0] - 2025-11-20
### Added
- `game_ui.py`: Pygame-based graphical user interface.
- Main Menu: Options for New World, Load Game, and Quit.
- World Config Screen: Sliders to customize world generation parameters.
- Game View: Interactive map with pan/zoom, play/pause controls, and real-time statistics.
- Visualization: Biome coloring, animal rendering, and event tracking.

## [0.7.0] - 2025-11-20
### Added
- `game_controller.py`: Central game state management, world generation configuration, and turn execution.
- `resource_definitions.py`: Data layer for resources, biome yields, and animal yields.
- Save/Load system: JSON-based persistence for complete game state.
- Statistics tracking: Tracks turns, births, deaths, and extinctions.

## [0.6.0] - 2024-03-21
### Added
- `events_ecology.py`: Added scavengers, avian creatures, and aquatic life.
- Implemented disease outbreaks affecting herbivores and predators.
- Implemented natural disasters (wildfires, floods, blizzards) that affect terrain and life.
- Added visualization for the complete ecosystem including all new species and events.

## [0.5.0] - 2024-03-21
### Added
- Predator system (`predator_system.py`)
  - Carnivore species (Wolf, Lion, Bear, Leopard, Arctic Fox)
  - Hunting mechanics with success rates and pack bonuses
  - Top-down population control and predator-prey dynamics
  - Omnivore behavior for Bears (fallback to vegetation)

## [0.4.0] - 2025-11-20
### Added
- Animal system (`animal_system.py`)
  - Herbivore species with unique traits (Deer, Bison, Caribou, Gazelle, Elephant)
  - Agency-based behaviors: Movement, Feeding, Reproduction
  - Population dynamics and energy metabolism
  - Migration logic based on biome preference and climate comfort

## [0.3.0] - 2025-11-20
### Added
- Vegetation system (`vegetation_system.py`)
  - Biome-specific growth rates and maximum densities
  - Dynamic response to temperature, moisture, and seasons
  - Logistic growth and seed dispersal mechanics
  - Impact of weather events (storms and droughts) on vegetation

## [0.2.0] - 2025-11-20
### Added
- Climate engine (`climate_engine.py`)
  - Seasonal cycles (Spring, Summer, Fall, Winter)
  - Dynamic temperature and moisture shifts
  - Weather events: Storms and Droughts
  - Turn-based time progression system
- Updated `terrain_generator.py` to support module import

## [0.1.0] - 2025-11-20
### Added
- Initial terrain generation system (`terrain_generator.py`)
  - Perlin-like noise generation for elevation
  - Temperature and moisture maps
  - Biome derivation based on environmental factors
  - Visualization using matplotlib
