# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
