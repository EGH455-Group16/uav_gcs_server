// Socket.IO connection
const ns = "/stream";
const socket = io(ns, { 
    transports: ["websocket", "polling"],
    autoConnect: true,
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5,
    timeout: 20000,
    forceNew: false
});

// Chart configuration
const MAX_DATA_POINTS = 100;
let dataPointCount = 0;

// Chart instances
const charts = {};

// Data storage
const chartData = {
    co: { labels: [], data: [] },
    no2: { labels: [], data: [] },
    nh3: { labels: [], data: [] },
    temp: { labels: [], data: [] },
    press: { labels: [], data: [] },
    hum: { labels: [], data: [] },
    light: { labels: [], data: [] }
};

// Chart colors (light theme)
const chartColors = {
    co: {
        border: '#FF9800',
        background: 'rgba(255, 152, 0, 0.1)',
        gradient: ['rgba(255, 152, 0, 0.3)', 'rgba(255, 152, 0, 0.05)']
    },
    no2: {
        border: '#FF9800',
        background: 'rgba(255, 152, 0, 0.1)',
        gradient: ['rgba(255, 152, 0, 0.3)', 'rgba(255, 152, 0, 0.05)']
    },
    nh3: {
        border: '#FF9800',
        background: 'rgba(255, 152, 0, 0.1)',
        gradient: ['rgba(255, 152, 0, 0.3)', 'rgba(255, 152, 0, 0.05)']
    },
    temp: {
        border: '#4CAF50',
        background: 'rgba(76, 175, 80, 0.1)',
        gradient: ['rgba(76, 175, 80, 0.3)', 'rgba(76, 175, 80, 0.05)']
    },
    press: {
        border: '#4CAF50',
        background: 'rgba(76, 175, 80, 0.1)',
        gradient: ['rgba(76, 175, 80, 0.3)', 'rgba(76, 175, 80, 0.05)']
    },
    hum: {
        border: '#4CAF50',
        background: 'rgba(76, 175, 80, 0.1)',
        gradient: ['rgba(76, 175, 80, 0.3)', 'rgba(76, 175, 80, 0.05)']
    },
    light: {
        border: '#4CAF50',
        background: 'rgba(76, 175, 80, 0.1)',
        gradient: ['rgba(76, 175, 80, 0.3)', 'rgba(76, 175, 80, 0.05)']
    }
};

// Create gradient
function createGradient(ctx, colors) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, colors[0]);
    gradient.addColorStop(1, colors[1]);
    return gradient;
}

// Initialize a chart
function initChart(canvasId, label, color, unit) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas ${canvasId} not found`);
        return null;
    }
    
    const ctx = canvas.getContext('2d');
    const gradient = createGradient(ctx, color.gradient);
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: color.border,
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: color.border,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#333',
                    bodyColor: '#333',
                    borderColor: color.border,
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return `${label}: ${context.parsed.y.toFixed(2)} ${unit}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#666',
                        font: {
                            size: 10
                        },
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 8
                    }
                },
                y: {
                    display: true,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#666',
                        font: {
                            size: 10
                        },
                        callback: function(value) {
                            return value.toFixed(1);
                        }
                    }
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        }
    });
    
    return chart;
}

// Initialize all charts
function initAllCharts() {
    charts.co = initChart('chart-co', 'CO', chartColors.co, 'ppm');
    charts.no2 = initChart('chart-no2', 'NO₂', chartColors.no2, 'ppm');
    charts.nh3 = initChart('chart-nh3', 'NH₃', chartColors.nh3, 'ppm');
    charts.temp = initChart('chart-temp', 'Temperature', chartColors.temp, '°C');
    charts.press = initChart('chart-press', 'Pressure', chartColors.press, 'hPa');
    charts.hum = initChart('chart-hum', 'Humidity', chartColors.hum, '%');
    charts.light = initChart('chart-light', 'Light', chartColors.light, 'lux');
    
    console.log('All charts initialized');
}

// Format timestamp for display
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
    });
}

// Update a chart with new data
function updateChart(chartKey, label, value) {
    const chart = charts[chartKey];
    if (!chart) return;
    
    const data = chartData[chartKey];
    
    // Add new data point
    data.labels.push(label);
    data.data.push(value);
    
    // Remove oldest point if exceeding max
    if (data.labels.length > MAX_DATA_POINTS) {
        data.labels.shift();
        data.data.shift();
    }
    
    // Update chart
    chart.data.labels = data.labels;
    chart.data.datasets[0].data = data.data;
    chart.update('none'); // 'none' for smooth updates without animation on each point
}

// Update all charts with sensor data
function updateAllCharts(sensorData) {
    const timestamp = sensorData.ts ? new Date(sensorData.ts) : new Date();
    const timeLabel = formatTime(timestamp);
    
    if (sensorData.co_ppm !== undefined && sensorData.co_ppm !== null) {
        updateChart('co', timeLabel, sensorData.co_ppm);
        updateValueDisplay('co', sensorData.co_ppm, 2);
    }
    
    if (sensorData.no2_ppm !== undefined && sensorData.no2_ppm !== null) {
        updateChart('no2', timeLabel, sensorData.no2_ppm);
        updateValueDisplay('no2', sensorData.no2_ppm, 2);
    }
    
    if (sensorData.nh3_ppm !== undefined && sensorData.nh3_ppm !== null) {
        updateChart('nh3', timeLabel, sensorData.nh3_ppm);
        updateValueDisplay('nh3', sensorData.nh3_ppm, 2);
    }
    
    if (sensorData.temp_c !== undefined && sensorData.temp_c !== null) {
        updateChart('temp', timeLabel, sensorData.temp_c);
        updateValueDisplay('temp', sensorData.temp_c, 1);
    }
    
    if (sensorData.pressure_hpa !== undefined && sensorData.pressure_hpa !== null) {
        updateChart('press', timeLabel, sensorData.pressure_hpa);
        updateValueDisplay('press', sensorData.pressure_hpa, 1);
    }
    
    if (sensorData.humidity_pct !== undefined && sensorData.humidity_pct !== null) {
        updateChart('hum', timeLabel, sensorData.humidity_pct);
        updateValueDisplay('hum', sensorData.humidity_pct, 1);
    }
    
    if (sensorData.light_lux !== undefined && sensorData.light_lux !== null) {
        updateChart('light', timeLabel, sensorData.light_lux);
        updateValueDisplay('light', sensorData.light_lux, 0);
    }
    
    dataPointCount++;
    updateStatus();
}

// Update value display
function updateValueDisplay(sensor, value, decimals) {
    const element = document.getElementById(`chart-value-${sensor}`);
    if (element) {
        element.textContent = value.toFixed(decimals);
    }
}

// Update status indicators
function updateStatus() {
    const lastUpdateElement = document.getElementById('graph-last-update');
    const dataPointsElement = document.getElementById('graph-data-points');
    
    if (lastUpdateElement) {
        lastUpdateElement.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
    }
    
    if (dataPointsElement) {
        dataPointsElement.textContent = `Data points: ${dataPointCount}`;
    }
}

// Load historical data
async function loadHistoricalData() {
    try {
        const response = await fetch('/api/sensor-history?limit=100');
        if (!response.ok) {
            console.warn('Historical data endpoint not available, starting with live data only');
            return;
        }
        
        const data = await response.json();
        
        if (data && data.length > 0) {
            console.log(`Loading ${data.length} historical data points`);
            
            // Process historical data in chronological order
            data.forEach(record => {
                updateAllCharts(record);
            });
            
            console.log('Historical data loaded successfully');
        } else {
            console.log('No historical data available');
        }
    } catch (error) {
        console.warn('Failed to load historical data:', error);
        console.log('Starting with live data only');
    }
}

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to GCS stream');
    updateConnectionStatus('connected');
});

socket.on('disconnect', (reason) => {
    console.log('Disconnected from GCS stream:', reason);
    updateConnectionStatus('disconnected');
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    updateConnectionStatus('error');
});

socket.on('reconnect', (attemptNumber) => {
    console.log('Reconnected after', attemptNumber, 'attempts');
    updateConnectionStatus('connected');
});

socket.on('sensor_update', (data) => {
    console.log('Sensor update received:', data);
    updateAllCharts(data);
});

// Update connection status indicator
function updateConnectionStatus(status) {
    let indicator = document.querySelector('.connection-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'connection-indicator';
        document.body.appendChild(indicator);
    }
    
    indicator.className = `connection-indicator ${status}`;
    
    switch(status) {
        case 'connected':
            indicator.textContent = '● Connected';
            break;
        case 'disconnected':
            indicator.textContent = '● Disconnected';
            break;
        case 'error':
            indicator.textContent = '● Connection Error';
            break;
    }
}

// Ping interval to keep connection alive
setInterval(() => {
    if (socket.connected) {
        socket.emit('ping');
    }
}, 30000);

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing graphs page');
    
    // Initialize all charts
    initAllCharts();
    
    // Load historical data
    await loadHistoricalData();
    
    console.log('Graphs page ready');
});

// Handle page visibility changes to pause/resume updates
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Page hidden, socket will continue in background');
    } else {
        console.log('Page visible again');
    }
});

