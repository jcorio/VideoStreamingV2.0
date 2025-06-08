/**
 * Main JavaScript for RTSP Camera Dashboard
 */

// Socket.IO connection
let socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/stream');

// DOM Elements
const cameraGrid = document.getElementById('cameraGrid');
const snapshotGrid = document.getElementById('snapshotGrid');
const cameraSettings = document.getElementById('cameraSettings');
const connectionStatus = document.getElementById('connectionStatus');
const dashboardTab = document.getElementById('dashboardTab');
const snapshotsTab = document.getElementById('snapshotsTab');
const settingsTab = document.getElementById('settingsTab');
const dashboardView = document.getElementById('dashboardView');
const snapshotsView = document.getElementById('snapshotsView');
const settingsView = document.getElementById('settingsView');

// Templates
const cameraTemplate = document.getElementById('cameraTemplate');
const cameraSettingsTemplate = document.getElementById('cameraSettingsTemplate');
const snapshotTemplate = document.getElementById('snapshotTemplate');

// Camera state
const cameras = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set up tab navigation
    setupTabNavigation();
    
    // Load snapshots
    loadSnapshots();
});

// Socket.IO event handlers
socket.on('connect', () => {
    connectionStatus.textContent = 'Connected';
    connectionStatus.classList.add('text-success');
});

socket.on('disconnect', () => {
    connectionStatus.textContent = 'Disconnected';
    connectionStatus.classList.remove('text-success');
    connectionStatus.classList.add('text-danger');
    
    // Mark all cameras as disconnected
    document.querySelectorAll('.camera-status').forEach(statusBadge => {
        statusBadge.textContent = 'Disconnected';
        statusBadge.classList.remove('connected');
        statusBadge.classList.add('disconnected');
    });
});

socket.on('camera_frame', (data) => {
    updateCameraFrame(data.camera_name, data.frame, data.connected);
});

socket.on('camera_status', (statusData) => {
    updateCameraStatus(statusData);
});

/**
 * Update camera frame with new image data
 */
function updateCameraFrame(cameraName, frameData, connected) {
    // Create camera element if it doesn't exist
    if (!cameras[cameraName]) {
        createCameraElement(cameraName);
    }
    
    // Update frame
    const frameImg = document.querySelector(`.camera-container[data-camera="${cameraName}"] .camera-frame`);
    if (frameImg) {
        frameImg.src = `data:image/jpeg;base64,${frameData}`;
    }
    
    // Update connection status
    const statusBadge = document.querySelector(`.camera-container[data-camera="${cameraName}"] .camera-status`);
    if (statusBadge) {
        statusBadge.textContent = connected ? 'Connected' : 'Disconnected';
        statusBadge.classList.remove('connected', 'disconnected');
        statusBadge.classList.add(connected ? 'connected' : 'disconnected');
    }
}

/**
 * Create camera element from template
 */
function createCameraElement(cameraName) {
    // Clone template
    const cameraElement = cameraTemplate.content.cloneNode(true).querySelector('.camera-container');
    cameraElement.setAttribute('data-camera', cameraName);
    
    // Set camera name
    cameraElement.querySelector('.camera-name').textContent = cameraName;
    
    // Set up snapshot button
    const snapshotBtn = cameraElement.querySelector('.snapshot-btn');
    snapshotBtn.addEventListener('click', () => {
        takeSnapshot(cameraName);
    });
    
    // Set up detection toggle
    const detectionToggle = cameraElement.querySelector('.detection-toggle');
    detectionToggle.addEventListener('click', () => {
        toggleDetection(cameraName);
    });
    
    // Add to grid
    cameraGrid.appendChild(cameraElement);
    
    // Add to cameras object
    cameras[cameraName] = {
        element: cameraElement,
        detectionEnabled: true
    };
    
    // Also create settings element
    createCameraSettingsElement(cameraName);
}

/**
 * Create camera settings element from template
 */
function createCameraSettingsElement(cameraName) {
    // Clone template
    const settingsElement = cameraSettingsTemplate.content.cloneNode(true).querySelector('.camera-setting');
    settingsElement.setAttribute('data-camera', cameraName);
    
    // Set camera name
    settingsElement.querySelector('.camera-name').textContent = cameraName;
    
    // Set up detection checkbox
    const detectionCheckbox = settingsElement.querySelector('.detection-enabled');
    detectionCheckbox.checked = true;
    detectionCheckbox.addEventListener('change', (e) => {
        updateCameraSetting(cameraName, 'detection_enabled', e.target.checked);
    });
    
    // Set up confidence threshold slider
    const confidenceSlider = settingsElement.querySelector('.confidence-threshold');
    const confidenceValue = settingsElement.querySelector('.confidence-value');
    confidenceSlider.addEventListener('input', (e) => {
        const value = e.target.value;
        confidenceValue.textContent = value;
    });
    confidenceSlider.addEventListener('change', (e) => {
        updateCameraSetting(cameraName, 'confidence_threshold', e.target.value);
    });
    
    // Add to settings container
    cameraSettings.appendChild(settingsElement);
}

/**
 * Update camera settings via API
 */
function updateCameraSetting(cameraName, settingName, value) {
    fetch('/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            camera_name: cameraName,
            [settingName]: value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to update setting:', data.message);
        }
        
        // Update UI based on setting changed
        if (settingName === 'detection_enabled') {
            const statusSpan = document.querySelector(`.camera-container[data-camera="${cameraName}"] .detection-status`);
            if (statusSpan) {
                statusSpan.textContent = `Detection: ${value ? 'On' : 'Off'}`;
            }
        }
    })
    .catch(error => {
        console.error('Error updating setting:', error);
    });
}

/**
 * Toggle object detection for a camera
 */
function toggleDetection(cameraName) {
    const camera = cameras[cameraName];
    if (!camera) return;
    
    // Toggle state
    camera.detectionEnabled = !camera.detectionEnabled;
    
    // Update UI
    const statusSpan = document.querySelector(`.camera-container[data-camera="${cameraName}"] .detection-status`);
    if (statusSpan) {
        statusSpan.textContent = `Detection: ${camera.detectionEnabled ? 'On' : 'Off'}`;
    }
    
    // Update checkbox in settings
    const checkbox = document.querySelector(`.camera-setting[data-camera="${cameraName}"] .detection-enabled`);
    if (checkbox) {
        checkbox.checked = camera.detectionEnabled;
    }
    
    // Send update to server
    updateCameraSetting(cameraName, 'detection_enabled', camera.detectionEnabled);
}

/**
 * Update all camera status displays
 */
function updateCameraStatus(statusData) {
    for (const [cameraName, status] of Object.entries(statusData)) {
        // Create camera element if it doesn't exist
        if (!cameras[cameraName]) {
            createCameraElement(cameraName);
        }
        
        // Update detection status in UI
        cameras[cameraName].detectionEnabled = status.detection_enabled;
        
        const statusSpan = document.querySelector(`.camera-container[data-camera="${cameraName}"] .detection-status`);
        if (statusSpan) {
            statusSpan.textContent = `Detection: ${status.detection_enabled ? 'On' : 'Off'}`;
        }
        
        // Update settings UI
        const checkbox = document.querySelector(`.camera-setting[data-camera="${cameraName}"] .detection-enabled`);
        if (checkbox) {
            checkbox.checked = status.detection_enabled;
        }
        
        const confidenceSlider = document.querySelector(`.camera-setting[data-camera="${cameraName}"] .confidence-threshold`);
        const confidenceValue = document.querySelector(`.camera-setting[data-camera="${cameraName}"] .confidence-value`);
        if (confidenceSlider && confidenceValue) {
            confidenceSlider.value = status.confidence_threshold;
            confidenceValue.textContent = status.confidence_threshold;
        }
    }
}

/**
 * Take a snapshot from a camera
 */
function takeSnapshot(cameraName) {
    fetch(`/snapshot/${cameraName}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showAlert(`Snapshot saved for ${cameraName}`, 'success');
            
            // Reload snapshots if on snapshots tab
            if (!snapshotsView.classList.contains('d-none')) {
                loadSnapshots();
            }
        } else {
            showAlert(`Failed to take snapshot: ${data.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error taking snapshot:', error);
        showAlert('Error taking snapshot', 'danger');
    });
}

/**
 * Load and display snapshots
 */
function loadSnapshots() {
    fetch('/snapshots')
    .then(response => response.json())
    .then(snapshots => {
        // Clear grid
        snapshotGrid.innerHTML = '';
        
        if (snapshots.length === 0) {
            snapshotGrid.innerHTML = '<div class="col-12"><p>No snapshots available</p></div>';
            return;
        }
        
        // Sort by timestamp (newest first)
        snapshots.sort((a, b) => b.timestamp - a.timestamp);
        
        // Add snapshots to grid
        snapshots.forEach(snapshot => {
            // Clone template
            const snapshotElement = snapshotTemplate.content.cloneNode(true).querySelector('div');
            
            // Set image source
            const img = snapshotElement.querySelector('.snapshot-img');
            img.src = snapshot.url;
            
            // Set name and time
            const nameElement = snapshotElement.querySelector('.snapshot-name');
            nameElement.textContent = snapshot.filename.split('_')[0].replace(/_/g, ' ');
            
            const timeElement = snapshotElement.querySelector('.snapshot-time');
            const date = new Date(snapshot.timestamp * 1000);
            timeElement.textContent = date.toLocaleString();
            
            // Set download link
            const downloadLink = snapshotElement.querySelector('.snapshot-download');
            downloadLink.href = snapshot.url;
            downloadLink.download = snapshot.filename;
            
            // Add to grid
            snapshotGrid.appendChild(snapshotElement);
        });
    })
    .catch(error => {
        console.error('Error loading snapshots:', error);
        snapshotGrid.innerHTML = '<div class="col-12"><p>Error loading snapshots</p></div>';
    });
}

/**
 * Set up tab navigation
 */
function setupTabNavigation() {
    // Dashboard tab
    dashboardTab.addEventListener('click', (e) => {
        e.preventDefault();
        setActiveTab(dashboardTab, dashboardView);
    });
    
    // Snapshots tab
    snapshotsTab.addEventListener('click', (e) => {
        e.preventDefault();
        setActiveTab(snapshotsTab, snapshotsView);
        loadSnapshots();
    });
    
    // Settings tab
    settingsTab.addEventListener('click', (e) => {
        e.preventDefault();
        setActiveTab(settingsTab, settingsView);
    });
}

/**
 * Set active tab and view
 */
function setActiveTab(tab, view) {
    // Reset all tabs
    [dashboardTab, snapshotsTab, settingsTab].forEach(t => {
        t.classList.remove('active');
    });
    
    // Reset all views
    [dashboardView, snapshotsView, settingsView].forEach(v => {
        v.classList.add('d-none');
    });
    
    // Set active tab and view
    tab.classList.add('active');
    view.classList.remove('d-none');
}

/**
 * Show an alert message
 */
function showAlert(message, type = 'info') {
    // Create alert element
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertElement.style.top = '20px';
    alertElement.style.right = '20px';
    alertElement.style.zIndex = '9999';
    alertElement.setAttribute('role', 'alert');
    
    // Add message and close button
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to body
    document.body.appendChild(alertElement);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            alertElement.remove();
        }, 150);
    }, 3000);
}
