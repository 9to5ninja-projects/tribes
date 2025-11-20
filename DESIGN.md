# Tribes Evolution Sim - Design Document

## Core Philosophy
- **Primitive Focus**: No metals (Iron/Bronze). Peak tech is Steam/Architecture/Advanced Stone.
- **Tribal-Political**: Focus on the tribe as a unit, not individual survival.
- **Generative Economy**: Resources are tied to world generation and ecology. Adaptation is key.
- **Turn-Based Tactics**: Player moves units individually -> Wildlife moves in batch.

## 1. Resource Economy
**Type**: Tile-based, Finite & Renewable.
**Storage**: Global Tribal Stockpile (initially unlimited).

### Resource Categories
*   **Renewable**:
    *   **Wood**: Forest tiles (tied to vegetation %).
    *   **Fiber**: Grassland/Forest (tied to vegetation %).
    *   **Food**: Meat (Hunting), Fish (Coast), Berries (Gathering).
*   **Finite**:
    *   **Stone**: Mountains/Hills (Abundant).
    *   **Clay**: Near water/hills (Required for pottery).
    *   **Obsidian/Flint**: Rare stone types (Required for advanced tools).
    *   **Resin**: Rare forest drop (Required for hafting).
    *   **Salt**: Desert/Coast (Required for preservation).

## 2. Turn Structure
1.  **Player Phase**:
    *   Select Unit -> Move (within range).
    *   Action (Gather / Attack / Build).
    *   *Note*: Gathering adds to global stockpile immediately.
2.  **Wildlife Phase**:
    *   Animals move/hunt/flee based on AI.
    *   Predators: Hunger-driven + Territorial.
    *   Herbivores: Flee threats.
3.  **World Phase**:
    *   Vegetation regrows.
    *   Weather/Disasters apply effects.

## 3. Units & Classes
*   **Base Classes**:
    *   **Gatherer**: High carry capacity, efficient harvesting.
    *   **Hunter**: Ranged combat, stealth/scouting.
    *   **Crafter**: Bonus to building speed/quality.
    *   **Shaman/Healer**: Buffs, healing, ritual.
*   **Progression**:
    *   Units gain XP/Skills through action.
    *   Specialization unlocked via Tech/Buildings.

## 4. Technology (Research vs Invention)
*   **Research**: Unlocks concepts (e.g., "Pyrotechnology").
*   **Invention**: Unlocks specific recipes (e.g., "Kiln").
*   **Recipe System**:
    *   `Stone Axe` = Stone + Wood + Fiber.
    *   `Campfire` = Wood + Stone.

## 5. Structures & Defense
*   **Campfire**: Small safe zone, repels predators.
*   **Palisade**: Blocks movement, destructible.
*   **Storage**: (Later) Increases capacity/preservation.

## 6. Wildlife AI
*   **Hybrid Model**:
    *   **Hunger**: Predators hunt when hungry.
    *   **Territory**: Animals defend home ranges.
    *   **Pack Behavior**: Wolves/Lions coordinate.
