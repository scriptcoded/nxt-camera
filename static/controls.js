/**
 * Client-side controls for NXT Camera Car
 * Handles keyboard input, button clicks, and WebSocket communication
 */

// Initialize Socket.IO connection
const socket = io();

// Track active keys to prevent repeat
const activeKeys = new Set();

// Connection status handlers
socket.on('connect', () => {
    console.log('Connected to server');
    updateConnectionStatus(true);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateConnectionStatus(false);
});

socket.on('status', (data) => {
    console.log('Status update:', data);
    updateCameraStatus(data.camera);
    updateNXTStatus(data.nxt);
});

socket.on('distance', (data) => {
    updateDistance(data.value);
});

socket.on('error', (data) => {
    console.error('Server error:', data.message);
    showError(data.message);
});

// Update status indicators
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('connection-indicator');
    if (connected) {
        indicator.classList.add('connected');
    } else {
        indicator.classList.remove('connected');
    }
}

function updateCameraStatus(connected) {
    const indicator = document.getElementById('camera-indicator');
    if (connected) {
        indicator.classList.add('connected');
    } else {
        indicator.classList.remove('connected');
    }
}

function updateNXTStatus(connected) {
    const indicator = document.getElementById('nxt-indicator');
    if (connected) {
        indicator.classList.add('connected');
    } else {
        indicator.classList.remove('connected');
    }
}

function updateDistance(value) {
    const distanceValue = document.getElementById('distance-value');
    if (value !== null && value >= 0) {
        distanceValue.textContent = value;
    } else {
        distanceValue.textContent = '--';
    }
}

function showError(message) {
    // Simple error display - could be enhanced with a toast notification
    console.error(message);
}

// Movement control functions
function sendMove(direction) {
    console.log('Move:', direction);
    socket.emit('move', { direction: direction });
}

function sendStop() {
    console.log('Stop');
    socket.emit('stop');
}

// Keyboard controls
const keyMap = {
    'w': 'forward',
    'W': 'forward',
    'ArrowUp': 'forward',
    's': 'backward',
    'S': 'backward',
    'ArrowDown': 'backward',
    'a': 'left',
    'A': 'left',
    'ArrowLeft': 'left',
    'd': 'right',
    'D': 'right',
    'ArrowRight': 'right'
};

document.addEventListener('keydown', (event) => {
    // Ignore if repeating or in input field
    if (event.repeat || event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }
    
    const direction = keyMap[event.key];
    if (direction && !activeKeys.has(event.key)) {
        event.preventDefault();
        activeKeys.add(event.key);
        sendMove(direction);
        
        // Visual feedback on corresponding button
        const button = document.querySelector(`[data-direction="${direction}"]`);
        if (button) {
            button.classList.add('active');
        }
    }
});

document.addEventListener('keyup', (event) => {
    const direction = keyMap[event.key];
    if (direction && activeKeys.has(event.key)) {
        event.preventDefault();
        activeKeys.delete(event.key);
        
        // Only stop if no other movement keys are pressed
        if (activeKeys.size === 0) {
            sendStop();
        }
        
        // Remove visual feedback
        const button = document.querySelector(`[data-direction="${direction}"]`);
        if (button) {
            button.classList.remove('active');
        }
    }
});

// Button controls
const controlButtons = document.querySelectorAll('.control-btn[data-direction]');
const stopButton = document.getElementById('btn-stop');

// Helper to handle button press
function handleButtonPress(button) {
    const direction = button.getAttribute('data-direction');
    if (direction) {
        sendMove(direction);
        button.classList.add('active');
    }
}

// Helper to handle button release
function handleButtonRelease(button) {
    sendStop();
    button.classList.remove('active');
}

// Mouse/touch events for direction buttons
controlButtons.forEach(button => {
    // Mouse events
    button.addEventListener('mousedown', (e) => {
        e.preventDefault();
        handleButtonPress(button);
    });
    
    button.addEventListener('mouseup', (e) => {
        e.preventDefault();
        handleButtonRelease(button);
    });
    
    button.addEventListener('mouseleave', (e) => {
        if (button.classList.contains('active')) {
            handleButtonRelease(button);
        }
    });
    
    // Touch events
    button.addEventListener('touchstart', (e) => {
        e.preventDefault();
        handleButtonPress(button);
    });
    
    button.addEventListener('touchend', (e) => {
        e.preventDefault();
        handleButtonRelease(button);
    });
    
    button.addEventListener('touchcancel', (e) => {
        e.preventDefault();
        handleButtonRelease(button);
    });
});

// Stop button
if (stopButton) {
    stopButton.addEventListener('click', (e) => {
        e.preventDefault();
        sendStop();
        // Clear all active states
        document.querySelectorAll('.control-btn.active').forEach(btn => {
            btn.classList.remove('active');
        });
        activeKeys.clear();
    });
}

// Prevent context menu on buttons (especially on touch devices)
document.querySelectorAll('.control-btn').forEach(button => {
    button.addEventListener('contextmenu', (e) => {
        e.preventDefault();
    });
});

// Emergency stop on window blur (user switches tabs/apps)
window.addEventListener('blur', () => {
    if (activeKeys.size > 0) {
        sendStop();
        activeKeys.clear();
        document.querySelectorAll('.control-btn.active').forEach(btn => {
            btn.classList.remove('active');
        });
    }
});

console.log('Controls initialized - Use WASD or arrow keys, or click/tap buttons to control');
