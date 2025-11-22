import React from 'react';
import { Paper, Typography, Box } from '@mui/material';

interface StatisticsPanelProps {
    history: {
        herbivores: Record<string, number[]>;
        predators: Record<string, number[]>;
        scavengers: number[];
        avian: number[];
        aquatic: number[];
        nomads?: number[];
        tribe: {
            total: number[];
            gatherer: number[];
            hunter: number[];
            crafter: number[];
            shaman: number[];
        };
    } | null;
    deathCauses?: Record<string, Record<string, number>>;
    foodChain?: Record<string, Record<string, number>>;
}

const COLORS = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00c49f', '#ffbb28', '#ff8042',
    '#a4de6c', '#d0ed57', '#ffc0cb', '#cddc39', '#ffeb3b', '#ff9800', '#795548', '#607d8b'
];

const SimpleLineChart = ({ data, title, isSimpleList = false, extraSeries = [] }: { data: any, title: string, isSimpleList?: boolean, extraSeries?: {name: string, data: number[]}[] }) => {
    if (!data) return null;
    
    let speciesList: string[] = [];
    let maxLength = 0;
    
    if (isSimpleList) {
        if (data.length === 0) return <Typography>No data available</Typography>;
        speciesList = ['Population'];
        maxLength = data.length;
    } else {
        if (Object.keys(data).length === 0) return null;
        speciesList = Object.keys(data);
        maxLength = Math.max(...speciesList.map(s => data[s].length));
    }
    
    // Handle extra series (like Nomads)
    if (extraSeries.length > 0) {
        extraSeries.forEach(s => {
            if (s.data.length > maxLength) maxLength = s.data.length;
            speciesList.push(s.name);
        });
    }
    
    if (maxLength === 0) return <Typography>No data available</Typography>;

    const width = 500;
    const height = 300;
    const padding = 40;
    const graphWidth = width - padding * 2;
    const graphHeight = height - padding * 2;

    // Find max value for scaling
    let maxValue = 0;
    if (isSimpleList) {
        maxValue = Math.max(...data);
    } else {
        // Check main data
        if (!isSimpleList && typeof data === 'object') {
             Object.keys(data).forEach(s => {
                const max = Math.max(...data[s]);
                if (max > maxValue) maxValue = max;
            });
        }
    }
    
    // Check extra series max
    extraSeries.forEach(s => {
        const max = Math.max(...s.data);
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
                    let seriesData: number[] = [];
                    
                    // Check if it's an extra series
                    const extra = extraSeries.find(s => s.name === species);
                    if (extra) {
                        seriesData = extra.data;
                    } else if (isSimpleList) {
                        seriesData = data;
                    } else {
                        seriesData = data[species];
                    }
                    
                    if (!seriesData) return null;

                    const points = seriesData.map((val: number, i: number) => {
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

export const StatisticsPanel: React.FC<StatisticsPanelProps> = ({ history, deathCauses, foodChain }) => {
    if (!history) return <Typography>No statistics available</Typography>;

    return (
        <Paper elevation={0} sx={{ p: 2 }}>
            <SimpleLineChart 
                data={history.tribe} 
                title="Human Population" 
                extraSeries={history.nomads ? [{name: 'Nomads', data: history.nomads}] : []}
            />
            <SimpleLineChart data={history.herbivores} title="Herbivore Populations" />
            <SimpleLineChart data={history.predators} title="Predator Populations" />
            <SimpleLineChart data={history.avian} title="Avian Population" isSimpleList={true} />
            <SimpleLineChart data={history.aquatic} title="Aquatic Population" isSimpleList={true} />
            <SimpleLineChart data={history.scavengers} title="Scavenger Population" isSimpleList={true} />

            {deathCauses && Object.keys(deathCauses).length > 0 && (
                <Box sx={{ mt: 4 }}>
                    <Typography variant="h6" gutterBottom>Causes of Death</Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 2 }}>
                        {Object.entries(deathCauses).map(([species, causes]) => (
                            <Paper key={species} variant="outlined" sx={{ p: 2 }}>
                                <Typography variant="subtitle1" sx={{ textTransform: 'capitalize', fontWeight: 'bold' }}>{species}</Typography>
                                {Object.entries(causes)
                                    .sort(([, a], [, b]) => b - a)
                                    .map(([cause, count]) => (
                                        <Box key={cause} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="body2" color="text.secondary">{cause}</Typography>
                                            <Typography variant="body2">{count}</Typography>
                                        </Box>
                                    ))}
                            </Paper>
                        ))}
                    </Box>
                </Box>
            )}

            {foodChain && Object.keys(foodChain).length > 0 && (
                <Box sx={{ mt: 4 }}>
                    <Typography variant="h6" gutterBottom>Food Chain (Predation)</Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 2 }}>
                        {Object.entries(foodChain).map(([predator, preyMap]) => (
                            <Paper key={predator} variant="outlined" sx={{ p: 2 }}>
                                <Typography variant="subtitle1" sx={{ textTransform: 'capitalize', fontWeight: 'bold' }}>{predator} eats...</Typography>
                                {Object.entries(preyMap)
                                    .sort(([, a], [, b]) => b - a)
                                    .map(([prey, count]) => (
                                        <Box key={prey} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <Typography variant="body2" color="text.secondary">{prey}</Typography>
                                            <Typography variant="body2">{count}</Typography>
                                        </Box>
                                    ))}
                            </Paper>
                        ))}
                    </Box>
                </Box>
            )}
        </Paper>
    );
};
