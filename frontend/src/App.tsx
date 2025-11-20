import { useState, useCallback, Component, type ErrorInfo, type ReactNode } from 'react';
import { Box, Button, Container, Typography, AppBar, Toolbar, CircularProgress } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RefreshIcon from '@mui/icons-material/Refresh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { gameAPI, type WorldData, type EntityList, type GameStats, type TileInfo } from './gameAPI';
import { WorldCanvas } from './components/WorldCanvas';
import { StatsPanel } from './components/StatsPanel';
import { MainMenu } from './components/MainMenu';

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
  const [phase, setPhase] = useState<GamePhase>('MENU');
  const [worldData, setWorldData] = useState<WorldData | null>(null);
  const [entities, setEntities] = useState<EntityList | null>(null);
  const [stats, setStats] = useState<GameStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTile, setSelectedTile] = useState<TileInfo | null>(null);
  const [selectedCoords, setSelectedCoords] = useState<{x: number, y: number} | null>(null);

  const refreshGameState = useCallback(async () => {
    try {
      const [wData, eData, sData] = await Promise.all([
        gameAPI.getWorld(),
        gameAPI.getEntities(),
        gameAPI.getStats()
      ]);
      setWorldData(wData);
      setEntities(eData);
      setStats(sData);
    } catch (error) {
      console.error("Failed to fetch game state:", error);
    }
  }, []);

  const handleStartGame = async () => {
    setLoading(true);
    try {
      await gameAPI.newGame({
        width: 100,
        height: 80,
        sea_level: 0.42,
        herbivore_population: 120,
        predator_population: 10
      });
      await refreshGameState();
      setPhase('PLAYING');
    } catch (error) {
      console.error("Failed to start new game:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStep = async () => {
    try {
      await gameAPI.step();
      const [eData, sData] = await Promise.all([
        gameAPI.getEntities(),
        gameAPI.getStats()
      ]);
      setEntities(eData);
      setStats(sData);
      
      if (selectedCoords) {
        const tInfo = await gameAPI.getTileInfo(selectedCoords.x, selectedCoords.y);
        setSelectedTile(tInfo);
      }
    } catch (error) {
      console.error("Failed to advance turn:", error);
    }
  };

  const handleTileClick = async (x: number, y: number) => {
    setSelectedCoords({x, y});
    try {
      const info = await gameAPI.getTileInfo(x, y);
      setSelectedTile(info);
    } catch (error) {
      console.error("Failed to get tile info:", error);
    }
  };

  const handleBackToMenu = () => {
    setPhase('MENU');
    setWorldData(null);
    setEntities(null);
    setStats(null);
  };

  if (phase === 'MENU') {
    return (
      <ErrorBoundary>
        {loading ? (
          <Box sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', bgcolor: '#1a1a1a', color: 'white' }}>
            <CircularProgress color="inherit" />
            <Typography sx={{ mt: 2 }}>Generating World...</Typography>
          </Box>
        ) : (
          <MainMenu onStartGame={handleStartGame} />
        )}
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#f5f5f5' }}>
        <AppBar position="static" color="default" elevation={1}>
          <Toolbar>
            <Button startIcon={<ArrowBackIcon />} onClick={handleBackToMenu} sx={{ mr: 2 }}>
              Menu
            </Button>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Tribes Evolution Sim
            </Typography>
            <Button color="primary" startIcon={<RefreshIcon />} onClick={handleStartGame} disabled={loading}>
              Regenerate
            </Button>
          </Toolbar>
        </AppBar>

        <Container maxWidth="xl" sx={{ mt: 2, flex: 1, display: 'flex', gap: 2, overflow: 'auto' }}>
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
              <Button 
                variant="contained" 
                color="primary" 
                size="large"
                startIcon={<PlayArrowIcon />}
                onClick={handleStep}
                disabled={loading || !worldData}
              >
                Next Turn
              </Button>
            </Box>
            
            {loading ? (
              <CircularProgress />
            ) : (
              <WorldCanvas 
                worldData={worldData} 
                entities={entities} 
                onTileClick={handleTileClick}
              />
            )}
          </Box>

          <StatsPanel 
            stats={stats} 
            selectedTile={selectedTile}
            selectedCoords={selectedCoords}
          />
        </Container>
      </Box>
    </ErrorBoundary>
  );
}

export default App;

