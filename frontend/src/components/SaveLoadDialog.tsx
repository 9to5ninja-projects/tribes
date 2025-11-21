import React, { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, List, ListItem, ListItemText, IconButton, Typography, Tabs, Tab, Box, ListItemButton } from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import UploadIcon from '@mui/icons-material/Upload';
import { gameAPI } from '../gameAPI';

interface SaveLoadDialogProps {
    open: boolean;
    mode: 'save' | 'load';
    onClose: () => void;
    onSave: (filename: string) => void;
    onLoad: (filename: string) => void;
}

export const SaveLoadDialog: React.FC<SaveLoadDialogProps> = ({ open, mode, onClose, onSave, onLoad }) => {
    const [saves, setSaves] = useState<string[]>([]);
    const [filename, setFilename] = useState('');
    const [tabValue, setTabValue] = useState(mode === 'save' ? 0 : 1);

    useEffect(() => {
        if (open) {
            refreshSaves();
            setTabValue(mode === 'save' ? 0 : 1);
        }
    }, [open, mode]);

    const refreshSaves = async () => {
        try {
            const response = await gameAPI.listSaves();
            setSaves(response.saves);
        } catch (error) {
            console.error("Failed to list saves:", error);
        }
    };

    const handleSave = () => {
        if (filename) {
            onSave(filename);
            setFilename('');
        }
    };

    const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
        setTabValue(newValue);
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>
                {tabValue === 0 ? 'Save Game' : 'Load Game'}
            </DialogTitle>
            <DialogContent>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                    <Tabs value={tabValue} onChange={handleTabChange} aria-label="save load tabs">
                        <Tab label="Save" />
                        <Tab label="Load" />
                    </Tabs>
                </Box>

                {tabValue === 0 && (
                    <Box sx={{ mt: 2 }}>
                        <TextField
                            autoFocus
                            margin="dense"
                            label="Save Filename"
                            fullWidth
                            variant="outlined"
                            value={filename}
                            onChange={(e) => setFilename(e.target.value)}
                            placeholder="my_save_game"
                        />
                        <Typography variant="caption" color="textSecondary">
                            Existing saves:
                        </Typography>
                        <List dense>
                            {saves.map((save) => (
                                <ListItem key={save} disablePadding>
                                    <ListItemButton onClick={() => setFilename(save.replace('.json', ''))}>
                                        <ListItemText primary={save} />
                                    </ListItemButton>
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}

                {tabValue === 1 && (
                    <List>
                        {saves.length === 0 ? (
                            <Typography color="textSecondary" align="center" sx={{ py: 2 }}>
                                No saved games found.
                            </Typography>
                        ) : (
                            saves.map((save) => (
                                <ListItem key={save} disablePadding
                                    secondaryAction={
                                        <IconButton edge="end" aria-label="load" onClick={() => onLoad(save)}>
                                            <UploadIcon />
                                        </IconButton>
                                    }
                                >
                                    <ListItemButton onClick={() => onLoad(save)}>
                                        <ListItemText primary={save} />
                                    </ListItemButton>
                                </ListItem>
                            ))
                        )}
                    </List>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Cancel</Button>
                {tabValue === 0 && (
                    <Button onClick={handleSave} variant="contained" color="primary" startIcon={<SaveIcon />}>
                        Save
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
};
