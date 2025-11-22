import { useState, useCallback, Component, type ErrorInfo, type ReactNode, useEffect } from 'react';
import { Box, Button, Container, Typography, AppBar, Toolbar, CircularProgress, Dialog, DialogTitle, DialogActions, DialogContent, DialogContentText, List, ListItem, ListItemText, ListItemButton, LinearProgress, Chip } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RefreshIcon from '@mui/icons-material/Refresh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import BarChartIcon from '@mui/icons-material/BarChart';
import { gameAPI, type WorldData, type EntityList, type GameStats, type TileInfo, type TribeData, type Unit } from './gameAPI';
import { WorldCanvas } from './components/WorldCanvas';
import { StatsPanel } from './components/StatsPanel';
import { StatisticsPanel } from './components/StatisticsPanel';
import { GameLog, type LogEntry } from './components/GameLog';
import { NewGameDialog } from './components/NewGameDialog';
import { SaveLoadDialog } from './components/SaveLoadDialog';

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean, error: Error | null }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 3, color: 'error.main' }}>
          <Typography variant="h5">Something went wrong.</Typography>
          <Typography variant="body1" sx={{ mt: 1, fontFamily: 'monospace' }}>
            {this.state.error?.toString()}
          </Typography>
          <Button onClick={() => window.location.reload()} sx={{ mt: 2 }}>
            Reload Page
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

type GamePhase = 'MENU' | 'PLAYING';

function App() {
  console.log('App.tsx: Rendering App component');
  const [phase, setPhase] = useState<GamePhase>('MENU');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [worldData, setWorldData] = useState<WorldData | null>(null);
  const [entities, setEntities] = useState<EntityList | null>(null);
  const [stats, setStats] = useState<GameStats | null>(null);
  const [tribeData, setTribeData] = useState<TribeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [selectedTile, setSelectedTile] = useState<TileInfo | null>(null);
  const [selectedCoords, setSelectedCoords] = useState<{x: number, y: number} | null>(null);
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  
  // New Game Options
  const [newGameOpen, setNewGameOpen] = useState(false);

  // Save/Load Dialog
  const [saveLoadOpen, setSaveLoadOpen] = useState(false);
  const [saveLoadMode, setSaveLoadMode] = useState<'save' | 'load'>('save');

  // Build Mode
  const [buildMode, setBuildMode] = useState(false);
  const [buildStructureType, setBuildStructureType] = useState<string | null>(null);
  
  // Tribe Details Dialog
  const [tribeDetailsOpen, setTribeDetailsOpen] = useState(false);
  
  // Statistics Dialog
  const [statsOpen, setStatsOpen] = useState(false);
  
  // Unit Selection Dialog
  const [unitSelectionOpen, setUnitSelectionOpen] = useState(false);
  const [unitsOnTile, setUnitsOnTile] = useState<Unit[]>([]);

  // Movement Confirmation Dialog
  const [moveConfirmation, setMoveConfirmation] = useState<{x: number, y: number, unitId: string} | null>(null);

  const addLog = (message: string, type: 'info' | 'success' | 'error' | 'warning' = 'info') => {
    setLogs(prev => [...prev, {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        message,
        type
    }]);
  };

  // Hotkeys
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (phase !== 'PLAYING' || !tribeData || !tribeData.units) return;

      if (e.key === 'Tab') {
        e.preventDefault();
        // Cycle through units that haven't acted
        const availableUnits = tribeData.units.filter(u => !u.has_acted);
        if (availableUnits.length === 0) return;

        const currentIndex = availableUnits.findIndex(u => u.id === selectedUnitId);
        const nextIndex = (currentIndex + 1) % availableUnits.length;
        const nextUnit = availableUnits[nextIndex];
        
        setSelectedUnitId(nextUnit.id);
        setSelectedCoords({ x: nextUnit.x, y: nextUnit.y });
        
        // Also fetch tile info for the new unit
        gameAPI.getTileInfo(nextUnit.x, nextUnit.y).then(setSelectedTile);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [phase, tribeData, selectedUnitId]);

  const refreshGameState = useCallback(async () => {
    try {
      const [wData, eData, sData, tData] = await Promise.all([
        gameAPI.getWorld(),
        gameAPI.getEntities(),
        gameAPI.getStats(),
        gameAPI.getTribe()
      ]);
      setWorldData(wData);
      setEntities(eData);
      setStats(sData);
      setTribeData(tData);
    } catch (error) {
      console.error("Failed to fetch game state:", error);
    }
  }, []);

  const handleSaveGame = async (filename: string) => {
    try {
        await gameAPI.saveGame(filename);
        addLog(`Game saved as ${filename}`, 'success');
        setSaveLoadOpen(false);
    } catch (error) {
        console.error("Failed to save game:", error);
        addLog(`Failed to save game: ${error}`, 'error');
    }
  };

  const handleLoadGame = async (filename: string) => {
    setLoading(true);
    setLoadingProgress(0);
    addLog(`Loading game ${filename}...`, 'info');
    
    try {
        await gameAPI.loadGame(filename);
        setLoadingProgress(100);
        await refreshGameState();
        setPhase('PLAYING');
        addLog("Game loaded successfully.", 'success');
        setSaveLoadOpen(false);
    } catch (error) {
        console.error("Failed to load game:", error);
        addLog(`Failed to load game: ${error}`, 'error');
    } finally {
        setLoading(false);
    }
  };

  const handleStartGame = async (config: any = {}) => {
    setNewGameOpen(false);
    setLoading(true);
    setLoadingProgress(0);
    addLog("Starting new game...", 'info');
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 90) return prev;
        return prev + 10;
      });
    }, 500);

    try {
      await gameAPI.newGame({
        width: 100,
        height: 80,
        sea_level: 0.42,
        herbivore_population: 120,
        predator_population: 10,
        starting_biome: 'Savanna',
        ...config
      });
      setLoadingProgress(100);
      await refreshGameState();
      setPhase('PLAYING');
      addLog("Game started successfully.", 'success');
    } catch (error) {
      console.error("Failed to start new game:", error);
      addLog(`Failed to start game: ${error}`, 'error');
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  };

  const handleStep = async () => {
    try {
      const stepResult = await gameAPI.step();
      addLog(`Turn advanced.`, 'info');
      
      // Log messages from the server (events, queue updates, etc)
      if (stepResult.messages && Array.isArray(stepResult.messages)) {
          stepResult.messages.forEach((msg: string) => {
              // Determine type based on content
              let type: 'info' | 'success' | 'error' | 'warning' = 'info';
              if (msg.includes('killed') || msg.includes('died')) type = 'error';
              else if (msg.includes('complete') || msg.includes('generated')) type = 'success';
              else if (msg.includes('attacked')) type = 'warning';
              
              addLog(msg, type);
          });
      }

      const [eData, sData, tData] = await Promise.all([
        gameAPI.getEntities(),
        gameAPI.getStats(),
        gameAPI.getTribe()
      ]);
      setEntities(eData);
      setStats(sData);
      setTribeData(tData);
      
      if (selectedCoords) {
        const tInfo = await gameAPI.getTileInfo(selectedCoords.x, selectedCoords.y);
        setSelectedTile(tInfo);
      }
    } catch (error) {
      console.error("Failed to advance turn:", error);
      addLog(`Failed to advance turn: ${error}`, 'error');
    }
  };

  const handleTileClick = async (x: number, y: number) => {
    console.log("Tile clicked:", x, y, "SelectedUnit:", selectedUnitId);
    
    // Build Mode Logic
    if (buildMode && selectedUnitId && buildStructureType) {
      await handleUnitAction(selectedUnitId, 'build', undefined, undefined, buildStructureType, x, y);
      setBuildMode(false);
      setBuildStructureType(null);
      return;
    }

    // If a unit is selected, try to move it
    let isMoveAction = false;
    if (selectedUnitId && tribeData) {
      const unit = tribeData.units.find(u => u.id === selectedUnitId);
      console.log("Attempting move for unit:", unit);
      
      if (unit) {
        if (!unit.has_moved) {
            const dx = x - unit.x;
            const dy = y - unit.y;
            const dist = Math.abs(dx) + Math.abs(dy);
            const range = unit.movement_range || 2;
            
            console.log("Move check:", { dx, dy, dist, range, unitX: unit.x, unitY: unit.y, clickX: x, clickY: y });

            // Check if moving to a new tile within range
            if ((dx !== 0 || dy !== 0) && dist <= range) {
                // Check if there is a target on the tile (for Hunters)
                const hasTarget = entities?.predators?.some(p => p.x === x && p.y === y) || 
                                  entities?.herbivores?.some(h => h.x === x && h.y === y);

                // If it's a hunter and there's a target, don't prompt move immediately
                // This allows clicking to inspect/hunt without the dialog blocking it
                if (unit.type === 'hunter' && hasTarget) {
                    console.log("Click on target with hunter - skipping move confirmation to allow inspection");
                    addLog("Target selected. Use Hunt button to attack.", 'info');
                } else {
                    setMoveConfirmation({x, y, unitId: selectedUnitId});
                    isMoveAction = true;
                }
                // Do not return here; allow fall-through to inspect the tile
                // This allows the user to Cancel the move dialog and still see the tile info (e.g. to Hunt)
            }
        }
        // If unit has moved or clicked out of range, fall through to inspection
      } else {
        console.log("Unit not found in tribeData");
      }
    }

    // Otherwise inspect tile
    setSelectedCoords({x, y});
    
    // Check if we clicked a unit
    // Only select new unit if we are NOT in the middle of a move action
    if (!isMoveAction) {
        const clickedUnits = tribeData?.units?.filter(u => u.x === x && u.y === y) || [];
        
        if (clickedUnits.length > 1) {
          // Multiple units - open dialog
          setUnitsOnTile(clickedUnits);
          setUnitSelectionOpen(true);
          setSelectedUnitId(null);
        } else if (clickedUnits.length === 1) {
          // Single unit - select it
          setSelectedUnitId(clickedUnits[0].id);
        } else {
          // No unit on this tile
          // Only deselect if we are NOT inspecting a tile within range of the currently selected unit
          // This allows "Targeted Hunting" where we select a hunter, then click a target tile
          if (selectedUnitId && tribeData) {
            const unit = tribeData.units.find(u => u.id === selectedUnitId);
            if (unit) {
                const dist = Math.abs(unit.x - x) + Math.abs(unit.y - y);
                // If within interaction range (2 for hunt/move), keep selected
                if (dist <= 2) {
                    // Keep selected
                } else {
                    setSelectedUnitId(null);
                }
            } else {
                setSelectedUnitId(null);
            }
          } else {
            setSelectedUnitId(null);
          }
        }
    }

    try {
      const info = await gameAPI.getTileInfo(x, y);
      setSelectedTile(info);
    } catch (error) {
      console.error("Failed to get tile info:", error);
    }
  };

  const handleConfirmMove = async () => {
    if (!moveConfirmation) return;
    
    const { x, y, unitId } = moveConfirmation;
    const unit = tribeData?.units.find(u => u.id === unitId);
    if (!unit) return;

    const dx = x - unit.x;
    const dy = y - unit.y;

    try {
        addLog(`Moving ${unit.name} to (${x}, ${y})...`, 'info');
        const result = await gameAPI.moveUnit(unitId, dx, dy);
        if (result.error) {
            addLog(`Move failed: ${result.error}`, 'error');
        } else {
            addLog(`${unit.name} moved to (${x}, ${y})`, 'success');
            // Refresh tribe data to show new position
            const [tData, eData] = await Promise.all([
                gameAPI.getTribe(),
                gameAPI.getEntities()
            ]);
            setTribeData(tData);
            setEntities(eData);
            
            // Check if unit can still act
            const updatedUnit = tData.units.find((u: Unit) => u.id === unitId);
            if (updatedUnit && !updatedUnit.has_acted) {
                // Keep selected
                setSelectedUnitId(unitId);
                // Update tile info for new location
                const tInfo = await gameAPI.getTileInfo(x, y);
                setSelectedTile(tInfo);
                setSelectedCoords({x, y});
            } else {
                setSelectedUnitId(null); // Deselect if acted or not found
            }
        }
    } catch (e) {
        console.error("Move failed", e);
        addLog(`Move failed: ${e}`, 'error');
    } finally {
        setMoveConfirmation(null);
    }
  };

  const handleUnitSelectFromDialog = (unitId: string) => {
    console.log("Unit selected from dialog:", unitId);
    addLog(`Selected unit ${unitId} from stack`, 'info');
    setSelectedUnitId(unitId);
    setUnitSelectionOpen(false);
  };

  const handleUnitAction = async (unitId: string, action: string, target?: string, targetId?: string, structureType?: string, buildX?: number, buildY?: number, unitType?: string) => {
    try {
      const unit = tribeData?.units.find(u => u.id === unitId);
      const unitName = unit ? unit.name : 'Unit';

      const result = await gameAPI.unitAction(unitId, action, target, targetId, structureType, buildX, buildY, unitType);
      
      if (result.error) {
          addLog(`${unitName}: Action '${action}' failed: ${result.error}`, 'error');
      } else {
          addLog(result.message || `${unitName}: Action '${action}' successful`, 'success');
          if (result.gathered) {
              addLog(`${unitName} gathered ${result.gathered} ${result.resource}`, 'success');
          }
          if (result.damage) {
              const targetName = result.target_species || 'Target';
              addLog(`${unitName} dealt ${result.damage} damage to ${targetName}`, 'success');
              
              if (!result.kill && result.target_hp !== undefined) {
                  addLog(`${targetName} has ${result.target_hp} HP remaining.`, 'warning');
              }
          }
          if (result.kill) {
              const targetInfo = result.target_species ? `${result.target_species} at (${result.target_location[0]}, ${result.target_location[1]})` : 'Target';
              addLog(`${targetInfo} killed! (+${result.food_gain} food)`, 'success');
              
              // Refresh entities to remove dead ones
              const eData = await gameAPI.getEntities();
              setEntities(eData);
          }
      }

      // Refresh tribe data to show updated stockpile/energy
      const tData = await gameAPI.getTribe();
      setTribeData(tData);
      
      // Also refresh tile info if we gathered resources (they might be depleted)
      if (selectedCoords) {
        const tInfo = await gameAPI.getTileInfo(selectedCoords.x, selectedCoords.y);
        setSelectedTile(tInfo);
      }
    } catch (error) {
      console.error("Action failed:", error);
      addLog(`Action failed: ${error}`, 'error');
    }
  };
  return (
    <ErrorBoundary>
      <Box sx={{ flexGrow: 1, height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Tribes
            </Typography>
            {phase === 'MENU' ? (
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <Button color="inherit" startIcon={<PlayArrowIcon />} onClick={() => setNewGameOpen(true)}>
                        New Game
                    </Button>
                    <Button color="inherit" onClick={() => { setSaveLoadMode('load'); setSaveLoadOpen(true); }}>
                        Load Game
                    </Button>
                </Box>
            ) : (
                <>
                    <Button color="inherit" onClick={() => { setSaveLoadMode('save'); setSaveLoadOpen(true); }}>
                        Save
                    </Button>
                    <Button color="inherit" onClick={() => { setSaveLoadMode('load'); setSaveLoadOpen(true); }}>
                        Load
                    </Button>
                    <Button color="inherit" startIcon={<BarChartIcon />} onClick={() => setStatsOpen(true)}>
                        Stats
                    </Button>
                    <Button color="inherit" startIcon={<RefreshIcon />} onClick={handleStep}>
                        Next Turn
                    </Button>
                    <Button color="inherit" startIcon={<ArrowBackIcon />} onClick={() => setPhase('MENU')}>
                        Menu
                    </Button>
                </>
            )}
          </Toolbar>
        </AppBar>

        {loading && (
            <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, bgcolor: 'rgba(0,0,0,0.7)', zIndex: 9999, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <CircularProgress size={60} />
                <Typography variant="h6" sx={{ mt: 2, color: 'white' }}>Generating World...</Typography>
                <Box sx={{ width: '50%', mt: 2 }}>
                    <LinearProgress variant="determinate" value={loadingProgress} />
                </Box>
            </Box>
        )}

        <Container maxWidth={false} sx={{ flexGrow: 1, display: 'flex', overflow: 'hidden', p: 2, gap: 2 }}>
          <Box sx={{ flexGrow: 1, overflow: 'hidden', border: '1px solid #ccc', borderRadius: 1, position: 'relative' }}>
             {worldData && entities && (
                 <WorldCanvas 
                    worldData={worldData}
                    entities={entities}
                    onTileClick={handleTileClick}
                    selectedUnitId={selectedUnitId}
                    tribeData={tribeData}
                 />
             )}
          </Box>

          <StatsPanel 
            stats={stats} 
            tribeData={tribeData}
            selectedTile={selectedTile}
            selectedCoords={selectedCoords}
            selectedUnitId={selectedUnitId}
            entities={entities}
            onAction={handleUnitAction}
            onEnterBuildMode={(type) => {
                setBuildMode(true);
                setBuildStructureType(type);
                addLog(`Select an adjacent tile to build ${type}`, 'info');
            }}
            onOpenTribeDetails={() => setTribeDetailsOpen(true)}
            onLog={(msg) => addLog(msg, 'info')}
          />
          
          <Box sx={{ width: 300, display: 'flex', flexDirection: 'column' }}>
             <GameLog logs={logs} />
          </Box>
        </Container>

        {/* New Game Dialog */}
        <NewGameDialog
            open={newGameOpen}
            onClose={() => setNewGameOpen(false)}
            onStart={handleStartGame}
        />

        {/* Save/Load Dialog */}
        <SaveLoadDialog
            open={saveLoadOpen}
            mode={saveLoadMode}
            onClose={() => setSaveLoadOpen(false)}
            onSave={handleSaveGame}
            onLoad={handleLoadGame}
        />

        {/* Move Confirmation Dialog */}
        <Dialog open={!!moveConfirmation} onClose={() => setMoveConfirmation(null)}>
            <DialogTitle>Confirm Movement</DialogTitle>
            <DialogContent>
                <DialogContentText>
                    Move unit to ({moveConfirmation?.x}, {moveConfirmation?.y})?
                </DialogContentText>
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setMoveConfirmation(null)}>Cancel</Button>
                <Button onClick={handleConfirmMove} autoFocus variant="contained">
                    Confirm
                </Button>
            </DialogActions>
        </Dialog>

        {/* Unit Selection Dialog */}
        <Dialog open={unitSelectionOpen} onClose={() => setUnitSelectionOpen(false)}>
          <DialogTitle>Select Unit</DialogTitle>
          <List sx={{ pt: 0 }}>
            {unitsOnTile.map((unit) => (
              <ListItem key={unit.id} disablePadding>
                <ListItemButton onClick={() => handleUnitSelectFromDialog(unit.id)}>
                  <ListItemText 
                    primary={unit.name} 
                    secondary={`${unit.type} | HP: ${unit.hp} | ${unit.has_acted ? 'Acted' : 'Ready'}`} 
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Dialog>

        {/* Tribe Details Dialog */}
        <Dialog open={tribeDetailsOpen} onClose={() => setTribeDetailsOpen(false)} maxWidth="md" fullWidth>
            <DialogTitle>Tribe Details</DialogTitle>
            <Box sx={{ p: 2 }}>
                {tribeData && tribeData.stockpile && (
                    <>
                        <Typography variant="h6">Stockpile</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                            {Object.entries(tribeData.stockpile).map(([res, amount]) => (
                                <Chip key={res} label={`${res}: ${amount}`} />
                            ))}
                        </Box>
                        
                        {tribeData.units && (
                            <>
                                <Typography variant="h6">Units ({tribeData.units.length})</Typography>
                                <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                                    {tribeData.units.map(u => (
                                        <ListItem key={u.id}>
                                            <ListItemText 
                                                primary={u.name} 
                                                secondary={`${u.type} | HP: ${u.hp} | Energy: ${u.energy}`} 
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            </>
                        )}
                    </>
                )}
            </Box>
        </Dialog>

        {/* Statistics Dialog */}
        <Dialog open={statsOpen} onClose={() => setStatsOpen(false)} maxWidth="lg" fullWidth>
            <DialogTitle>World Statistics</DialogTitle>
            <DialogContent>
                <StatisticsPanel 
                    history={(stats as any)?.history} 
                    deathCauses={(stats as any)?.death_causes}
                    foodChain={(stats as any)?.food_chain}
                />
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setStatsOpen(false)}>Close</Button>
            </DialogActions>
        </Dialog>
      </Box>
    </ErrorBoundary>
  );
}

export default App;

