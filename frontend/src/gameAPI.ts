import axios from 'axios';

const API_URL = 'http://localhost:8000';

export interface GameConfig {
    width: number;
    height: number;
    sea_level: number;
    herbivore_population: number;
    predator_population: number;
    starting_biome?: string;
    starting_units?: { [key: string]: number };
    fog_of_war?: boolean;
}

export interface WorldData {
    width: number;
    height: number;
    biomes: number[][];
    vegetation: number[][];
}

export interface Entity {
    id: string;
    species: string;
    x: number;
    y: number;
    hp: number;
    max_hp: number;
    attack?: number;
    defense?: number;
}

export interface EntityList {
    herbivores: Entity[];
    predators: Entity[];
    avian: Entity[];
    aquatic: Entity[];
    scavengers: Entity[];
}

export interface GameStats {
    turn: number;
    year: number;
    population: {
        herbivores: number;
        predators: number;
        scavengers: number;
        avian: number;
        aquatic: number;
    };
    history?: {
        herbivores: Record<string, number[]>;
        predators: Record<string, number[]>;
        scavengers: number[];
        avian: number[];
        aquatic: number[];
        tribe: {
            total: number[];
            gatherer: number[];
            hunter: number[];
            crafter: number[];
            shaman: number[];
        };
    };
    [key: string]: any;
}

export interface TileInfo {
    terrain: string;
    vegetation: string;
    temperature: string;
    moisture: string;
    entities: {
        id: string;
        type: string;
        species: string;
        hp: string;
        stats: string;
    }[];
    resources?: { [key: string]: number };
}

export interface Unit {
    id: string;
    x: number;
    y: number;
    type: 'gatherer' | 'hunter' | 'crafter' | 'shaman';
    hp: number;
    max_hp: number;
    energy: number;
    max_energy: number;
    name: string;
    movement_range?: number;
    has_moved?: boolean;
    has_acted?: boolean;
}

export interface Structure {
    id: string;
    x: number;
    y: number;
    type: string;
    hp: number;
}

export interface TribeData {
    name: string;
    stockpile: {
        wood: number;
        stone: number;
        fiber: number;
        food: number;
        clay: number;
        flint: number;
    };
    culture?: number;
    culture_rate?: number;
    expected_food_consumption?: number;
    units: Unit[];
    structures: Structure[];
    tech_tree: Record<string, boolean>;
    fog_map?: boolean[][]; // Optional as it might be large
    training_queue?: {
        type: string;
        turns_left: number;
        x: number;
        y: number;
    }[];
}

export const gameAPI = {
    newGame: async (config: GameConfig) => {
        const response = await axios.post(`${API_URL}/game/new`, config);
        return response.data;
    },

    getWorld: async (): Promise<WorldData> => {
        const response = await axios.get(`${API_URL}/game/world`);
        return response.data;
    },

    getEntities: async (): Promise<EntityList> => {
        const response = await axios.get(`${API_URL}/game/entities`);
        return response.data;
    },

    getStats: async (): Promise<GameStats> => {
        const response = await axios.get(`${API_URL}/game/stats`);
        return response.data;
    },

    step: async () => {
        const response = await axios.post(`${API_URL}/game/step`);
        return response.data;
    },

    getTileInfo: async (x: number, y: number): Promise<TileInfo> => {
        const response = await axios.get(`${API_URL}/game/tile/${x}/${y}`);
        return response.data;
    },

    getTribe: async (): Promise<TribeData> => {
        const response = await axios.get(`${API_URL}/game/tribe`);
        return response.data;
    },

    moveUnit: async (unitId: string, dx: number, dy: number) => {
        const response = await axios.post(`${API_URL}/game/unit/move`, { unit_id: unitId, dx, dy });
        return response.data;
    },

    unitAction: async (unitId: string, actionType: string, targetResource?: string, targetId?: string, structureType?: string, buildX?: number, buildY?: number, unitType?: string) => {
        const response = await axios.post(`${API_URL}/game/unit/action`, { 
            unit_id: unitId, 
            action_type: actionType,
            target_resource: targetResource,
            target_id: targetId,
            structure_type: structureType,
            build_x: buildX,
            build_y: buildY,
            unit_type: unitType
        });
        return response.data;
    },

    listSaves: async (): Promise<{saves: string[]}> => {
        const response = await axios.get(`${API_URL}/game/saves`);
        return response.data;
    },

    saveGame: async (filename: string) => {
        const response = await axios.post(`${API_URL}/game/save`, { filename });
        return response.data;
    },

    loadGame: async (filename: string) => {
        const response = await axios.post(`${API_URL}/game/load`, { filename });
        return response.data;
    }
};
