const ns = "/stream";
const socket = io(ns, { 
    transports: ["websocket", "polling"],
    autoConnect: true,
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5,
    timeout: 20000,
    forceNew: true
});

console.log("Attempting to connect to Socket.IO namespace:", ns);

function set(id, v) { 
    document.getElementById(id).textContent = v; 
}

function formatDetails(type, details) {
    if (!details) return 'No details available';
    
    if (type === 'valve') {
        const state = details.state || 'unknown';
        const confidence = details.confidence ? (details.confidence * 100).toFixed(1) + '%' : 'N/A';
        return `State: <strong>${state}</strong> | Confidence: <strong>${confidence}</strong>`;
    } else if (type === 'gauge') {
        const reading = details.reading_bar || details.value || 'unknown';
        const confidence = details.confidence ? (details.confidence * 100).toFixed(1) + '%' : 'N/A';
        return `Reading: <strong>${reading} bar</strong> | Confidence: <strong>${confidence}</strong>`;
    } else if (type === 'aruco') {
        const id = details.id !== undefined ? details.id : 'unknown';
        
        let position = 'N/A';
        let rotation = 'N/A';
        
        // Handle both field name formats: 'pose'/'rotation' and 'tvec'/'rvec'
        const positionData = details.pose || details.tvec;
        const rotationData = details.rotation || details.rvec;
        
        if (positionData && Array.isArray(positionData)) {
            position = `[${positionData.map(v => v.toFixed(3)).join(', ')}]`;
        }
        if (rotationData && Array.isArray(rotationData)) {
            rotation = `[${rotationData.map(v => v.toFixed(3)).join(', ')}]`;
        }
        
        return `ID: <strong>${id}</strong> | Position: <strong>${position}</strong> | Rotation: <strong>${rotation}</strong>`;
    } else {
        // For other types, format nicely
        const confidence = details.confidence ? `Confidence: <strong>${(details.confidence * 100).toFixed(1)}%</strong>` : '';
        const otherFields = Object.entries(details)
            .filter(([key]) => key !== 'confidence')
            .map(([key, value]) => `${key}: <strong>${value}</strong>`)
            .join(' | ');
        
        return [confidence, otherFields].filter(Boolean).join(' | ') || 'No additional details';
    }
}

function refreshDetection(meta) {
    const img = document.getElementById('det-img');
    if (img) {
        img.src = '/static/targets/latest.jpg?bust=' + Date.now();
        
        img.onerror = function() {
            console.log("Detection image not available or failed to load");
        };
        
        img.onload = function() {
            console.log("Detection image refreshed successfully");
        };
    }

    if (meta) {
        const el = document.getElementById('det-meta');
        if (el) {
            const { target_type, ts, details } = meta;
            
            // Use the formatDetails function for consistent formatting
            const detailsHtml = formatDetails(target_type, details);
            const timeStr = ts ? new Date(ts).toLocaleTimeString() : 'Unknown';
            
            el.innerHTML = `
                <div class="target-header">
                    <span class="target-time">[${timeStr}]</span>
                    <span class="target-type">${target_type ? target_type.toUpperCase() : 'UNKNOWN'}</span>
                </div>
                <div class="target-details">${detailsHtml}</div>
            `;
        }
    }
}

socket.on("connect", () => {
    console.log("Connected to GCS stream");
    document.title = "UAV GCS - Connected";
    updateConnectionStatus("connected");
    addLogEntry("info", "Connected to GCS stream");
});

socket.on("disconnect", (reason) => {
    console.log("Disconnected from GCS stream:", reason);
    document.title = "UAV GCS - Disconnected";
    updateConnectionStatus("disconnected");
    addLogEntry("warning", `Disconnected from GCS stream: ${reason}`);
});

socket.on("connect_error", (error) => {
    console.error("Connection error:", error);
    document.title = "UAV GCS - Connection Error";
    updateConnectionStatus("error");
    addLogEntry("error", `Connection error: ${error}`);
});

socket.on("reconnect", (attemptNumber) => {
    console.log("Reconnected after", attemptNumber, "attempts");
    document.title = "UAV GCS - Connected";
    updateConnectionStatus("connected");
    addLogEntry("info", `Reconnected after ${attemptNumber} attempts`);
});

socket.on("reconnect_error", (error) => {
    console.error("Reconnection error:", error);
    updateConnectionStatus("error");
    addLogEntry("error", `Reconnection error: ${error}`);
});

socket.on("reconnect_failed", () => {
    console.error("Failed to reconnect after maximum attempts");
    updateConnectionStatus("failed");
    addLogEntry("error", "Failed to reconnect after maximum attempts");
});

function updateConnectionStatus(status) {
    let statusElement = document.getElementById("connection-status");
    if (!statusElement) {
        const statusDiv = document.createElement("div");
        statusDiv.id = "connection-status";
        statusDiv.style.cssText = "position: fixed; top: 70px; right: 10px; padding: 5px 10px; border-radius: 3px; color: white; font-size: 12px; z-index: 1000; box-shadow: 0 2px 4px rgba(0,0,0,0.2);";
        document.body.appendChild(statusDiv);
        statusElement = statusDiv;
    }
    switch(status) {
        case "connected":
            statusElement.textContent = "Connected";
            statusElement.style.backgroundColor = "#4CAF50";
            break;
        case "disconnected":
            statusElement.textContent = "Disconnected";
            statusElement.style.backgroundColor = "#FF9800";
            break;
        case "error":
            statusElement.textContent = "Connection Error";
            statusElement.style.backgroundColor = "#F44336";
            break;
        case "failed":
            statusElement.textContent = "Connection Failed";
            statusElement.style.backgroundColor = "#9E9E9E";
            break;
    }
}

setInterval(() => {
    if (socket.connected) {
        socket.emit("ping");
    }
}, 30000);

let sensorUpdateCount = parseInt(localStorage.getItem('sensorUpdateCount') || '0');
let targetDetectionCount = parseInt(localStorage.getItem('targetDetectionCount') || '0');

socket.on("sensor_update", (d) => {
    set("v-co", Number(d.co_ppm ?? NaN).toFixed(2));
    set("v-no2", Number(d.no2_ppm ?? NaN).toFixed(2));
    set("v-nh3", Number(d.nh3_ppm ?? NaN).toFixed(2));
    set("v-light", Number(d.light_lux ?? NaN).toFixed(0));
    set("v-temp", Number(d.temp_c ?? NaN).toFixed(1));
    set("v-press", Number(d.pressure_hpa ?? NaN).toFixed(1));
    set("v-hum", Number(d.humidity_pct ?? NaN).toFixed(1));
    
    sensorUpdateCount++;
    localStorage.setItem('sensorUpdateCount', sensorUpdateCount.toString());
    updateDataCounters();
    updateLastUpdateTime();
    
    addLogEntry("info", `Sensor data received: CO=${d.co_ppm ? d.co_ppm.toFixed(3) : '--'}ppm, Temp=${d.temp_c ? d.temp_c.toFixed(2) : '--'}°C, Humidity=${d.humidity_pct ? d.humidity_pct.toFixed(2) : '--'}%`);
});

socket.on("target_detected", (e) => {
    // Filter out "livedata" type (not a real detection)
    if (e.target_type === "livedata") {
        // Still refresh the image for live feed, but don't add to list
        refreshDetection(e);
        return;
    }
    
    const li = document.createElement("li");
    li.innerHTML = `
        <div class="target-item">
            <span class="target-time">[${new Date(e.ts).toLocaleTimeString()}]</span>
            <span class="target-type">${e.target_type.toUpperCase()}</span>
            <span class="target-details">${JSON.stringify(e.details)}</span>
        </div>
    `;
    const recentList = document.getElementById("recent-list");
    if (recentList) {
        recentList.prepend(li);
    } else {
        console.warn("recent-list element not found");
        return;
    }
    while (recentList.children.length > 50) {
        recentList.removeChild(recentList.lastChild);
    }

    targetDetectionCount++;
    localStorage.setItem('targetDetectionCount', targetDetectionCount.toString());
    updateDataCounters();
    
    addLogEntry("info", `Target detected: ${e.target_type.toUpperCase()} - ${JSON.stringify(e.details)}`);

    refreshDetection(e);

    const ttsOn = document.getElementById("tts-toggle").checked;
    if (ttsOn && "speechSynthesis" in window) {
        let phrase = `Target detected: ${e.target_type}.`;
        if (e.target_type === "valve" && e.details?.state) {
            phrase = `Valve detected: ${e.details.state}.`;
        } else if (e.target_type === "gauge" && e.details?.value !== undefined) {
            phrase = `Gauge reads ${e.details.value} ${e.details.unit || ""}.`;
        } else if (e.target_type === "aruco" && e.details?.id !== undefined) {
            phrase = `ArUco marker ${e.details.id} detected.`;
        }
        speechSynthesis.cancel();
        speechSynthesis.speak(new SpeechSynthesisUtterance(phrase));
        addLogEntry("info", `TTS: ${phrase}`);
    }
});

socket.on("throughput_update", data => {
    document.getElementById("tp-aqsa").textContent = data.aqsa_kbps ?? "--";
    document.getElementById("tp-taip").textContent = data.taip_kbps ?? "--";
    document.getElementById("tp-time").textContent =
        `Updated: ${new Date(data.ts * 1000).toLocaleTimeString()}`;
});

socket.on('recent_detection', (item) => {
    addRecentItem(item);
    // For single detections, show just that one detection
    setMultiplePreviews([item]);
});

// Handle batch detections to prevent flickering
socket.on('target_batch', (batchData) => {
    console.log(`Received batch of ${batchData.count} detections`);
    
    // Convert all detections to recent detection format and sort by timestamp
    const recentItems = batchData.detections
        .sort((a, b) => a.ts - b.ts); // Sort by timestamp to maintain order
    
    // Add all detections to the recent list in order
    recentItems.forEach(item => {
        addRecentItem(item);
    });
    
    // Show all detections in the preview box
    if (recentItems.length > 0) {
        setMultiplePreviews(recentItems);
    }
});

function updateDataCounters() {
    const dataCountElement = document.getElementById("data-count");
    if (dataCountElement) {
        dataCountElement.textContent = `Records: ${sensorUpdateCount + targetDetectionCount}`;
    }
}

function updateLastUpdateTime() {
    const lastUpdateElement = document.getElementById("last-update");
    if (lastUpdateElement) {
        lastUpdateElement.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const clearTargetsBtn = document.getElementById("clear-targets");
    if (clearTargetsBtn) {
        clearTargetsBtn.addEventListener("click", async () => {
            // Ask for confirmation
            if (!confirm("Are you sure you want to clear ALL history? This will delete all database records, images, and reset all counters. This action cannot be undone.")) {
                return;
            }
            
            try {
                // Call the clear history API endpoint
                const response = await fetch('/api/clear-history', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.message || 'Failed to clear history');
                }
                
                const result = await response.json();
                
                // Clear the UI
                const recentList = document.getElementById("recent-list");
                if (recentList) {
                    recentList.innerHTML = "";
                }
                
                // Reset counters
                targetDetectionCount = 0;
                sensorUpdateCount = 0;
                localStorage.setItem('targetDetectionCount', '0');
                localStorage.setItem('sensorUpdateCount', '0');
                updateDataCounters();
                
                addLogEntry("success", "All history cleared successfully - database, images, and counters reset");
            } catch (error) {
                console.error("Error clearing history:", error);
                addLogEntry("error", `Failed to clear history: ${error.message}`);
            }
        });
    }

    // Live Camera button functionality
    const liveCameraBtn = document.getElementById("live-camera-btn");
    if (liveCameraBtn) {
        liveCameraBtn.addEventListener("click", () => {
            switchToLiveCamera();
        });
    }

    const clearLogsBtn = document.getElementById("clear-logs");
    if (clearLogsBtn) {
        clearLogsBtn.addEventListener("click", () => {
            document.getElementById("logs-area").textContent = "";
        });
    }

    const logLevelSelect = document.getElementById("log-level");
    if (logLevelSelect) {
        logLevelSelect.addEventListener("change", (e) => {
            console.log("Log level filter changed to:", e.target.value);
        });
    }

    const resetCountersBtn = document.getElementById("reset-counters");
    if (resetCountersBtn) {
        resetCountersBtn.addEventListener("click", () => {
            sensorUpdateCount = 0;
            targetDetectionCount = 0;
            localStorage.setItem('sensorUpdateCount', '0');
            localStorage.setItem('targetDetectionCount', '0');
            updateDataCounters();
            addLogEntry("info", "All counters reset");
        });
    }

    // Device control functionality
    setupDeviceControls();
});

function setupDeviceControls() {
    const modeButtons = document.querySelectorAll('.mode-btn');
    const deviceIdInput = document.getElementById('device-id');
    const controlStatus = document.getElementById('control-status');
    
    modeButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const mode = button.dataset.mode;
            const deviceId = deviceIdInput.value.trim();
            
            if (!deviceId) {
                updateControlStatus('Please enter a device ID', 'error');
                return;
            }
            
            // Update button states
            modeButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Send display command
            await sendDisplayCommand(deviceId, mode);
        });
    });
}

async function sendDisplayCommand(deviceId, mode) {
    const controlStatus = document.getElementById('control-status');
    
    try {
        updateControlStatus(`Sending command to ${deviceId}...`, '');
        
        const response = await fetch(`/api/device/${deviceId}/display`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': 'your-api-key-here' // You may need to set this properly
            },
            body: JSON.stringify({ mode: mode })
        });
        
        if (response.ok) {
            const result = await response.json();
            updateControlStatus(`✓ Display mode set to '${mode}' for ${deviceId}`, 'success');
            addLogEntry("info", `Device control: Set ${deviceId} display mode to '${mode}'`);
        } else {
            const error = await response.json();
            updateControlStatus(`✗ Error: ${error.error || 'Unknown error'}`, 'error');
            addLogEntry("error", `Device control failed: ${error.error || 'Unknown error'}`);
        }
    } catch (error) {
        updateControlStatus(`✗ Network error: ${error.message}`, 'error');
        addLogEntry("error", `Device control network error: ${error.message}`);
    }
}

function updateControlStatus(message, type = '') {
    const controlStatus = document.getElementById('control-status');
    if (controlStatus) {
        controlStatus.textContent = message;
        controlStatus.className = `control-status ${type}`;
    }
}

function addLogEntry(level, message) {
    const logsArea = document.getElementById("logs-area");
    if (logsArea) {
        const timestamp = new Date().toISOString();
        const logEntry = `[${timestamp}] ${level.toUpperCase()}: ${message}\n`;
        logsArea.textContent += logEntry;
        logsArea.scrollTop = logsArea.scrollHeight;
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    addLogEntry("info", "UAV GCS Dashboard initialized");
    
    updateDataCounters();
    
    await loadLatestSensorData();
    
    await loadRecentTargets();
    
    await loadRecent();
    
    refreshDetection();
    
    setInterval(() => refreshDetection(), 3500);
});

async function loadLatestSensorData() {
    try {
        const response = await fetch('/api/latest-sensor');
        const data = await response.json();
        
        if (data) {
            set("v-co", data.co_ppm ? Number(data.co_ppm).toFixed(2) : "--");
            set("v-no2", data.no2_ppm ? Number(data.no2_ppm).toFixed(2) : "--");
            set("v-nh3", data.nh3_ppm ? Number(data.nh3_ppm).toFixed(2) : "--");
            set("v-light", data.light_lux ? Number(data.light_lux).toFixed(0) : "--");
            set("v-temp", data.temp_c ? Number(data.temp_c).toFixed(1) : "--");
            set("v-press", data.pressure_hpa ? Number(data.pressure_hpa).toFixed(1) : "--");
            set("v-hum", data.humidity_pct ? Number(data.humidity_pct).toFixed(1) : "--");
            
            const lastUpdate = new Date(data.ts);
            const lastUpdateElement = document.getElementById("last-update");
            if (lastUpdateElement) {
                lastUpdateElement.textContent = `Last update: ${lastUpdate.toLocaleTimeString()}`;
            }
            
            addLogEntry("info", `Loaded latest sensor data from database (${lastUpdate.toLocaleString()})`);
        } else {
            addLogEntry("info", "No sensor data found in database");
        }
    } catch (error) {
        console.error('Error loading latest sensor data:', error);
        addLogEntry("error", "Failed to load latest sensor data from database");
    }
}

async function loadRecentTargets() {
    try {
        const response = await fetch('/api/recent-targets');
        const data = await response.json();
        
        if (data && data.length > 0) {
            const recentList = document.getElementById("recent-list");
            if (recentList) {
                recentList.innerHTML = "";
                
                // Filter out "livedata" type (extra safety check)
                data.filter(target => target.target_type !== "livedata").forEach(target => {
                    const li = document.createElement("li");
                    li.innerHTML = `
                        <div class="target-item">
                            <div class="target-image">
                                <img src="${target.image_url || '/static/targets/latest.jpg'}" alt="${target.target_type}" onerror="this.src='/static/targets/latest.jpg'">
                            </div>
                            <div class="target-content">
                                <div class="target-header">
                                    <span class="target-time">[${new Date(target.ts).toLocaleTimeString()}]</span>
                                    <span class="target-type">${target.target_type.toUpperCase()}</span>
                                </div>
                                <div class="target-details">${JSON.stringify(target.details)}</div>
                            </div>
                        </div>
                    `;
                    recentList.appendChild(li);
                });
            } else {
                console.warn("recent-list element not found");
            }
            
            addLogEntry("info", `Loaded ${data.length} recent target detections from database`);
        } else {
            addLogEntry("info", "No target detections found in database");
        }
    } catch (error) {
        console.error('Error loading recent targets:', error);
        addLogEntry("error", "Failed to load recent target detections from database");
    }
}

// Recent Detections functionality
async function loadRecent() {
    try {
        const res = await fetch('/api/recent-detections?limit=40');
        const data = await res.json();
        renderRecentList(data);
    } catch (e) { 
        console.warn('recent load failed', e); 
    }
}

function renderRecentList(items) {
    const ul = document.getElementById('recent-list');
    if (!ul) return;
    ul.innerHTML = '';
    items.forEach(addRecentItem);
}

function addRecentItem(item) {
    const ul = document.getElementById('recent-list');
    if (!ul) return;
    const li = document.createElement('li');
    
    // Handle different timestamp formats
    let timeStr;
    if (typeof item.ts === 'number') {
        timeStr = new Date(item.ts * 1000).toLocaleTimeString();
    } else if (typeof item.ts === 'string') {
        timeStr = new Date(item.ts).toLocaleTimeString();
    } else {
        timeStr = 'Unknown time';
    }
    
    // Format details based on target type
    let detailsHtml = '';
    if (item.type === 'valve') {
        const state = item.details?.state || 'unknown';
        const confidence = item.details?.confidence ? (item.details.confidence * 100).toFixed(1) : '0.0';
        detailsHtml = `State: ${state} | Confidence: ${confidence}%`;
    } else if (item.type === 'gauge') {
        const reading = item.details?.reading_bar || item.details?.value || 'unknown';
        const confidence = item.details?.confidence ? (item.details.confidence * 100).toFixed(1) : '0.0';
        detailsHtml = `Reading: ${reading} bar | Confidence: ${confidence}%`;
    } else if (item.type === 'aruco') {
        const id = item.details?.id || 'unknown';
        
        // Handle both field name formats: 'pose'/'rotation' and 'tvec'/'rvec'
        const positionData = item.details?.pose || item.details?.tvec;
        const rotationData = item.details?.rotation || item.details?.rvec;
        
        const position = positionData ? `[${positionData.map(v => v.toFixed(3)).join(', ')}]` : 'N/A';
        const rotation = rotationData ? `[${rotationData.map(v => v.toFixed(3)).join(', ')}]` : 'N/A';
        
        detailsHtml = `ID: ${id} | Position: ${position} | Rotation: ${rotation}`;
    } else {
        // Fallback for other types
        detailsHtml = JSON.stringify(item.details || {});
    }
    
    li.innerHTML = `
        <div class="target-item">
            <div class="target-image">
                <img src="${item.thumb_url || item.image_url || '/static/targets/latest.jpg'}" alt="${item.type}" onerror="this.src='/static/targets/latest.jpg'">
            </div>
            <div class="target-content">
                <div class="target-header">
                    <span class="target-time">[${timeStr}]</span>
                    <span class="target-type">${item.type.toUpperCase()}</span>
                </div>
                <div class="target-details">${detailsHtml}</div>
            </div>
        </div>`;
    
    li.addEventListener('click', () => {
        // Remove active class from all items
        document.querySelectorAll('#recent-list li').forEach(el => el.classList.remove('active'));
        // Add active class to clicked item
        li.classList.add('active');
        
        // Show single detection in the preview
        setMultiplePreviews([item]);
    });
    ul.appendChild(li);  // Append to maintain ascending order (earliest to latest)
}

function setPreview(item) {
    const img = document.getElementById('det-img');
    const meta = document.getElementById('det-meta');
    
    if (img) {
        const newSrc = item.image_url + '?v=' + Date.now();
        img.src = newSrc;
    }
    if (meta) {
        // Format details based on target type
        let detailsHtml = formatDetails(item.type, item.details);
        
        const timeStr = new Date(item.ts * 1000).toLocaleTimeString();
        
        meta.innerHTML = `
            <div class="target-header">
                <span class="target-time">[${timeStr}]</span>
                <span class="target-type">${item.type.toUpperCase()}</span>
            </div>
            <div class="target-details">${detailsHtml}</div>
        `;
    }
}

function setMultiplePreviews(items) {
    const img = document.getElementById('det-img');
    const meta = document.getElementById('det-meta');
    
    if (img && items.length > 0) {
        const newSrc = items[0].image_url + '?v=' + Date.now();
        img.src = newSrc;
    }
    if (meta) {
        // Group detections by timestamp (assuming they're all from the same frame)
        const timeStr = items.length > 0 ? new Date(items[0].ts * 1000).toLocaleTimeString() : 'Unknown time';
        
        // Format all detections
        const detectionHtml = items.map(item => {
            const detailsHtml = formatDetails(item.type, item.details);
            return `
                <div class="detection-item">
                    <div class="detection-header">
                        <span class="detection-type">${item.type.toUpperCase()}</span>
                    </div>
                    <div class="detection-details">${detailsHtml}</div>
                </div>
            `;
        }).join('');
        
        meta.innerHTML = `
            <div class="target-header">
                <span class="target-time">[${timeStr}]</span>
                <span class="target-type">FRAME (${items.length} detections)</span>
            </div>
            <div class="multiple-detections">
                ${detectionHtml}
            </div>
        `;
    }
}

function switchToLiveCamera() {
    // Clear active selection from recent detections
    document.querySelectorAll('#recent-list li').forEach(el => el.classList.remove('active'));
    
    // Reset image to live feed
    const img = document.getElementById('det-img');
    if (img) {
        img.src = '/static/targets/latest.jpg?v=' + Date.now();
    }
    
    // Reset metadata to show live status
    const meta = document.getElementById('det-meta');
    if (meta) {
        meta.innerHTML = `
            <div class="target-header">
                <span class="target-time">[LIVE]</span>
                <span class="target-type">LIVE CAMERA</span>
            </div>
            <div class="target-details">Monitoring live camera feed...</div>
        `;
    }
    
    addLogEntry("info", "Switched to live camera view");
}
