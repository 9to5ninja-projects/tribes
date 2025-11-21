import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Slider, Typography, Box, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import type { GameConfig } from '../gameAPI';

interface NewGameDialogProps {
    open: boolean;
    onClose: () => void;
    onStart: (config: GameConfig) => void;
}

export const NewGameDialog: React.FC<NewGameDialogProps> = ({ open, onClose, onStart }) => {
    const [config, setConfig] = useState<GameConfig>({
        width: 100,
        height: 80,
        sea_level: 0.42,
        herbivore_population: 120,
        predator_population: 10,
        starting_biome: 'Savanna',
        starting_units: { gatherer: 2, hunter: 1 }
    });

    const handleChange = (key: keyof GameConfig, value: any) => {
        setConfig(prev => ({ ...prev, [key]: value }));
    };

    const handleUnitChange = (type: string, value: number) => {
        setConfig(prev => ({
            ...prev,
            starting_units: {
                ...prev.starting_units,
                [type]: value
            }
        }));
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>New Game Configuration</DialogTitle>
            <DialogContent>
                <Box sx={{ mt: 2, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3 }}>
                    <Box>
                        <Typography gutterBottom>World Width: {config.width}</Typography>
                        <Slider
                            value={config.width}
                            min={50}
                            max={200}
                            step={10}
                            onChange={(_, v) => handleChange('width', v)}
                        />
                    </Box>
                    <Box>
                        <Typography gutterBottom>World Height: {config.height}</Typography>
                        <Slider
                            value={config.height}
                            min={50}
                            max={200}
                            step={10}
                            onChange={(_, v) => handleChange('height', v)}
                        />
                    </Box>
                    <Box>
                        <Typography gutterBottom>Sea Level: {config.sea_level}</Typography>
                        <Slider
                            value={config.sea_level}
                            min={0.1}
                            max={0.8}
                            step={0.01}
                            onChange={(_, v) => handleChange('sea_level', v)}
                        />
                    </Box>
                    <Box>
                        <FormControl fullWidth>
                            <InputLabel>Starting Biome</InputLabel>
                            <Select
                                value={config.starting_biome || 'Savanna'}
                                label="Starting Biome"
                                onChange={(e) => handleChange('starting_biome', e.target.value)}
                            >
                                <MenuItem value="Savanna">Savanna</MenuItem>
                                <MenuItem value="Grassland">Grassland</MenuItem>
                                <MenuItem value="Forest">Forest</MenuItem>
                                <MenuItem value="Rainforest">Rainforest</MenuItem>
                                <MenuItem value="Desert">Desert</MenuItem>
                                <MenuItem value="Tundra">Tundra</MenuItem>
                                <MenuItem value="Snow">Snow</MenuItem>
                                <MenuItem value="Beach">Beach</MenuItem>
                                <MenuItem value="Mountain">Mountain</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                    <Box>
                        <Typography gutterBottom>Herbivore Population: {config.herbivore_population}</Typography>
                        <Slider
                            value={config.herbivore_population}
                            min={50}
                            max={300}
                            step={10}
                            onChange={(_, v) => handleChange('herbivore_population', v)}
                        />
                    </Box>
                    <Box>
                        <Typography gutterBottom>Predator Population: {config.predator_population}</Typography>
                        <Slider
                            value={config.predator_population}
                            min={0}
                            max={50}
                            step={1}
                            onChange={(_, v) => handleChange('predator_population', v)}
                        />
                    </Box>
                    <Box sx={{ gridColumn: '1 / -1' }}>
                        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Starting Tribe</Typography>
                        <Box sx={{ display: 'flex', gap: 4 }}>
                            <Box sx={{ flex: 1 }}>
                                <Typography gutterBottom>Gatherers: {config.starting_units?.gatherer ?? 2}</Typography>
                                <Slider
                                    value={config.starting_units?.gatherer ?? 2}
                                    min={1}
                                    max={10}
                                    step={1}
                                    onChange={(_, v) => handleUnitChange('gatherer', v as number)}
                                />
                            </Box>
                            <Box sx={{ flex: 1 }}>
                                <Typography gutterBottom>Hunters: {config.starting_units?.hunter ?? 1}</Typography>
                                <Slider
                                    value={config.starting_units?.hunter ?? 1}
                                    min={0}
                                    max={10}
                                    step={1}
                                    onChange={(_, v) => handleUnitChange('hunter', v as number)}
                                />
                            </Box>
                        </Box>
                    </Box>
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cancel</Button>
                <Button onClick={() => onStart(config)} variant="contained" color="primary">
                    Start Game
                </Button>
            </DialogActions>
        </Dialog>
    );
};
