const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const Docker = require('dockerode');
const chokidar = require('chokidar');
const axios = require('axios');
const cors = require('cors');
const morgan = require('morgan');
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

const docker = new Docker();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Development dashboard data
let dashboardData = {
  services: {},
  logs: [],
  metrics: {},
  fileChanges: [],
  lastUpdate: new Date()
};

// Monitor Docker containers
async function monitorContainers() {
  try {
    const containers = await docker.listContainers({ all: true });
    const services = {};
    
    for (const containerInfo of containers) {
      const container = docker.getContainer(containerInfo.Id);
      const inspect = await container.inspect();
      
      const serviceName = inspect.Config.Labels['com.docker.compose.service'] || 'unknown';
      
      services[serviceName] = {
        id: containerInfo.Id.substring(0, 12),
        name: containerInfo.Names[0].substring(1),
        status: containerInfo.State,
        image: containerInfo.Image,
        ports: containerInfo.Ports,
        created: containerInfo.Created,
        labels: inspect.Config.Labels,
        env: inspect.Config.Env,
        mounts: inspect.Mounts,
        networkSettings: inspect.NetworkSettings
      };
    }
    
    dashboardData.services = services;
    dashboardData.lastUpdate = new Date();
    
    // Emit to connected clients
    io.emit('services-update', services);
    
  } catch (error) {
    console.error('Error monitoring containers:', error);
  }
}

// Monitor file changes
function monitorFileChanges() {
  const watcher = chokidar.watch('/workspace', {
    ignored: [
      '**/node_modules/**',
      '**/venv/**',
      '**/.git/**',
      '**/logs/**',
      '**/data/**',
      '**/__pycache__/**',
      '**/coverage/**',
      '**/build/**',
      '**/dist/**'
    ],
    persistent: true
  });
  
  watcher.on('change', (filePath) => {
    const change = {
      type: 'change',
      path: filePath.replace('/workspace/', ''),
      timestamp: new Date()
    };
    
    dashboardData.fileChanges.unshift(change);
    if (dashboardData.fileChanges.length > 100) {
      dashboardData.fileChanges = dashboardData.fileChanges.slice(0, 100);
    }
    
    io.emit('file-change', change);
    console.log(`File changed: ${change.path}`);
  });
  
  watcher.on('add', (filePath) => {
    const change = {
      type: 'add',
      path: filePath.replace('/workspace/', ''),
      timestamp: new Date()
    };
    
    dashboardData.fileChanges.unshift(change);
    if (dashboardData.fileChanges.length > 100) {
      dashboardData.fileChanges = dashboardData.fileChanges.slice(0, 100);
    }
    
    io.emit('file-change', change);
  });
}

// Collect service metrics
async function collectMetrics() {
  try {
    const metrics = {};
    
    // Get container stats
    const containers = await docker.listContainers();
    for (const containerInfo of containers) {
      const container = docker.getContainer(containerInfo.Id);
      try {
        const stats = await container.stats({ stream: false });
        const serviceName = containerInfo.Names[0].substring(1);
        
        metrics[serviceName] = {
          cpu: calculateCPUPercent(stats),
          memory: calculateMemoryPercent(stats),
          network: stats.networks,
          timestamp: new Date()
        };
      } catch (error) {
        console.error(`Error getting stats for ${containerInfo.Names[0]}:`, error);
      }
    }
    
    // Try to get application metrics
    try {
      const healthResponse = await axios.get('http://backend-dev:5000/api/health', { timeout: 5000 });
      metrics.application = {
        health: healthResponse.data,
        timestamp: new Date()
      };
    } catch (error) {
      metrics.application = {
        health: { status: 'unavailable', error: error.message },
        timestamp: new Date()
      };
    }
    
    dashboardData.metrics = metrics;
    io.emit('metrics-update', metrics);
    
  } catch (error) {
    console.error('Error collecting metrics:', error);
  }
}

// Helper functions
function calculateCPUPercent(stats) {
  const cpuDelta = stats.cpu_stats.cpu_usage.total_usage - stats.precpu_stats.cpu_usage.total_usage;
  const systemDelta = stats.cpu_stats.system_cpu_usage - stats.precpu_stats.system_cpu_usage;
  const numberCpus = stats.cpu_stats.online_cpus || 1;
  
  if (systemDelta > 0 && cpuDelta > 0) {
    return (cpuDelta / systemDelta) * numberCpus * 100;
  }
  return 0;
}

function calculateMemoryPercent(stats) {
  if (stats.memory_stats.limit) {
    return (stats.memory_stats.usage / stats.memory_stats.limit) * 100;
  }
  return 0;
}

// API Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date() });
});

app.get('/api/dashboard', (req, res) => {
  res.json(dashboardData);
});

app.get('/api/services', (req, res) => {
  res.json(dashboardData.services);
});

app.get('/api/metrics', (req, res) => {
  res.json(dashboardData.metrics);
});

app.get('/api/logs/:service', async (req, res) => {
  try {
    const serviceName = req.params.service;
    const containers = await docker.listContainers();
    const container = containers.find(c => c.Names[0].includes(serviceName));
    
    if (!container) {
      return res.status(404).json({ error: 'Service not found' });
    }
    
    const dockerContainer = docker.getContainer(container.Id);
    const logs = await dockerContainer.logs({
      stdout: true,
      stderr: true,
      tail: 100,
      timestamps: true
    });
    
    res.json({ logs: logs.toString() });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/services/:service/restart', async (req, res) => {
  try {
    const serviceName = req.params.service;
    const containers = await docker.listContainers({ all: true });
    const container = containers.find(c => c.Names[0].includes(serviceName));
    
    if (!container) {
      return res.status(404).json({ error: 'Service not found' });
    }
    
    const dockerContainer = docker.getContainer(container.Id);
    await dockerContainer.restart();
    
    res.json({ message: `Service ${serviceName} restarted successfully` });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/services/:service/stop', async (req, res) => {
  try {
    const serviceName = req.params.service;
    const containers = await docker.listContainers();
    const container = containers.find(c => c.Names[0].includes(serviceName));
    
    if (!container) {
      return res.status(404).json({ error: 'Service not found' });
    }
    
    const dockerContainer = docker.getContainer(container.Id);
    await dockerContainer.stop();
    
    res.json({ message: `Service ${serviceName} stopped successfully` });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/services/:service/start', async (req, res) => {
  try {
    const serviceName = req.params.service;
    const containers = await docker.listContainers({ all: true });
    const container = containers.find(c => c.Names[0].includes(serviceName));
    
    if (!container) {
      return res.status(404).json({ error: 'Service not found' });
    }
    
    const dockerContainer = docker.getContainer(container.Id);
    await dockerContainer.start();
    
    res.json({ message: `Service ${serviceName} started successfully` });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('Client connected to development dashboard');
  
  // Send initial data
  socket.emit('services-update', dashboardData.services);
  socket.emit('metrics-update', dashboardData.metrics);
  
  socket.on('disconnect', () => {
    console.log('Client disconnected from development dashboard');
  });
});

// Serve development dashboard
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start monitoring
monitorContainers();
monitorFileChanges();
collectMetrics();

// Set up intervals
setInterval(monitorContainers, 10000); // Every 10 seconds
setInterval(collectMetrics, 5000);     // Every 5 seconds

// Start server
server.listen(PORT, '0.0.0.0', () => {
  console.log(`Development dashboard running on port ${PORT}`);
  console.log(`Dashboard URL: http://localhost:${PORT}`);
});