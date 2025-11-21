import React, { useState } from 'react';
import { Box, Button, Typography, Container, Paper } from '@mui/material';
import LandscapeIcon from '@mui/icons-material/Landscape';

interface MainMenuProps {
    onStartGame: (config: any) => void;
}

export const MainMenu: React.FC<MainMenuProps> = ({ onStartGame }) => {
    const [units] = useState({
        gatherer: 2,
        hunter: 1,
        crafter: 0,
        shaman: 0
    });

    /*
    const handleUnitChange = (type: string) => (_event: Event, newValue: number | number[]) => {
        setUnits({ ...units, [type]: newValue as number });
    };
    */

    const handleStart = () => {
        onStartGame({
            starting_units: units
        });
    };

    return (
        <Box sx={{ 
            height: '100vh', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            bgcolor: '#1a1a1a',
            color: 'white'
        }}>
            <Container maxWidth="md">
                <Paper elevation={6} sx={{ p: 6, textAlign: 'center', bgcolor: '#2d2d2d', color: 'white' }}>
                    <LandscapeIcon sx={{ fontSize: 80, mb: 2, color: '#4caf50' }} />
                    <Typography variant="h2" gutterBottom sx={{ fontWeight: 'bold' }}>
                        TRIBES
                    </Typography>
                    <Typography variant="h5" gutterBottom sx={{ mb: 4, color: '#aaa' }}>
                        Evolution Simulator
                    </Typography>
                    
                    <Box sx={{ mb: 4, textAlign: 'left', bgcolor: '#333', p: 3, borderRadius: 2 }}>
                        <Typography variant="h6" gutterBottom sx={{ color: '#4caf50' }}>Starting Tribe Configuration</Typography>
                        {/* Grid removed to fix build error
                        <Grid container spacing={4}>
                            {Object.entries(units).map(([type, count]) => (
                                <div key={type}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <Typography gutterBottom sx={{ textTransform: 'capitalize' }}>
                                            {type}s
                                        </Typography>
                                        <Typography gutterBottom sx={{ fontWeight: 'bold' }}>
                                            {count}
                                        </Typography>
                                    </Box>
                                    <Slider
                                        value={count}
                                        onChange={handleUnitChange(type)}
                                        min={0}
                                        max={10}
                                        step={1}
                                        marks
                                        valueLabelDisplay="auto"
                                        sx={{ color: '#4caf50' }}
                                    />
                                </div>
                            ))}
                        </Grid>
                        */}
                    </Box>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <Button 
                            variant="contained" 
                            size="large" 
                            color="primary" 
                            onClick={handleStart}
                            sx={{ py: 2, fontSize: '1.2rem' }}
                        >
                            Start New World
                        </Button>
                        <Button variant="outlined" size="large" disabled sx={{ color: '#aaa', borderColor: '#555' }}>
                            Load World (Coming Soon)
                        </Button>
                        <Button variant="outlined" size="large" disabled sx={{ color: '#aaa', borderColor: '#555' }}>
                            Tribe Editor (Coming Soon)
                        </Button>
                    </Box>
                </Paper>
            </Container>
        </Box>
    );
};
