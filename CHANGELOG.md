# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
