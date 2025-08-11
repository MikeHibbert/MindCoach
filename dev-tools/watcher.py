#!/usr/bin/env python3
"""
File watcher for development environment
Monitors file changes and triggers appropriate actions
"""

import os
import time
import logging
import docker
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DevelopmentFileHandler(FileSystemEventHandler):
    """Handle file system events for development"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.project_name = os.getenv('COMPOSE_PROJECT_NAME', 'mindcoach')
        self.last_rebuild = {}
        self.rebuild_cooldown = 30  # seconds
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        self.handle_file_change(file_path, 'modified')
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        self.handle_file_change(file_path, 'created')
    
    def handle_file_change(self, file_path: Path, change_type: str):
        """Handle different types of file changes"""
        try:
            relative_path = file_path.relative_to('/workspace')
            logger.info(f"File {change_type}: {relative_path}")
            
            # Handle different file types
            if self.should_rebuild_container(file_path):
                self.trigger_container_rebuild(file_path)
            elif self.should_restart_service(file_path):
                self.trigger_service_restart(file_path)
            elif self.should_reload_config(file_path):
                self.trigger_config_reload(file_path)
                
        except ValueError:
            # File is outside workspace, ignore
            pass
        except Exception as e:
            logger.error(f"Error handling file change {file_path}: {e}")
    
    def should_rebuild_container(self, file_path: Path) -> bool:
        """Check if file change should trigger container rebuild"""
        rebuild_triggers = [
            'Dockerfile',
            'Dockerfile.dev',
            'Dockerfile.prod',
            'requirements.txt',
            'requirements-dev.txt',
            'package.json',
            'package-lock.json'
        ]
        
        return file_path.name in rebuild_triggers
    
    def should_restart_service(self, file_path: Path) -> bool:
        """Check if file change should trigger service restart"""
        restart_triggers = [
            '.py',  # Python files
            '.js',  # JavaScript files (for Node.js services)
            '.json',  # Configuration files
            '.yml',  # YAML configuration
            '.yaml'
        ]
        
        # Skip certain directories
        skip_dirs = ['node_modules', 'venv', '__pycache__', '.git', 'logs', 'data']
        if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
            return False
        
        return file_path.suffix in restart_triggers
    
    def should_reload_config(self, file_path: Path) -> bool:
        """Check if file change should trigger config reload"""
        config_files = [
            '.env',
            '.env.dev',
            'docker-compose.dev.yml',
            'nginx.conf'
        ]
        
        return file_path.name in config_files
    
    def trigger_container_rebuild(self, file_path: Path):
        """Trigger container rebuild for affected service"""
        try:
            service_name = self.get_service_from_path(file_path)
            if not service_name:
                return
            
            # Check cooldown
            now = time.time()
            last_rebuild = self.last_rebuild.get(service_name, 0)
            if now - last_rebuild < self.rebuild_cooldown:
                logger.info(f"Rebuild for {service_name} in cooldown period")
                return
            
            logger.info(f"Triggering rebuild for service: {service_name}")
            
            # Use docker-compose to rebuild
            import subprocess
            result = subprocess.run([
                'docker-compose', '-f', '/workspace/docker-compose.dev.yml',
                'build', '--no-cache', service_name
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Successfully rebuilt {service_name}")
                
                # Restart the service
                subprocess.run([
                    'docker-compose', '-f', '/workspace/docker-compose.dev.yml',
                    'up', '-d', '--no-deps', service_name
                ], timeout=60)
                
                self.last_rebuild[service_name] = now
            else:
                logger.error(f"Failed to rebuild {service_name}: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error rebuilding container: {e}")
    
    def trigger_service_restart(self, file_path: Path):
        """Trigger service restart for affected service"""
        try:
            service_name = self.get_service_from_path(file_path)
            if not service_name:
                return
            
            logger.info(f"Triggering restart for service: {service_name}")
            
            # Find and restart the container
            containers = self.docker_client.containers.list(
                filters={'label': f'com.docker.compose.service={service_name}'}
            )
            
            for container in containers:
                container.restart()
                logger.info(f"Restarted container: {container.name}")
                
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
    
    def trigger_config_reload(self, file_path: Path):
        """Trigger configuration reload"""
        try:
            logger.info(f"Configuration file changed: {file_path.name}")
            
            if file_path.name in ['.env', '.env.dev']:
                logger.info("Environment file changed, restart all services")
                self.restart_all_services()
            elif 'docker-compose' in file_path.name:
                logger.info("Docker Compose file changed, recreating services")
                self.recreate_services()
                
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
    
    def get_service_from_path(self, file_path: Path) -> str:
        """Determine service name from file path"""
        path_parts = file_path.parts
        
        # Map directories to services
        service_mapping = {
            'backend': 'backend-dev',
            'frontend': 'frontend-dev',
            'dev-tools': 'dev-tools',
            'nginx': 'nginx-dev'
        }
        
        for part in path_parts:
            if part in service_mapping:
                return service_mapping[part]
        
        return None
    
    def restart_all_services(self):
        """Restart all development services"""
        try:
            import subprocess
            subprocess.run([
                'docker-compose', '-f', '/workspace/docker-compose.dev.yml',
                'restart'
            ], timeout=120)
            logger.info("All services restarted")
        except Exception as e:
            logger.error(f"Error restarting all services: {e}")
    
    def recreate_services(self):
        """Recreate services with new configuration"""
        try:
            import subprocess
            subprocess.run([
                'docker-compose', '-f', '/workspace/docker-compose.dev.yml',
                'up', '-d', '--force-recreate'
            ], timeout=180)
            logger.info("Services recreated")
        except Exception as e:
            logger.error(f"Error recreating services: {e}")


def main():
    """Main file watcher process"""
    logger.info("Starting development file watcher...")
    
    # Create event handler and observer
    event_handler = DevelopmentFileHandler()
    observer = Observer()
    
    # Watch the workspace directory
    workspace_path = '/workspace'
    observer.schedule(event_handler, workspace_path, recursive=True)
    
    # Start watching
    observer.start()
    logger.info(f"Watching for file changes in {workspace_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        observer.stop()
    
    observer.join()
    logger.info("File watcher stopped")


if __name__ == '__main__':
    main()