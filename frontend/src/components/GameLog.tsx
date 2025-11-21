import React, { useEffect, useRef } from 'react';
import { Paper, Typography, List, ListItem, ListItemText } from '@mui/material';

export interface LogEntry {
    id: number;
    timestamp: string;
    message: string;
    type: 'info' | 'success' | 'error' | 'warning';
}

interface GameLogProps {
    logs: LogEntry[];
}

export const GameLog: React.FC<GameLogProps> = ({ logs }) => {
    const endRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <Paper elevation={3} sx={{ height: 150, overflow: 'auto', p: 1, bgcolor: '#212121', color: '#eee', mt: 2 }}>
            <Typography variant="subtitle2" sx={{ borderBottom: '1px solid #444', mb: 1, color: '#aaa' }}>Game Log</Typography>
            <List dense disablePadding>
                {logs.map((log) => (
                    <ListItem key={log.id} disablePadding sx={{ py: 0.25 }}>
                        <ListItemText
                            primary={
                                <Typography variant="caption" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                    <span style={{ color: '#666' }}>[{log.timestamp}]</span>{' '}
                                    <span style={{
                                        color: log.type === 'error' ? '#ff5252' :
                                               log.type === 'success' ? '#69f0ae' :
                                               log.type === 'warning' ? '#ffd740' : '#e0e0e0'
                                    }}>
                                        {log.message}
                                    </span>
                                </Typography>
                            }
                        />
                    </ListItem>
                ))}
                <div ref={endRef} />
            </List>
        </Paper>
    );
};
