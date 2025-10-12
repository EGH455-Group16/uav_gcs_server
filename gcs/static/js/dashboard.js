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
            // Image not available
        };
        
        img.onload = function() {
            // Image loaded successfully
        };
    }

    // If meta is provided, use the new setMultiplePreviews function instead of overwriting structure
    if (meta) {
        setMultiplePreviews([meta]);
    }
}

socket.on("connect", () => {
    document.title = "UAV GCS - Connected";
    updateConnectionStatus("connected");
    addLogEntry("info", "Connected to GCS stream");
});

socket.on("disconnect", (reason) => {
    document.title = "UAV GCS - Disconnected";
    updateConnectionStatus("disconnected");
    addLogEntry("warning", `Disconnected from GCS stream: ${reason}`);
});

socket.on("connect_error", (error) => {
    document.title = "UAV GCS - Connection Error";
    updateConnectionStatus("error");
    addLogEntry("error", `Connection error: ${error}`);
});

socket.on("reconnect", (attemptNumber) => {
    document.title = "UAV GCS - Connected";
    updateConnectionStatus("connected");
    addLogEntry("info", `Reconnected after ${attemptNumber} attempts`);
});

socket.on("reconnect_error", (error) => {
    updateConnectionStatus("error");
    addLogEntry("error", `Reconnection error: ${error}`);
});

socket.on("reconnect_failed", () => {
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

// Client-side batching for rapid individual detections
let detectionBatch = [];
let batchTimeout = null;

socket.on('recent_detection', (item) => {
    console.log('DEBUG: Recent detection received:', item);
    addRecentItem(item);
    
    // Add to batch
    detectionBatch.push(item);
    console.log('DEBUG: Added to batch. Batch size:', detectionBatch.length);
    
    // Clear any existing timeout
    if (batchTimeout) {
        clearTimeout(batchTimeout);
    }
    
    // Set a short timeout to batch rapid detections
    batchTimeout = setTimeout(() => {
        console.log('DEBUG: Processing batch with', detectionBatch.length, 'items');
        // Process the batch
        if (detectionBatch.length > 1) {
            // Multiple detections - sort by timestamp and show all
            const sortedBatch = detectionBatch.sort((a, b) => a.ts - b.ts);
            console.log('DEBUG: Sending sorted batch to setMultiplePreviews:', sortedBatch);
            setMultiplePreviews(sortedBatch);
        } else {
            // Single detection
            console.log('DEBUG: Sending single detection to setMultiplePreviews:', detectionBatch);
            setMultiplePreviews(detectionBatch);
        }
        
        // Clear the batch
        detectionBatch = [];
        batchTimeout = null;
    }, 50); // 50ms batching window
});

// Handle batch detections to prevent flickering
socket.on('target_batch', (batchData) => {
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

// Single consolidated DOMContentLoaded event listener
document.addEventListener("DOMContentLoaded", async () => {
    // CRITICAL: Initialize the fixed metadata structure FIRST
    initializeMetadataStructure();
    
    addLogEntry("info", "UAV GCS Dashboard initialized");
    
    // Set up button event listeners
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
            // Log level filter changed
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
    
    // Load data
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
            }
            
            addLogEntry("info", `Loaded ${data.length} recent target detections from database`);
        } else {
            addLogEntry("info", "No target detections found in database");
        }
    } catch (error) {
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
        // Recent load failed
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

function initializeMetadataStructure() {
    const meta = document.getElementById('det-meta');
    if (!meta) {
        return;
    }
    if (meta.dataset.initialized) {
        return;
    }
    
    // Create the fixed structure once with persistent labels
    meta.innerHTML = `
        <div class="target-header">
            <span class="target-time" id="meta-time">[--:--:--]</span>
            <span class="target-type" id="meta-count">FRAME (0 detections)</span>
        </div>
        <div class="multiple-detections">
            <div class="detection-item detection-item-placeholder" id="det-aruco">
                <div class="detection-header">
                    <span class="detection-type">ARUCO</span>
                </div>
                <div class="detection-details">ID: <strong>--</strong> | Position: <strong>[--, --, --]</strong> | Rotation: <strong>[--, --, --]</strong></div>
            </div>
            <div class="detection-item detection-item-placeholder" id="det-gauge">
                <div class="detection-header">
                    <span class="detection-type">GAUGE</span>
                </div>
                <div class="detection-details">Reading: <strong>-- bar</strong> | Confidence: <strong>--%</strong></div>
            </div>
            <div class="detection-item detection-item-placeholder" id="det-valve">
                <div class="detection-header">
                    <span class="detection-type">VALVE</span>
                </div>
                <div class="detection-details">State: <strong>--</strong> | Confidence: <strong>--%</strong></div>
            </div>
        </div>
    `;
    meta.dataset.initialized = 'true';
}

function setMultiplePreviews(items) {
    console.log('DEBUG: setMultiplePreviews called with:', items);
    const img = document.getElementById('det-img');
    
    // Initialize structure if needed
    initializeMetadataStructure();
    
    // Update image
    if (img && items.length > 0) {
        const newSrc = items[0].image_url + '?v=' + Date.now();
        img.src = newSrc;
    }
    
    // Update header time and count
    let timeStr = '--:--:--';
    if (items.length > 0 && items[0].ts) {
        try {
            // Handle different timestamp formats
            let timestamp;
            if (typeof items[0].ts === 'number') {
                timestamp = items[0].ts * 1000; // Convert seconds to milliseconds
            } else if (typeof items[0].ts === 'string') {
                timestamp = new Date(items[0].ts).getTime();
            } else {
                timestamp = items[0].ts;
            }
            
            if (!isNaN(timestamp)) {
                timeStr = new Date(timestamp).toLocaleTimeString();
            }
        } catch (e) {
            // Invalid timestamp, keep default
        }
    }
    
    const timeEl = document.getElementById('meta-time');
    const countEl = document.getElementById('meta-count');
    
    // Create a map of detections by type
    const detectionMap = {};
    items.forEach(item => {
        // Handle both 'type' and 'target_type' fields for compatibility
        const itemType = item.type || item.target_type;
        console.log('DEBUG: Processing item:', itemType, item);
        detectionMap[itemType] = item;
    });
    
    const activeCount = Object.keys(detectionMap).length;
    console.log('DEBUG: Detection map:', detectionMap);
    console.log('DEBUG: Active count:', activeCount);
    
    if (timeEl) timeEl.textContent = `[${timeStr}]`;
    if (countEl) countEl.textContent = `FRAME (${activeCount} detection${activeCount !== 1 ? 's' : ''})`;
    
    // Update each detection slot (only update content, not structure)
    const detectionTypes = ['aruco', 'gauge', 'valve'];
    detectionTypes.forEach(type => {
        const slotId = `det-${type}`;
        const slotEl = document.getElementById(slotId);
        if (!slotEl) {
            console.log('DEBUG: Could not find slot element:', slotId);
            return;
        }
        
        const item = detectionMap[type];
        const detailsEl = slotEl.querySelector('.detection-details');
        
        console.log('DEBUG: Updating slot', type, 'with item:', item);
        
        if (item) {
            // Detection present - update content and style
            console.log('DEBUG: Setting', type, 'as ACTIVE');
            slotEl.classList.remove('detection-item-placeholder');
            slotEl.classList.add('detection-item-active');
            if (detailsEl) {
                // Handle both 'type' and 'target_type' fields for compatibility
                const itemType = item.type || item.target_type;
                const formattedDetails = formatDetails(itemType, item.details);
                console.log('DEBUG: Formatted details for', type, ':', formattedDetails);
                detailsEl.innerHTML = formattedDetails;
            }
        } else {
            // No detection - show placeholder with persistent labels
            slotEl.classList.remove('detection-item-active');
            slotEl.classList.add('detection-item-placeholder');
            if (detailsEl) {
                // Show placeholder with the same label structure but with -- values
                if (type === 'aruco') {
                    detailsEl.innerHTML = 'ID: <strong>--</strong> | Position: <strong>[--, --, --]</strong> | Rotation: <strong>[--, --, --]</strong>';
                } else if (type === 'gauge') {
                    detailsEl.innerHTML = 'Reading: <strong>-- bar</strong> | Confidence: <strong>--%</strong>';
                } else if (type === 'valve') {
                    detailsEl.innerHTML = 'State: <strong>--</strong> | Confidence: <strong>--%</strong>';
                } else {
                    detailsEl.innerHTML = '<span class="detection-placeholder">No detection</span>';
                }
            }
        }
    });
}

function switchToLiveCamera() {
    // Clear active selection from recent detections
    document.querySelectorAll('#recent-list li').forEach(el => el.classList.remove('active'));
    
    // Reset image to live feed
    const img = document.getElementById('det-img');
    if (img) {
        img.src = '/static/targets/latest.jpg?v=' + Date.now();
    }
    
    // Reset metadata to show live status - but preserve the fixed structure
    const meta = document.getElementById('det-meta');
    if (meta) {
        // Initialize structure if needed
        initializeMetadataStructure();
        
        // Update header to show live status
        const timeEl = document.getElementById('meta-time');
        const countEl = document.getElementById('meta-count');
        if (timeEl) timeEl.textContent = '[LIVE]';
        if (countEl) countEl.textContent = 'LIVE CAMERA';
        
        // Reset all detection slots to placeholder state with persistent labels
        const detectionTypes = ['aruco', 'gauge', 'valve'];
        detectionTypes.forEach(type => {
            const slotEl = document.getElementById(`det-${type}`);
            if (slotEl) {
                slotEl.classList.remove('detection-item-active');
                slotEl.classList.add('detection-item-placeholder');
                const detailsEl = slotEl.querySelector('.detection-details');
                if (detailsEl) {
                    // Show placeholder with the same label structure but with -- values
                    if (type === 'aruco') {
                        detailsEl.innerHTML = 'ID: <strong>--</strong> | Position: <strong>[--, --, --]</strong> | Rotation: <strong>[--, --, --]</strong>';
                    } else if (type === 'gauge') {
                        detailsEl.innerHTML = 'Reading: <strong>-- bar</strong> | Confidence: <strong>--%</strong>';
                    } else if (type === 'valve') {
                        detailsEl.innerHTML = 'State: <strong>--</strong> | Confidence: <strong>--%</strong>';
                    } else {
                        detailsEl.innerHTML = '<span class="detection-placeholder">No detection</span>';
                    }
                }
            }
        });
    }
    
    addLogEntry("info", "Switched to live camera view");
}
