import React from 'react';
import { Box, Button, Typography, Container, Paper } from '@mui/material';
import LandscapeIcon from '@mui/icons-material/Landscape';

interface MainMenuProps {
    onStartGame: () => void;
}

export const MainMenu: React.FC<MainMenuProps> = ({ onStartGame }) => {
    return (
        <Box sx={{ 
            height: '100vh', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            bgcolor: '#1a1a1a',
            color: 'white'
        }}>
            <Container maxWidth="sm">
                <Paper elevation={6} sx={{ p: 6, textAlign: 'center', bgcolor: '#2d2d2d', color: 'white' }}>
                    <LandscapeIcon sx={{ fontSize: 80, mb: 2, color: '#4caf50' }} />
                    <Typography variant="h2" gutterBottom sx={{ fontWeight: 'bold' }}>
                        TRIBES
                    </Typography>
                    <Typography variant="h5" gutterBottom sx={{ mb: 4, color: '#aaa' }}>
                        Evolution Simulator
                    </Typography>
                    
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <Button 
                            variant="contained" 
                            size="large" 
                            color="primary" 
                            onClick={onStartGame}
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
