import axios from 'axios';

const API_URL = 'http://localhost:8000';

export interface GameConfig {
    width: number;
    height: number;
    sea_level: number;
    herbivore_population: number;
    predator_population: number;
}

export interface WorldData {
    width: number;
    height: number;
    biomes: number[][];
    vegetation: number[][];
}

export interface Entity {
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
}

export interface GameStats {
    turn: number;
    year: number;
    population: {
        herbivores: number;
        predators: number;
    };
    [key: string]: any;
}

export interface TileInfo {
    terrain: string;
    vegetation: string;
    temperature: string;
    moisture: string;
    entities: {
        type: string;
        species: string;
        hp: string;
        stats: string;
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
    }
};
