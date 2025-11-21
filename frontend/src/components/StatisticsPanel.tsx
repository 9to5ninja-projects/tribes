import React from 'react';
import { Paper, Typography, Box } from '@mui/material';

interface StatisticsPanelProps {
    history: {
        herbivores: Record<string, number[]>;
        predators: Record<string, number[]>;
    } | null;
}

const COLORS = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00c49f', '#ffbb28', '#ff8042',
    '#a4de6c', '#d0ed57', '#ffc0cb', '#cddc39', '#ffeb3b', '#ff9800', '#795548', '#607d8b'
];

const SimpleLineChart = ({ data, title }: { data: Record<string, number[]>, title: string }) => {
    if (!data || Object.keys(data).length === 0) return null;

    const speciesList = Object.keys(data);
    const maxLength = Math.max(...speciesList.map(s => data[s].length));
    
    if (maxLength === 0) return <Typography>No data available</Typography>;

    const width = 500;
    const height = 300;
    const padding = 40;
    const graphWidth = width - padding * 2;
    const graphHeight = height - padding * 2;

    // Find max value for scaling
    let maxValue = 0;
    speciesList.forEach(s => {
        const max = Math.max(...data[s]);
        if (max > maxValue) maxValue = max;
    });
    
    // Add some headroom
    maxValue = Math.max(10, maxValue * 1.1);

    return (
        <Box sx={{ mb: 4 }}>
            <Typography variant="h6" align="center" gutterBottom>{title}</Typography>
            <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ border: '1px solid #eee', borderRadius: 4 }}>
                {/* Y Axis */}
                <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#ccc" />
                <text x={padding - 10} y={padding} textAnchor="end" fontSize="10">{Math.round(maxValue)}</text>
                <text x={padding - 10} y={height - padding} textAnchor="end" fontSize="10">0</text>

                {/* X Axis */}
                <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#ccc" />
                <text x={width - padding} y={height - padding + 20} textAnchor="middle" fontSize="10">Turn {maxLength}</text>

                {/* Lines */}
                {speciesList.map((species, index) => {
                    const points = data[species].map((val, i) => {
                        const x = padding + (i / (maxLength - 1)) * graphWidth;
                        const y = height - padding - (val / maxValue) * graphHeight;
                        return `${x},${y}`;
                    }).join(' ');

                    return (
                        <g key={species}>
                            <polyline
                                points={points}
                                fill="none"
                                stroke={COLORS[index % COLORS.length]}
                                strokeWidth="2"
                            />
                        </g>
                    );
                })}
            </svg>
            
            {/* Legend */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 2, mt: 1 }}>
                {speciesList.map((species, index) => (
                    <Box key={species} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Box sx={{ width: 12, height: 12, bgcolor: COLORS[index % COLORS.length] }} />
                        <Typography variant="caption">{species}</Typography>
                    </Box>
                ))}
            </Box>
        </Box>
    );
};

export const StatisticsPanel: React.FC<StatisticsPanelProps> = ({ history }) => {
    if (!history) return <Typography>No statistics available</Typography>;

    return (
        <Paper elevation={0} sx={{ p: 2 }}>
            <SimpleLineChart data={history.herbivores} title="Herbivore Populations" />
            <SimpleLineChart data={history.predators} title="Predator Populations" />
        </Paper>
    );
};
