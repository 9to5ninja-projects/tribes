import React, { useRef, useEffect, useState } from 'react';
import type { WorldData, EntityList } from '../gameAPI';
import { Typography, Paper } from '@mui/material';

interface WorldCanvasProps {
    worldData: WorldData | null;
    entities: EntityList | null;
    onTileClick: (x: number, y: number) => void;
}

const BIOME_COLORS: Record<number, string> = {
    0: '#1a237e', // Deep Ocean
    1: '#0277bd', // Shallow Ocean
    2: '#fff59d', // Beach
    3: '#d7ccc8', // Desert
    4: '#8d6e63', // Savanna
    5: '#81c784', // Grassland
    6: '#2e7d32', // Tropical Rainforest
    7: '#388e3c', // Temperate Forest
    8: '#1b5e20', // Taiga
    9: '#cfd8dc', // Tundra
    10: '#ffffff', // Snow
    11: '#546e7a', // Mountain
};

const TILE_SIZE = 8;

export const WorldCanvas: React.FC<WorldCanvasProps> = ({ worldData, entities, onTileClick }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [hoverPos, setHoverPos] = useState<{x: number, y: number} | null>(null);

    useEffect(() => {
        if (!worldData || !canvasRef.current) {
            console.log("WorldCanvas: Missing data or ref", { worldData, ref: canvasRef.current });
            return;
        }

        console.log("WorldCanvas: Drawing frame", { width: worldData.width, height: worldData.height });
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Draw terrain
        for (let y = 0; y < worldData.height; y++) {
            for (let x = 0; x < worldData.width; x++) {
                const biome = worldData.biomes[y][x];
                const veg = worldData.vegetation[y][x];
                
                ctx.fillStyle = BIOME_COLORS[biome] || '#000000';
                ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);

                // Overlay vegetation
                if (veg > 0.1 && biome !== 0 && biome !== 1 && biome !== 10 && biome !== 11) {
                    ctx.fillStyle = `rgba(0, 100, 0, ${veg * 0.3})`;
                    ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                }
            }
        }

        // Draw entities
        if (entities) {
            // Herbivores (Green/Brown circles)
            ctx.fillStyle = '#795548';
            entities.herbivores.forEach(e => {
                ctx.beginPath();
                ctx.arc(e.x * TILE_SIZE + TILE_SIZE/2, e.y * TILE_SIZE + TILE_SIZE/2, TILE_SIZE/3, 0, Math.PI * 2);
                ctx.fill();
            });

            // Predators (Red circles)
            ctx.fillStyle = '#d32f2f';
            entities.predators.forEach(e => {
                ctx.beginPath();
                ctx.arc(e.x * TILE_SIZE + TILE_SIZE/2, e.y * TILE_SIZE + TILE_SIZE/2, TILE_SIZE/3, 0, Math.PI * 2);
                ctx.fill();
            });
        }

        // Draw hover cursor
        if (hoverPos) {
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 1;
            ctx.strokeRect(hoverPos.x * TILE_SIZE, hoverPos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        }

    }, [worldData, entities, hoverPos]);

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!canvasRef.current) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / TILE_SIZE);
        const y = Math.floor((e.clientY - rect.top) / TILE_SIZE);
        setHoverPos({x, y});
    };

    const handleClick = () => {
        if (hoverPos) {
            onTileClick(hoverPos.x, hoverPos.y);
        }
    };

    if (!worldData) return <Typography>No world data</Typography>;

    return (
        <Paper elevation={3} sx={{ p: 1, display: 'inline-block', bgcolor: '#000' }}>
            <canvas
                ref={canvasRef}
                width={worldData.width * TILE_SIZE}
                height={worldData.height * TILE_SIZE}
                onMouseMove={handleMouseMove}
                onClick={handleClick}
                style={{ cursor: 'crosshair', display: 'block' }}
            />
        </Paper>
    );
};
