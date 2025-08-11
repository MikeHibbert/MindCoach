#!/usr/bin/env python3
"""
Auto-scaling service for MindCoach
Monitors metrics and scales services based on load
"""

import os
import time
import logging
import requests
import docker
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScalingConfig:
    """Configuration for auto-scaling"""
    service_name: str
    min_replicas: int
    max_replicas: int
    scale_up_threshold: float
    scale_down_threshold: float
    scale_up_cooldown: int  # seconds
    scale_down_cooldown: int  # seconds
    metric_name: str
    metric_query: str


class MetricsCollector:
    """Collects metrics from Prometheus"""
    
    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url.rstrip('/')
    
    def query_metric(self, query: str) -> Optional[float]:
        """Query a metric from Prometheus"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data['status'] == 'success' and data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to query metric '{query}': {e}")
            return None
    
    def get_cpu_usage(self, service_name: str) -> Optional[float]:
        """Get CPU usage percentage for a service"""
        query = f'avg(rate(container_cpu_usage_seconds_total{{name=~"{service_name}.*"}}[5m])) * 100'
        return self.query_metric(query)
    
    def get_memory_usage(self, service_name: str) -> Optional[float]:
        """Get memory usage percentage for a service"""
        query = f'avg(container_memory_usage_bytes{{name=~"{service_name}.*"}} / container_spec_memory_limit_bytes{{name=~"{service_name}.*"}}) * 100'
        return self.query_metric(query)
    
    def get_request_rate(self, service_name: str) -> Optional[float]:
        """Get request rate for a service"""
        query = f'sum(rate(http_requests_total{{service="{service_name}"}}[5m]))'
        return self.query_metric(query)
    
    def get_response_time(self, service_name: str) -> Optional[float]:
        """Get average response time for a service"""
        query = f'avg(http_request_duration_seconds{{service="{service_name}"}}) * 1000'
        return self.query_metric(query)
    
    def get_queue_length(self, queue_name: str) -> Optional[float]:
        """Get queue length for Celery tasks"""
        query = f'celery_queue_length{{queue="{queue_name}"}}'
        return self.query_metric(query)


class DockerScaler:
    """Handles Docker service scaling"""
    
    def __init__(self):
        self.client = docker.from_env()
    
    def get_service_replicas(self, service_name: str) -> Optional[int]:
        """Get current number of replicas for a service"""
        try:
            # For Docker Compose, we need to count containers
            containers = self.client.containers.list(
                filters={'label': f'com.docker.compose.service={service_name}'}
            )
            return len([c for c in containers if c.status == 'running'])
            
        except Exception as e:
            logger.error(f"Failed to get replicas for {service_name}: {e}")
            return None
    
    def scale_service(self, service_name: str, replicas: int) -> bool:
        """Scale a service to the specified number of replicas"""
        try:
            # Use docker-compose to scale
            import subprocess
            
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.scale.yml',
                'up', '-d', '--scale', f'{service_name}={replicas}',
                '--no-recreate'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info(f"Successfully scaled {service_name} to {replicas} replicas")
                return True
            else:
                logger.error(f"Failed to scale {service_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to scale {service_name} to {replicas}: {e}")
            return False


class AutoScaler:
    """Main auto-scaling service"""
    
    def __init__(self, config_file: str = 'autoscaler-config.json'):
        self.metrics_collector = MetricsCollector(
            os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        )
        self.docker_scaler = DockerScaler()
        self.scaling_configs = self._load_config(config_file)
        self.last_scale_actions = {}  # Track cooldown periods
        self.running = False
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
    
    def _load_config(self, config_file: str) -> List[ScalingConfig]:
        """Load scaling configuration"""
        default_config = [
            ScalingConfig(
                service_name='backend',
                min_replicas=2,
                max_replicas=10,
                scale_up_threshold=80.0,
                scale_down_threshold=20.0,
                scale_up_cooldown=300,  # 5 minutes
                scale_down_cooldown=600,  # 10 minutes
                metric_name='cpu_usage',
                metric_query='cpu'
            ),
            ScalingConfig(
                service_name='celery-worker',
                min_replicas=2,
                max_replicas=8,
                scale_up_threshold=10.0,  # Queue length
                scale_down_threshold=2.0,
                scale_up_cooldown=180,  # 3 minutes
                scale_down_cooldown=600,  # 10 minutes
                metric_name='queue_length',
                metric_query='queue'
            ),
            ScalingConfig(
                service_name='nginx',
                min_replicas=2,
                max_replicas=5,
                scale_up_threshold=70.0,
                scale_down_threshold=30.0,
                scale_up_cooldown=300,
                scale_down_cooldown=600,
                metric_name='cpu_usage',
                metric_query='cpu'
            )
        ]
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    return [ScalingConfig(**cfg) for cfg in config_data]
            else:
                # Create default config file
                with open(config_file, 'w') as f:
                    json.dump([cfg.__dict__ for cfg in default_config], f, indent=2)
                logger.info(f"Created default config file: {config_file}")
                
        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
        
        return default_config
    
    def _get_metric_value(self, config: ScalingConfig) -> Optional[float]:
        """Get metric value based on configuration"""
        if config.metric_name == 'cpu_usage':
            return self.metrics_collector.get_cpu_usage(config.service_name)
        elif config.metric_name == 'memory_usage':
            return self.metrics_collector.get_memory_usage(config.service_name)
        elif config.metric_name == 'request_rate':
            return self.metrics_collector.get_request_rate(config.service_name)
        elif config.metric_name == 'response_time':
            return self.metrics_collector.get_response_time(config.service_name)
        elif config.metric_name == 'queue_length':
            return self.metrics_collector.get_queue_length(config.service_name)
        else:
            logger.warning(f"Unknown metric type: {config.metric_name}")
            return None
    
    def _should_scale_up(self, config: ScalingConfig, current_replicas: int, metric_value: float) -> bool:
        """Determine if service should be scaled up"""
        if current_replicas >= config.max_replicas:
            return False
        
        if metric_value < config.scale_up_threshold:
            return False
        
        # Check cooldown period
        last_action = self.last_scale_actions.get(config.service_name)
        if last_action:
            time_since_last = (datetime.now() - last_action['timestamp']).total_seconds()
            if time_since_last < config.scale_up_cooldown:
                logger.debug(f"Scale up for {config.service_name} in cooldown period")
                return False
        
        return True
    
    def _should_scale_down(self, config: ScalingConfig, current_replicas: int, metric_value: float) -> bool:
        """Determine if service should be scaled down"""
        if current_replicas <= config.min_replicas:
            return False
        
        if metric_value > config.scale_down_threshold:
            return False
        
        # Check cooldown period
        last_action = self.last_scale_actions.get(config.service_name)
        if last_action:
            time_since_last = (datetime.now() - last_action['timestamp']).total_seconds()
            if time_since_last < config.scale_down_cooldown:
                logger.debug(f"Scale down for {config.service_name} in cooldown period")
                return False
        
        return True
    
    def _scale_service(self, config: ScalingConfig, target_replicas: int, action: str) -> bool:
        """Scale a service and record the action"""
        success = self.docker_scaler.scale_service(config.service_name, target_replicas)
        
        if success:
            self.last_scale_actions[config.service_name] = {
                'timestamp': datetime.now(),
                'action': action,
                'target_replicas': target_replicas
            }
            
            # Log scaling action
            logger.info(f"Scaled {config.service_name} {action} to {target_replicas} replicas")
            
            # Send notification (if configured)
            self._send_notification(config.service_name, action, target_replicas)
        
        return success
    
    def _send_notification(self, service_name: str, action: str, replicas: int):
        """Send scaling notification"""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if webhook_url:
            try:
                message = f"🔄 Auto-scaled {service_name} {action} to {replicas} replicas"
                requests.post(
                    webhook_url,
                    json={'text': message},
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    def check_and_scale(self):
        """Check metrics and scale services if needed"""
        for config in self.scaling_configs:
            try:
                # Get current metrics and replica count
                metric_value = self._get_metric_value(config)
                current_replicas = self.docker_scaler.get_service_replicas(config.service_name)
                
                if metric_value is None or current_replicas is None:
                    logger.warning(f"Could not get metrics for {config.service_name}")
                    continue
                
                logger.debug(
                    f"{config.service_name}: {config.metric_name}={metric_value:.2f}, "
                    f"replicas={current_replicas}"
                )
                
                # Determine scaling action
                if self._should_scale_up(config, current_replicas, metric_value):
                    target_replicas = min(current_replicas + 1, config.max_replicas)
                    self._scale_service(config, target_replicas, 'up')
                    
                elif self._should_scale_down(config, current_replicas, metric_value):
                    target_replicas = max(current_replicas - 1, config.min_replicas)
                    self._scale_service(config, target_replicas, 'down')
                
            except Exception as e:
                logger.error(f"Error checking {config.service_name}: {e}")
    
    def get_status(self) -> Dict:
        """Get current auto-scaler status"""
        status = {
            'running': self.running,
            'check_interval': self.check_interval,
            'services': {},
            'last_check': datetime.now().isoformat()
        }
        
        for config in self.scaling_configs:
            current_replicas = self.docker_scaler.get_service_replicas(config.service_name)
            metric_value = self._get_metric_value(config)
            last_action = self.last_scale_actions.get(config.service_name)
            
            status['services'][config.service_name] = {
                'current_replicas': current_replicas,
                'min_replicas': config.min_replicas,
                'max_replicas': config.max_replicas,
                'metric_value': metric_value,
                'metric_name': config.metric_name,
                'scale_up_threshold': config.scale_up_threshold,
                'scale_down_threshold': config.scale_down_threshold,
                'last_action': last_action
            }
        
        return status
    
    def start(self):
        """Start the auto-scaling service"""
        logger.info("Starting auto-scaler service")
        self.running = True
        
        while self.running:
            try:
                self.check_and_scale()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in auto-scaler main loop: {e}")
                time.sleep(self.check_interval)
        
        logger.info("Auto-scaler service stopped")
    
    def stop(self):
        """Stop the auto-scaling service"""
        logger.info("Stopping auto-scaler service")
        self.running = False


def main():
    """Main entry point"""
    autoscaler = AutoScaler()
    
    # Start status API in background thread
    def status_api():
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        @app.route('/status')
        def status():
            return jsonify(autoscaler.get_status())
        
        @app.route('/health')
        def health():
            return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
        
        app.run(host='0.0.0.0', port=8080, debug=False)
    
    # Start API in background
    api_thread = threading.Thread(target=status_api, daemon=True)
    api_thread.start()
    
    # Start auto-scaler
    try:
        autoscaler.start()
    except KeyboardInterrupt:
        autoscaler.stop()


if __name__ == '__main__':
    main()