import React, { useRef, useEffect, useState } from 'react';
import type { WorldData, EntityList, TribeData } from '../gameAPI';
import { Typography, Paper, Box, IconButton } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';

interface WorldCanvasProps {
    worldData: WorldData | null;
    entities: EntityList | null;
    tribeData: TribeData | null;
    selectedUnitId: string | null;
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

// Viewport settings
const VIEWPORT_SIZES = [16, 24, 32, 48, 64, 96, 128]; // Tiles visible
const CANVAS_SIZE_PX = 600; // Fixed canvas size in pixels

export const WorldCanvas: React.FC<WorldCanvasProps> = ({ worldData, entities, tribeData, selectedUnitId, onTileClick }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [hoverPos, setHoverPos] = useState<{x: number, y: number} | null>(null);
    const [zoomIndex, setZoomIndex] = useState(2); // Default to 32x32
    const [viewCenter, setViewCenter] = useState<{x: number, y: number} | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const dragStartRef = useRef<{x: number, y: number} | null>(null);
    const viewCenterStartRef = useRef<{x: number, y: number} | null>(null);

    const viewportTiles = VIEWPORT_SIZES[zoomIndex];
    const tileSize = CANVAS_SIZE_PX / viewportTiles;

    // Center view on selected unit or first unit
    useEffect(() => {
        if (selectedUnitId && tribeData && tribeData.units) {
            const unit = tribeData.units.find(u => u.id === selectedUnitId);
            if (unit) {
                setViewCenter({ x: unit.x, y: unit.y });
            }
        } else if (!viewCenter && tribeData && tribeData.units && tribeData.units.length > 0) {
            // Initial center
            setViewCenter({ x: tribeData.units[0].x, y: tribeData.units[0].y });
        }
    }, [selectedUnitId, tribeData]);

    useEffect(() => {
        if (!worldData || !canvasRef.current || !viewCenter) {
            return;
        }

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Calculate viewport bounds
        const halfView = Math.floor(viewportTiles / 2);
        const startX = Math.max(0, Math.min(worldData.width - viewportTiles, viewCenter.x - halfView));
        const startY = Math.max(0, Math.min(worldData.height - viewportTiles, viewCenter.y - halfView));
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw terrain
        for (let vy = 0; vy < viewportTiles; vy++) {
            for (let vx = 0; vx < viewportTiles; vx++) {
                const worldX = startX + vx;
                const worldY = startY + vy;

                if (worldX >= worldData.width || worldY >= worldData.height) continue;

                // Check Fog of War
                const isRevealed = tribeData?.fog_map && tribeData.fog_map[worldY] ? tribeData.fog_map[worldY][worldX] : true;
                
                const drawX = vx * tileSize;
                const drawY = vy * tileSize;

                if (!isRevealed) {
                    ctx.fillStyle = '#000000';
                    ctx.fillRect(drawX, drawY, tileSize, tileSize);
                    continue; 
                }

                const biome = worldData.biomes[worldY][worldX];
                const veg = worldData.vegetation[worldY][worldX];
                
                ctx.fillStyle = BIOME_COLORS[biome] || '#000000';
                ctx.fillRect(drawX, drawY, tileSize, tileSize);

                // Overlay vegetation
                if (veg > 0.1 && biome !== 0 && biome !== 1 && biome !== 10 && biome !== 11) {
                    ctx.fillStyle = `rgba(0, 100, 0, ${veg * 0.3})`;
                    ctx.fillRect(drawX, drawY, tileSize, tileSize);
                }
                
                // Grid lines (subtle)
                ctx.strokeStyle = 'rgba(0,0,0,0.1)';
                ctx.lineWidth = 0.5;
                ctx.strokeRect(drawX, drawY, tileSize, tileSize);
            }
        }

        // Helper to check if entity is in viewport
        const isInView = (x: number, y: number) => {
            return x >= startX && x < startX + viewportTiles && 
                   y >= startY && y < startY + viewportTiles;
        };

        const toScreen = (x: number, y: number) => {
            return {
                x: (x - startX) * tileSize,
                y: (y - startY) * tileSize
            };
        };

        // Helper to draw health bar
        const drawHealthBar = (x: number, y: number, hp: number, maxHp: number) => {
            const barWidth = tileSize * 0.8;
            const barHeight = tileSize * 0.15;
            const xPos = x + (tileSize - barWidth) / 2;
            const yPos = y - barHeight - 2; // Slightly above the unit

            // Background (Black)
            ctx.fillStyle = '#000';
            ctx.fillRect(xPos, yPos, barWidth, barHeight);

            // Health (Green to Red)
            const pct = Math.max(0, Math.min(1, hp / maxHp));
            ctx.fillStyle = pct > 0.5 ? '#00e676' : '#f44336';
            ctx.fillRect(xPos + 1, yPos + 1, (barWidth - 2) * pct, barHeight - 2);
        };

        // Draw entities
        if (entities) {
            // Herbivores (Green/Brown circles)
            if (entities.herbivores) {
                ctx.fillStyle = '#795548';
                entities.herbivores.forEach(e => {
                    if (!isInView(e.x, e.y)) return;
                    const isRevealed = tribeData?.fog_map && tribeData.fog_map[e.y] ? tribeData.fog_map[e.y][e.x] : true;
                    if (!isRevealed) return;

                    const pos = toScreen(e.x, e.y);
                    ctx.beginPath();
                    ctx.arc(pos.x + tileSize/2, pos.y + tileSize/2, tileSize/3, 0, Math.PI * 2);
                    ctx.fill();

                    drawHealthBar(pos.x, pos.y, e.hp, e.max_hp);
                });
            }

            // Predators (Red circles)
            if (entities.predators) {
                ctx.fillStyle = '#d32f2f';
                entities.predators.forEach(e => {
                    if (!isInView(e.x, e.y)) return;
                    const isRevealed = tribeData?.fog_map && tribeData.fog_map[e.y] ? tribeData.fog_map[e.y][e.x] : true;
                    if (!isRevealed) return;

                    const pos = toScreen(e.x, e.y);
                    ctx.beginPath();
                    ctx.arc(pos.x + tileSize/2, pos.y + tileSize/2, tileSize/3, 0, Math.PI * 2);
                    ctx.fill();

                    drawHealthBar(pos.x, pos.y, e.hp, e.max_hp);
                });
            }

            // Avian (Yellow/White stars/circles)
            if (entities.avian) {
                entities.avian.forEach(e => {
                    if (!isInView(e.x, e.y)) return;
                    const isRevealed = tribeData?.fog_map && tribeData.fog_map[e.y] ? tribeData.fog_map[e.y][e.x] : true;
                    if (!isRevealed) return;

                    const pos = toScreen(e.x, e.y);
                    ctx.fillStyle = '#ffeb3b'; // Yellow
                    ctx.beginPath();
                    // Draw a small triangle or star-like shape
                    ctx.moveTo(pos.x + tileSize/2, pos.y + tileSize/4);
                    ctx.lineTo(pos.x + tileSize*0.7, pos.y + tileSize*0.7);
                    ctx.lineTo(pos.x + tileSize*0.3, pos.y + tileSize*0.7);
                    ctx.fill();
                });
            }

            // Aquatic (Cyan circles)
            if (entities.aquatic) {
                ctx.fillStyle = '#00bcd4';
                entities.aquatic.forEach(e => {
                    if (!isInView(e.x, e.y)) return;
                    const isRevealed = tribeData?.fog_map && tribeData.fog_map[e.y] ? tribeData.fog_map[e.y][e.x] : true;
                    if (!isRevealed) return;

                    const pos = toScreen(e.x, e.y);
                    ctx.beginPath();
                    ctx.arc(pos.x + tileSize/2, pos.y + tileSize/2, tileSize/4, 0, Math.PI * 2);
                    ctx.fill();
                });
            }

            // Scavengers (Grey/Brown small circles)
            if (entities.scavengers) {
                ctx.fillStyle = '#5d4037';
                entities.scavengers.forEach(e => {
                    if (!isInView(e.x, e.y)) return;
                    const isRevealed = tribeData?.fog_map && tribeData.fog_map[e.y] ? tribeData.fog_map[e.y][e.x] : true;
                    if (!isRevealed) return;

                    const pos = toScreen(e.x, e.y);
                    ctx.beginPath();
                    ctx.arc(pos.x + tileSize/2, pos.y + tileSize/2, tileSize/4, 0, Math.PI * 2);
                    ctx.fill();
                });
            }
        }

        // Draw Structures
        if (tribeData && tribeData.structures) {
            tribeData.structures.forEach(structure => {
                if (!isInView(structure.x, structure.y)) return;
                const isRevealed = tribeData?.fog_map && tribeData.fog_map[structure.y] ? tribeData.fog_map[structure.y][structure.x] : true;
                if (!isRevealed) return;

                const pos = toScreen(structure.x, structure.y);
                
                // Check if structure is under construction
                const isUnderConstruction = !(structure as any).is_complete;
                
                if (isUnderConstruction) {
                    // Draw scaffolding / construction site
                    ctx.fillStyle = 'rgba(139, 69, 19, 0.5)'; // Transparent brown
                    ctx.fillRect(pos.x + tileSize/4, pos.y + tileSize/4, tileSize/2, tileSize/2);
                    
                    // Draw progress bar
                    const progress = 1 - ((structure as any).construction_turns_left / (structure as any).max_construction_turns);
                    ctx.fillStyle = '#fff';
                    ctx.fillRect(pos.x + tileSize/4, pos.y + tileSize*0.8, tileSize/2, tileSize/10);
                    ctx.fillStyle = '#00e676'; // Green
                    ctx.fillRect(pos.x + tileSize/4, pos.y + tileSize*0.8, (tileSize/2) * progress, tileSize/10);
                    
                    return; // Skip drawing the full structure
                }
                
                // Draw Bonfire (Orange Square)
                if (structure.type === 'bonfire') {
                    ctx.fillStyle = '#ff6d00';
                    ctx.fillRect(pos.x + tileSize/4, pos.y + tileSize/4, tileSize/2, tileSize/2);
                    
                    // Flicker effect
                    if (Math.random() > 0.5) {
                        ctx.fillStyle = '#ffab40';
                        ctx.fillRect(pos.x + tileSize/3, pos.y + tileSize/3, tileSize/3, tileSize/3);
                    }
                } else if (structure.type === 'hut') {
                    ctx.fillStyle = '#8d6e63'; // Brown
                    ctx.fillRect(pos.x + tileSize/4, pos.y + tileSize/4, tileSize/2, tileSize/2);
                    // Roof
                    ctx.fillStyle = '#5d4037';
                    ctx.beginPath();
                    ctx.moveTo(pos.x + tileSize/4, pos.y + tileSize/4);
                    ctx.lineTo(pos.x + tileSize/2, pos.y + tileSize/8);
                    ctx.lineTo(pos.x + tileSize*0.75, pos.y + tileSize/4);
                    ctx.fill();
                } else if (structure.type === 'research_weapon') {
                    ctx.fillStyle = '#607d8b'; // Blue Grey
                    ctx.fillRect(pos.x + tileSize/4, pos.y + tileSize/4, tileSize/2, tileSize/2);
                    ctx.fillStyle = '#d32f2f'; // Red mark
                    ctx.fillRect(pos.x + tileSize/2 - tileSize/8, pos.y + tileSize/2 - tileSize/8, tileSize/4, tileSize/4);
                } else if (structure.type === 'research_armor') {
                    ctx.fillStyle = '#607d8b'; // Blue Grey
                    ctx.fillRect(pos.x + tileSize/4, pos.y + tileSize/4, tileSize/2, tileSize/2);
                    ctx.fillStyle = '#1976d2'; // Blue mark
                    ctx.fillRect(pos.x + tileSize/2 - tileSize/8, pos.y + tileSize/2 - tileSize/8, tileSize/4, tileSize/4);
                } else if (structure.type === 'idol') {
                    ctx.fillStyle = '#ffd700'; // Gold
                    ctx.beginPath();
                    ctx.arc(pos.x + tileSize/2, pos.y + tileSize/2, tileSize/4, 0, Math.PI * 2);
                    ctx.fill();
                }
            });
        }

        // Draw Tribe Units
        if (tribeData && tribeData.units) {
            tribeData.units.forEach(unit => {
                if (!isInView(unit.x, unit.y)) return;
                
                const pos = toScreen(unit.x, unit.y);
                
                // Selection highlight
                if (unit.id === selectedUnitId) {
                    ctx.fillStyle = 'rgba(255, 255, 0, 0.5)';
                    ctx.beginPath();
                    ctx.arc(pos.x + tileSize/2, pos.y + tileSize/2, tileSize, 0, Math.PI * 2);
                    ctx.fill();
                    
                    // Draw movement range (Diamond shape) - Only if hasn't moved
                    if (!unit.has_moved) {
                        ctx.strokeStyle = 'rgba(255, 255, 0, 0.5)';
                        ctx.lineWidth = 2;
                        const range = unit.movement_range || 2;
                        
                        ctx.fillStyle = 'rgba(255, 255, 0, 0.1)';
                        for (let dy = -range; dy <= range; dy++) {
                            for (let dx = -range; dx <= range; dx++) {
                                if (Math.abs(dx) + Math.abs(dy) <= range) {
                                    const tx = unit.x + dx;
                                    const ty = unit.y + dy;
                                    if (isInView(tx, ty)) {
                                        const tPos = toScreen(tx, ty);
                                        ctx.fillRect(tPos.x, tPos.y, tileSize, tileSize);
                                    }
                                }
                            }
                        }
                    }

                    // Draw Attack Range (Red) - Only if hasn't acted and is Hunter
                    if (!unit.has_acted && unit.type === 'hunter') {
                        const attackRange = 2;
                        ctx.fillStyle = 'rgba(255, 0, 0, 0.15)'; // Red tint
                        ctx.strokeStyle = 'rgba(255, 0, 0, 0.3)';
                        
                        for (let dy = -attackRange; dy <= attackRange; dy++) {
                            for (let dx = -attackRange; dx <= attackRange; dx++) {
                                if (Math.abs(dx) + Math.abs(dy) <= attackRange) {
                                    const tx = unit.x + dx;
                                    const ty = unit.y + dy;
                                    // Don't draw over the unit itself
                                    if (tx === unit.x && ty === unit.y) continue;
                                    
                                    if (isInView(tx, ty)) {
                                        const tPos = toScreen(tx, ty);
                                        ctx.fillRect(tPos.x, tPos.y, tileSize, tileSize);
                                        ctx.strokeRect(tPos.x, tPos.y, tileSize, tileSize);
                                    }
                                }
                            }
                        }
                    }
                }

                // Unit body
                ctx.fillStyle = '#00bcd4'; // Cyan for player units
                ctx.beginPath();
                ctx.arc(pos.x + tileSize/2, pos.y + tileSize/2, tileSize/2.5, 0, Math.PI * 2);
                ctx.fill();
                
                // Border
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 1;
                ctx.stroke();

                drawHealthBar(pos.x, pos.y, unit.hp, unit.max_hp);
            });
        }

        // Draw hover cursor
        if (hoverPos) {
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 1;
            ctx.strokeRect(hoverPos.x * tileSize, hoverPos.y * tileSize, tileSize, tileSize);
        }

    }, [worldData, entities, tribeData, selectedUnitId, hoverPos, zoomIndex, viewCenter]);

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true);
        dragStartRef.current = { x: e.clientX, y: e.clientY };
        viewCenterStartRef.current = viewCenter;
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!canvasRef.current || !viewCenter || !worldData) return;
        
        const rect = canvasRef.current.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        const vx = Math.floor(mouseX / tileSize);
        const vy = Math.floor(mouseY / tileSize);
        
        setHoverPos({x: vx, y: vy});

        if (isDragging && dragStartRef.current && viewCenterStartRef.current) {
            const dxPx = e.clientX - dragStartRef.current.x;
            const dyPx = e.clientY - dragStartRef.current.y;
            
            const dxTiles = Math.round(dxPx / tileSize);
            const dyTiles = Math.round(dyPx / tileSize);
            
            if (dxTiles !== 0 || dyTiles !== 0) {
                 setViewCenter({
                    x: Math.max(0, Math.min(worldData.width - 1, viewCenterStartRef.current.x - dxTiles)),
                    y: Math.max(0, Math.min(worldData.height - 1, viewCenterStartRef.current.y - dyTiles))
                });
            }
        }
    };

    const handleMouseUp = (e: React.MouseEvent) => {
        if (isDragging && dragStartRef.current) {
            const dx = Math.abs(e.clientX - dragStartRef.current.x);
            const dy = Math.abs(e.clientY - dragStartRef.current.y);
            
            if (dx < 5 && dy < 5) {
                // Click
                if (hoverPos && viewCenter && worldData) {
                    const halfView = Math.floor(viewportTiles / 2);
                    const startX = Math.max(0, Math.min(worldData.width - viewportTiles, viewCenter.x - halfView));
                    const startY = Math.max(0, Math.min(worldData.height - viewportTiles, viewCenter.y - halfView));
                    
                    const worldX = startX + hoverPos.x;
                    const worldY = startY + hoverPos.y;
                    
                    onTileClick(worldX, worldY);
                }
            }
        }
        setIsDragging(false);
        dragStartRef.current = null;
        viewCenterStartRef.current = null;
    };

    const handleMouseLeave = () => {
        setIsDragging(false);
        dragStartRef.current = null;
        viewCenterStartRef.current = null;
        setHoverPos(null);
    };
    
    // Pan controls
    const pan = (dx: number, dy: number) => {
        if (!viewCenter || !worldData) return;
        setViewCenter({
            x: Math.max(0, Math.min(worldData.width - 1, viewCenter.x + dx)),
            y: Math.max(0, Math.min(worldData.height - 1, viewCenter.y + dy))
        });
    };

    if (!worldData || !worldData.biomes) return <Typography>No world data</Typography>;

    return (
        <Box sx={{ position: 'relative', display: 'inline-block' }}>
            <Paper elevation={3} sx={{ p: 1, bgcolor: '#000', overflow: 'hidden' }}>
                <canvas
                    ref={canvasRef}
                    width={CANVAS_SIZE_PX}
                    height={CANVAS_SIZE_PX}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseLeave}
                    style={{ cursor: isDragging ? 'grabbing' : 'crosshair', display: 'block' }}
                />
            </Paper>
            
            {/* Zoom Controls */}
            <Paper sx={{ position: 'absolute', top: 16, right: 16, display: 'flex', flexDirection: 'column', gap: 1, p: 0.5, bgcolor: 'rgba(255,255,255,0.8)' }}>
                <IconButton size="small" onClick={() => setZoomIndex(z => Math.max(z - 1, 0))}>
                    <AddIcon />
                </IconButton>
                <Typography variant="caption" align="center">{viewportTiles}x{viewportTiles}</Typography>
                <IconButton size="small" onClick={() => setZoomIndex(z => Math.min(z + 1, VIEWPORT_SIZES.length - 1))}>
                    <RemoveIcon />
                </IconButton>
            </Paper>
            
            {/* Pan Hints */}
            <Typography variant="caption" sx={{ position: 'absolute', bottom: 5, left: 5, color: 'rgba(255,255,255,0.5)' }}>
                Click unit to center
            </Typography>
            
            {/* Pan Controls */}
            <Paper sx={{ position: 'absolute', bottom: 16, right: 16, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 0.5, p: 0.5, bgcolor: 'rgba(255,255,255,0.8)' }}>
                <Box />
                <IconButton size="small" onClick={() => pan(0, -5)}>
                    <Typography variant="caption">▲</Typography>
                </IconButton>
                <Box />
                <IconButton size="small" onClick={() => pan(-5, 0)}>
                    <Typography variant="caption">◀</Typography>
                </IconButton>
                <Box />
                <IconButton size="small" onClick={() => pan(5, 0)}>
                    <Typography variant="caption">▶</Typography>
                </IconButton>
                <Box />
                <IconButton size="small" onClick={() => pan(0, 5)}>
                    <Typography variant="caption">▼</Typography>
                </IconButton>
                <Box />
            </Paper>
        </Box>
    );
};
