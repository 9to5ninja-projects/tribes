import React, { useState } from 'react';
import type { GameStats, TileInfo, TribeData, EntityList } from '../gameAPI';
import { Paper, Typography, Box, Divider, List, ListItem, ListItemText, Chip, Button, Dialog, DialogTitle, ListItemButton } from '@mui/material';
import ConstructionIcon from '@mui/icons-material/Construction';

interface StatsPanelProps {
    stats: GameStats | null;
    tribeData: TribeData | null;
    selectedTile: TileInfo | null;
    selectedCoords: {x: number, y: number} | null;
    selectedUnitId: string | null;
    entities: EntityList | null;
    onAction?: (unitId: string, action: string, target?: string, targetId?: string, structureType?: string, buildX?: number, buildY?: number, unitType?: string) => void;
    onEnterBuildMode?: (structureType: string) => void;
    onOpenTribeDetails?: () => void;
    onLog?: (message: string) => void;
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ stats, tribeData, selectedTile, selectedCoords, selectedUnitId, entities, onAction, onEnterBuildMode, onOpenTribeDetails, onLog }) => {
    const [targetSelectionOpen, setTargetSelectionOpen] = useState(false);
    const [availableTargets, setAvailableTargets] = useState<{id: string, name: string, x: number, y: number, type: string, hp: number, max_hp: number}[]>([]);
    
    const [gatherSelectionOpen, setGatherSelectionOpen] = useState(false);
    const [availableResources, setAvailableResources] = useState<string[]>([]);

    const selectedUnit = tribeData?.units?.find(u => u.id === selectedUnitId);
    
    const handleHuntClick = () => {
        if (!selectedUnit || !entities) {
            console.warn("Hunt clicked but missing data:", { selectedUnit, entities });
            return;
        }
        
        console.log(`Hunting with ${selectedUnit.name} at (${selectedUnit.x}, ${selectedUnit.y})`);
        
        const targets: {id: string, name: string, x: number, y: number, type: string, hp: number, max_hp: number}[] = [];
        const range = 2; // Hunter range
        
        // Check herbivores
        if (entities.herbivores) {
            console.log(`Checking ${entities.herbivores.length} herbivores...`);
            entities.herbivores.forEach(h => {
                const dist = Math.abs(h.x - selectedUnit.x) + Math.abs(h.y - selectedUnit.y);
                if (dist <= range + 2) { // Log nearby ones even if slightly out of range
                     console.log(`  - ${h.species} at (${h.x}, ${h.y}) Dist: ${dist}`);
                }
                if (dist <= range) {
                    targets.push({
                        id: (h as any).id || `h-${h.x}-${h.y}`, // Fallback ID if missing
                        name: h.species,
                        x: h.x,
                        y: h.y,
                        type: 'Herbivore',
                        hp: h.hp,
                        max_hp: h.max_hp
                    });
                }
            });
        }
        
        // Check predators
        if (entities.predators) {
            console.log(`Checking ${entities.predators.length} predators...`);
            entities.predators.forEach(p => {
                const dist = Math.abs(p.x - selectedUnit.x) + Math.abs(p.y - selectedUnit.y);
                if (dist <= range + 2) {
                     console.log(`  - ${p.species} at (${p.x}, ${p.y}) Dist: ${dist}`);
                }
                if (dist <= range) {
                    targets.push({
                        id: (p as any).id || `p-${p.x}-${p.y}`,
                        name: p.species,
                        x: p.x,
                        y: p.y,
                        type: 'Predator',
                        hp: p.hp,
                        max_hp: p.max_hp
                    });
                }
            });
        } else {
            console.warn("entities.predators is undefined or empty", entities);
        }
        
        if (targets.length === 0) {
            console.log("No targets found in range. Unit:", selectedUnit);
            if (onLog) {
                onLog("No animals in range!");
            } else {
                alert("No animals in range!");
            }
        } else if (targets.length === 1) {
            // Just hunt the one
            console.log("Hunting single target:", targets[0]);
            if (confirm(`Hunt ${targets[0].name} at (${targets[0].x}, ${targets[0].y})?`)) {
                 onAction && onAction(selectedUnit.id, 'hunt', undefined, targets[0].id);
            }
        } else {
            console.log("Opening target selection for:", targets);
            setAvailableTargets(targets);
            setTargetSelectionOpen(true);
        }
    };
    
    // Check if selected unit is on a tile with resources
    // We need to check if the selected tile corresponds to the unit's location
    const unitTileResources = selectedUnit && selectedTile && 
        selectedCoords?.x === selectedUnit.x && 
        selectedCoords?.y === selectedUnit.y 
        ? selectedTile.resources 
        : null;

    const canBuildBonfire = tribeData && tribeData.stockpile &&
        (tribeData.stockpile.wood || 0) >= 10 && 
        (tribeData.stockpile.flint || 0) >= 5;

    const canBuildHut = tribeData && tribeData.stockpile &&
        (tribeData.stockpile.wood || 0) >= 20 && 
        (tribeData.stockpile.fiber || 0) >= 10;

    const canBuildResearchWeapon = tribeData && tribeData.stockpile &&
        (tribeData.stockpile.wood || 0) >= 30 && 
        (tribeData.stockpile.stone || 0) >= 10;

    const canBuildResearchArmor = tribeData && tribeData.stockpile &&
        (tribeData.stockpile.wood || 0) >= 30 && 
        (tribeData.stockpile.fiber || 0) >= 20;

    const canBuildIdol = tribeData && tribeData.stockpile &&
        (tribeData.stockpile.wood || 0) >= 40 && 
        (tribeData.stockpile.stone || 0) >= 40;

    // Check if unit is near a bonfire (for recruiting)
    const isNearBonfire = selectedUnit && tribeData?.structures?.some(s => 
        s.type === 'bonfire' && 
        (s as any).is_complete &&
        (Math.abs(s.x - selectedUnit.x) + Math.abs(s.y - selectedUnit.y) <= 3)
    );

    const isNearIdol = selectedUnit && tribeData?.structures?.some(s => 
        s.type === 'idol' && 
        (s as any).is_complete &&
        (Math.abs(s.x - selectedUnit.x) + Math.abs(s.y - selectedUnit.y) <= 3)
    );

    const canRecruitGatherer = tribeData && tribeData.stockpile && (tribeData.stockpile.food || 0) >= 5;
    const canRecruitHunter = tribeData && tribeData.stockpile && (tribeData.stockpile.food || 0) >= 7;
    const canRecruitCrafter = tribeData && tribeData.stockpile && (tribeData.stockpile.food || 0) >= 10;
    const canRecruitShaman = tribeData && tribeData.stockpile && (tribeData.stockpile.food || 0) >= 12;

    // Check if selected unit can hunt the selected tile
    const isHunter = selectedUnit?.type === 'hunter';
    const distToTile = selectedUnit && selectedCoords ? 
        Math.abs(selectedUnit.x - selectedCoords.x) + Math.abs(selectedUnit.y - selectedCoords.y) : Infinity;
    const canHuntTile = isHunter && distToTile <= 2 && !selectedUnit.has_acted;

    return (
        <Box sx={{ width: 300, height: '100%', overflow: 'auto' }}>
            {/* Tribe Status Summary */}
            <Paper elevation={3} sx={{ p: 2, mb: 2, bgcolor: '#e3f2fd' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" color="primary">Tribe</Typography>
                    <Button size="small" variant="outlined" onClick={onOpenTribeDetails}>
                        Details
                    </Button>
                </Box>
                {tribeData && tribeData.units ? (
                    <>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                            <Chip label={`Food: ${tribeData.stockpile.food}`} size="small" color={tribeData.stockpile.food < 10 ? "error" : "default"} />
                            <Chip label={`Wood: ${tribeData.stockpile.wood}`} size="small" />
                            <Chip label={`Flint: ${tribeData.stockpile.flint}`} size="small" />
                        </Box>
                        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                            Units: {tribeData.units.length} | Structures: {tribeData.structures?.length || 0}
                        </Typography>
                        {tribeData.training_queue && tribeData.training_queue.length > 0 && (
                            <Box sx={{ mt: 1 }}>
                                <Divider />
                                <Typography variant="caption" sx={{ fontWeight: 'bold' }}>Training Queue:</Typography>
                                <List dense disablePadding>
                                    {tribeData.training_queue.map((item, i) => (
                                        <ListItem key={i} disablePadding>
                                            <ListItemText 
                                                primary={`${item.type} (${item.turns_left} turns)`} 
                                                primaryTypographyProps={{ variant: 'caption' }}
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            </Box>
                        )}
                    </>
                ) : (
                    <Typography color="text.secondary">No tribe data</Typography>
                )}
            </Paper>

            {/* Selected Unit */}
            {selectedUnit && (
                <Paper elevation={3} sx={{ p: 2, mb: 2, border: '2px solid #00bcd4' }}>
                    <Typography variant="h6" gutterBottom>{selectedUnit.name}</Typography>
                    <Typography>Type: {selectedUnit.type}</Typography>
                    <Typography>HP: {selectedUnit.hp}/{selectedUnit.max_hp}</Typography>
                    <Typography>Energy: {selectedUnit.energy}/{selectedUnit.max_energy}</Typography>
                    
                    <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                        <Chip 
                            label={selectedUnit.has_moved ? "Moved" : "Can Move"} 
                            color={selectedUnit.has_moved ? "default" : "success"} 
                            size="small" 
                        />
                        <Chip 
                            label={selectedUnit.has_acted ? "Acted" : "Can Act"} 
                            color={selectedUnit.has_acted ? "default" : "success"} 
                            size="small" 
                        />
                    </Box>
                    
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2">Actions:</Typography>
                        
                        {unitTileResources && Object.keys(unitTileResources).length > 0 && selectedUnit.type !== 'hunter' && (
                            <Button 
                                variant="contained" 
                                size="small" 
                                startIcon={<ConstructionIcon />}
                                onClick={() => {
                                    if (!unitTileResources) return;
                                    const resources = Object.keys(unitTileResources);
                                    if (resources.length === 1) {
                                        // Gather the only resource
                                        onAction && onAction(selectedUnit.id, 'gather', resources[0]);
                                    } else {
                                        // Open selection dialog
                                        setAvailableResources(resources);
                                        setGatherSelectionOpen(true);
                                    }
                                }}
                                disabled={selectedUnit.has_acted}
                                sx={{ mt: 1, mr: 1 }}
                            >
                                Gather
                            </Button>
                        )}

                        {selectedUnit.type === 'hunter' && (
                            <Button
                                variant="contained"
                                size="small"
                                color="error"
                                onClick={handleHuntClick}
                                disabled={selectedUnit.has_acted}
                                sx={{ mt: 1, mr: 1 }}
                            >
                                Hunt
                            </Button>
                        )}

                        {(selectedUnit.type === 'gatherer' || selectedUnit.type === 'crafter') && (
                            <Button 
                                variant="contained" 
                                size="small" 
                                color="warning"
                                onClick={() => onEnterBuildMode && onEnterBuildMode('bonfire')}
                                disabled={selectedUnit.has_acted || !canBuildBonfire}
                                sx={{ mt: 1, mr: 1 }}
                            >
                                Build Bonfire (10 Wood, 5 Flint)
                            </Button>
                        )}

                        {selectedUnit.type === 'crafter' && (
                            <>
                                <Button 
                                    variant="contained" 
                                    size="small" 
                                    color="info"
                                    onClick={() => onEnterBuildMode && onEnterBuildMode('hut')}
                                    disabled={selectedUnit.has_acted || !canBuildHut}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    Build Hut (20 Wood, 10 Fiber)
                                </Button>
                                <Button 
                                    variant="contained" 
                                    size="small" 
                                    color="secondary"
                                    onClick={() => onEnterBuildMode && onEnterBuildMode('research_weapon')}
                                    disabled={selectedUnit.has_acted || !canBuildResearchWeapon}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    Build Weapon Lab (30 Wood, 10 Stone)
                                </Button>
                                <Button 
                                    variant="contained" 
                                    size="small" 
                                    color="secondary"
                                    onClick={() => onEnterBuildMode && onEnterBuildMode('research_armor')}
                                    disabled={selectedUnit.has_acted || !canBuildResearchArmor}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    Build Armor Lab (30 Wood, 20 Fiber)
                                </Button>
                                <Button 
                                    variant="contained" 
                                    size="small" 
                                    color="success"
                                    onClick={() => onEnterBuildMode && onEnterBuildMode('idol')}
                                    disabled={selectedUnit.has_acted || !canBuildIdol}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    Build Idol (40 Wood, 40 Stone)
                                </Button>
                            </>
                        )}

                        {isNearBonfire && (
                            <>
                                <Button
                                    variant="contained"
                                    size="small"
                                    color="secondary"
                                    onClick={() => {
                                        if (confirm("Recruit Gatherer (5 Food, 3 Turns)?")) {
                                            onAction && onAction(selectedUnit.id, 'recruit', undefined, undefined, undefined, undefined, undefined, 'gatherer');
                                        }
                                    }}
                                    disabled={selectedUnit.has_acted || !canRecruitGatherer}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    Recruit Gatherer
                                </Button>
                                <Button
                                    variant="contained"
                                    size="small"
                                    color="secondary"
                                    onClick={() => {
                                        if (confirm("Recruit Hunter (7 Food, 3 Turns)?")) {
                                            onAction && onAction(selectedUnit.id, 'recruit', undefined, undefined, undefined, undefined, undefined, 'hunter');
                                        }
                                    }}
                                    disabled={selectedUnit.has_acted || !canRecruitHunter}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    Recruit Hunter
                                </Button>
                                <Button
                                    variant="contained"
                                    size="small"
                                    color="secondary"
                                    onClick={() => {
                                        if (confirm("Recruit Crafter (10 Food, 9 Turns)?")) {
                                            onAction && onAction(selectedUnit.id, 'recruit', undefined, undefined, undefined, undefined, undefined, 'crafter');
                                        }
                                    }}
                                    disabled={selectedUnit.has_acted || !canRecruitCrafter}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    Recruit Crafter
                                </Button>
                            </>
                        )}

                        {isNearIdol && (
                            <Button
                                variant="contained"
                                size="small"
                                color="secondary"
                                onClick={() => {
                                    if (confirm("Recruit Shaman (12 Food, 12 Turns)?")) {
                                        onAction && onAction(selectedUnit.id, 'recruit', undefined, undefined, undefined, undefined, undefined, 'shaman');
                                    }
                                }}
                                disabled={selectedUnit.has_acted || !canRecruitShaman}
                                sx={{ mt: 1, mr: 1 }}
                            >
                                Recruit Shaman
                            </Button>
                        )}
                    </Box>
                    
                    <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                        {selectedUnit.has_moved ? "Unit has moved this turn" : "Click a tile to move"}
                    </Typography>
                </Paper>
            )}

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
                        
                        {/* Show Resources on Tile */}
                        {(selectedTile as any).resources && Object.keys((selectedTile as any).resources).length > 0 && (
                            <>
                                <Divider sx={{ my: 1 }} />
                                <Typography variant="subtitle2">Resources:</Typography>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {Object.entries((selectedTile as any).resources).map(([res, amt]) => (
                                        <Chip key={res} label={`${res} (${amt})`} size="small" variant="outlined" />
                                    ))}
                                </Box>
                            </>
                        )}

                        {selectedTile.entities && selectedTile.entities.length > 0 && (
                            <>
                                <Divider sx={{ my: 1 }} />
                                <Typography variant="subtitle2">Entities Here:</Typography>
                                <List dense>
                                    {selectedTile.entities.map((ent, i) => (
                                        <ListItem 
                                            key={i} 
                                            disablePadding
                                            secondaryAction={
                                                canHuntTile ? (
                                                    <Button 
                                                        size="small" 
                                                        color="error" 
                                                        variant="outlined"
                                                        onClick={() => {
                                                            if (confirm(`Hunt ${ent.species}?`)) {
                                                                onAction && onAction(selectedUnit!.id, 'hunt', undefined, ent.id);
                                                            }
                                                        }}
                                                    >
                                                        Hunt
                                                    </Button>
                                                ) : null
                                            }
                                        >
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

            {/* Target Selection Dialog */}
            <Dialog open={targetSelectionOpen} onClose={() => setTargetSelectionOpen(false)}>
                <DialogTitle>Select Target</DialogTitle>
                <List sx={{ pt: 0 }}>
                    {availableTargets.map((target) => (
                        <ListItem key={target.id} disablePadding>
                            <ListItemButton onClick={() => {
                                console.log("Selected target from list:", target);
                                onAction && onAction(selectedUnit!.id, 'hunt', undefined, target.id);
                                setTargetSelectionOpen(false);
                            }}>
                                <ListItemText 
                                    primary={target.name} 
                                    secondary={`${target.type} at (${target.x}, ${target.y}) | HP: ${target.hp}/${target.max_hp}`} 
                                />
                            </ListItemButton>
                        </ListItem>
                    ))}
                </List>
            </Dialog>

            {/* Gather Selection Dialog */}
            <Dialog open={gatherSelectionOpen} onClose={() => setGatherSelectionOpen(false)}>
                <DialogTitle>Select Resource</DialogTitle>
                <List sx={{ pt: 0 }}>
                    {availableResources.map((res) => (
                        <ListItem key={res} disablePadding>
                            <ListItemButton onClick={() => {
                                onAction && onAction(selectedUnit!.id, 'gather', res);
                                setGatherSelectionOpen(false);
                            }}>
                                <ListItemText primary={res} />
                            </ListItemButton>
                        </ListItem>
                    ))}
                </List>
            </Dialog>
        </Box>
    );
};

