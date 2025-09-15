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

// Debug: Log socket connection attempts
console.log("Attempting to connect to Socket.IO namespace:", ns);

function set(id, v){ document.getElementById(id).textContent = v; }

// Connection status indicator
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

// Connection status display
function updateConnectionStatus(status) {
  let statusElement = document.getElementById("connection-status");
  if (!statusElement) {
    // Create status element if it doesn't exist
    const statusDiv = document.createElement("div");
    statusDiv.id = "connection-status";
    statusDiv.style.cssText = "position: fixed; top: 10px; right: 10px; padding: 5px 10px; border-radius: 3px; color: white; font-size: 12px; z-index: 1000;";
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

// Ping server every 30 seconds to keep connection alive
setInterval(() => {
  if (socket.connected) {
    socket.emit("ping");
  }
}, 30000);

// Data counters with persistence
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
  
  // Update counters and timestamps
  sensorUpdateCount++;
  localStorage.setItem('sensorUpdateCount', sensorUpdateCount.toString());
  updateDataCounters();
  updateLastUpdateTime();
  
  // Add log entry for sensor update
  addLogEntry("info", `Sensor data received: CO=${d.co_ppm}ppm, Temp=${d.temp_c}°C, Humidity=${d.humidity_pct}%`);
});

socket.on("target_detected", (e) => {
  const li = document.createElement("li");
  li.innerHTML = `
    <div class="target-item">
      <span class="target-time">[${new Date(e.ts).toLocaleTimeString()}]</span>
      <span class="target-type">${e.target_type.toUpperCase()}</span>
      <span class="target-details">${JSON.stringify(e.details)}</span>
    </div>
  `;
  document.getElementById("target-list").prepend(li);
  
  // Limit to 50 most recent targets
  const targetList = document.getElementById("target-list");
  while (targetList.children.length > 50) {
    targetList.removeChild(targetList.lastChild);
  }

  // Update counters
  targetDetectionCount++;
  localStorage.setItem('targetDetectionCount', targetDetectionCount.toString());
  updateDataCounters();
  
  // Add log entry for target detection
  addLogEntry("info", `Target detected: ${e.target_type.toUpperCase()} - ${JSON.stringify(e.details)}`);

  // Text-to-Speech
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

// Update data counters
function updateDataCounters() {
  const dataCountElement = document.getElementById("data-count");
  if (dataCountElement) {
    dataCountElement.textContent = `Records: ${sensorUpdateCount + targetDetectionCount}`;
  }
}

// Update last update time
function updateLastUpdateTime() {
  const lastUpdateElement = document.getElementById("last-update");
  if (lastUpdateElement) {
    lastUpdateElement.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
  }
}

// Clear targets button
document.addEventListener("DOMContentLoaded", () => {
  const clearTargetsBtn = document.getElementById("clear-targets");
  if (clearTargetsBtn) {
    clearTargetsBtn.addEventListener("click", () => {
      document.getElementById("target-list").innerHTML = "";
      targetDetectionCount = 0;
      localStorage.setItem('targetDetectionCount', '0');
      updateDataCounters();
      addLogEntry("info", "Target detection history cleared");
    });
  }

  // Clear logs button
  const clearLogsBtn = document.getElementById("clear-logs");
  if (clearLogsBtn) {
    clearLogsBtn.addEventListener("click", () => {
      document.getElementById("logs-area").textContent = "";
    });
  }

  // Log level filter
  const logLevelSelect = document.getElementById("log-level");
  if (logLevelSelect) {
    logLevelSelect.addEventListener("change", (e) => {
      // This would filter logs based on level
      console.log("Log level filter changed to:", e.target.value);
    });
  }

  // Reset counters button
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
});

// Add some sample log entries
function addLogEntry(level, message) {
  const logsArea = document.getElementById("logs-area");
  if (logsArea) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${level.toUpperCase()}: ${message}\n`;
    logsArea.textContent += logEntry;
    logsArea.scrollTop = logsArea.scrollHeight;
  }
}

// Initialize with some sample logs
document.addEventListener("DOMContentLoaded", () => {
  addLogEntry("info", "UAV GCS Dashboard initialized");
  addLogEntry("info", "Waiting for sensor data...");
  
  // Initialize data counters from localStorage
  updateDataCounters();
});
