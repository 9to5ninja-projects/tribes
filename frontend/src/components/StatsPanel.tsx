import React from 'react';
import type { GameStats, TileInfo } from '../gameAPI';
import { Paper, Typography, Box, Divider, List, ListItem, ListItemText } from '@mui/material';

interface StatsPanelProps {
    stats: GameStats | null;
    selectedTile: TileInfo | null;
    selectedCoords: {x: number, y: number} | null;
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ stats, selectedTile, selectedCoords }) => {
    return (
        <Box sx={{ width: 300, height: '100%', overflow: 'auto' }}>
            <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>World Stats</Typography>
                {stats ? (
                    <>
                        <Typography>Year: {stats.year}</Typography>
                        <Typography>Turn: {stats.turn}</Typography>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="subtitle2">Population</Typography>
                        <Typography>Herbivores: {stats.population.herbivores}</Typography>
                        <Typography>Predators: {stats.population.predators}</Typography>
                    </>
                ) : (
                    <Typography color="text.secondary">No game active</Typography>
                )}
            </Paper>

            <Paper elevation={3} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Tile Inspector</Typography>
                {selectedCoords && (
                    <Typography variant="caption" display="block" gutterBottom>
                        Coordinates: ({selectedCoords.x}, {selectedCoords.y})
                    </Typography>
                )}
                
                {selectedTile ? (
                    <>
                        <Typography>Terrain: {selectedTile.terrain}</Typography>
                        <Typography>Vegetation: {selectedTile.vegetation}</Typography>
                        <Typography>Temp: {selectedTile.temperature}°C</Typography>
                        <Typography>Moisture: {selectedTile.moisture}</Typography>
                        
                        {selectedTile.entities.length > 0 && (
                            <>
                                <Divider sx={{ my: 1 }} />
                                <Typography variant="subtitle2">Entities Here:</Typography>
                                <List dense>
                                    {selectedTile.entities.map((ent, i) => (
                                        <ListItem key={i} disablePadding>
                                            <ListItemText 
                                                primary={`${ent.species} (${ent.type})`}
                                                secondary={
                                                    <>
                                                        HP: {ent.hp}<br/>
                                                        {ent.stats}
                                                    </>
                                                }
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            </>
                        )}
                    </>
                ) : (
                    <Typography color="text.secondary">Click a tile to inspect</Typography>
                )}
            </Paper>
        </Box>
    );
};
