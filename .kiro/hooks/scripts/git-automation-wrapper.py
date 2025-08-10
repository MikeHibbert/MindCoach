#!/usr/bin/env python3
"""
Git Automation Wrapper for Kiro Agent Hooks

This wrapper script is called by the Kiro hook system when tasks are completed.
It provides enhanced error handling, logging, and integration with the hook system.

Requirements addressed:
- 11.2: Create commit message generation using task number and description
- 11.3: Follow commit message format "Complete Task X: [task description]"
- 11.4: Add git push functionality to automatically push commits to remote
- 11.5: Handle git authentication and network issues
- 11.6: Create logging system for git operations and error tracking
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Import the main GitAutomation class
current_dir = Path(__file__).parent
git_automation_path = current_dir / "git-automation.py"

# Read the git-automation.py file and extract only the classes we need
with open(git_automation_path, 'r') as f:
    content = f.read()

# Execute only the class definitions, not the main function
lines = content.split('\n')
class_content = []
in_main = False
for line in lines:
    if line.startswith('def main():'):
        in_main = True
    elif line.startswith('if __name__ == \'__main__\':'):
        break
    elif not in_main:
        class_content.append(line)

exec('\n'.join(class_content))


class GitAutomationWrapper:
    """
    Wrapper class for git automation that integrates with Kiro hook system
    """
    
    def __init__(self, hook_config_path=None):
        self.hook_config = self.load_hook_config(hook_config_path)
        self.setup_logging()
        
    def load_hook_config(self, config_path=None):
        """Load hook configuration from JSON file"""
        if not config_path:
            config_path = Path(__file__).parent.parent / "git-automation-hook.json"
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            # Fallback configuration
            return {
                "settings": {
                    "timeout": 300,
                    "retry_count": 3,
                    "retry_delay": 5
                },
                "logging": {
                    "level": "INFO",
                    "file": ".kiro/hooks/logs/git-automation.log"
                }
            }
    
    def setup_logging(self):
        """Set up logging based on hook configuration"""
        log_config = self.hook_config.get("logging", {})
        log_file = log_config.get("file", ".kiro/hooks/logs/git-automation.log")
        log_level = getattr(logging, log_config.get("level", "INFO"))
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Git automation wrapper initialized")
    
    def execute_with_retry(self, func, *args, **kwargs):
        """
        Execute a function with retry logic
        
        Requirement 11.5: Handle git authentication and network issues
        """
        settings = self.hook_config.get("settings", {})
        retry_count = settings.get("retry_count", 3)
        retry_delay = settings.get("retry_delay", 5)
        
        last_exception = None
        
        for attempt in range(retry_count + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < retry_count:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"All {retry_count + 1} attempts failed. Last error: {e}")
        
        raise last_exception
    
    def process_hook_trigger(self, task_file, project_root="."):
        """
        Process the hook trigger and execute git automation
        
        This is the main entry point called by the Kiro hook system
        
        Requirements addressed:
        - 11.2: Create commit message generation using task number and description
        - 11.3: Follow commit message format "Complete Task X: [task description]"
        - 11.4: Add git push functionality to automatically push commits to remote
        - 11.5: Handle git authentication and network issues
        - 11.6: Create logging system for git operations and error tracking
        """
        try:
            self.logger.info("Processing git automation hook trigger")
            self.logger.info(f"Task file: {task_file}")
            self.logger.info(f"Project root: {project_root}")
            
            # Initialize git automation
            git_automation = GitAutomation(
                project_root=project_root,
                log_file=self.hook_config.get("logging", {}).get("file")
            )
            
            # Execute git automation with retry logic
            success = self.execute_with_retry(
                git_automation.process_completed_tasks,
                task_file
            )
            
            if success:
                self.logger.info("Git automation completed successfully")
                return {
                    "status": "success",
                    "message": "Git automation completed successfully",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                self.logger.error("Git automation completed with errors")
                return {
                    "status": "error",
                    "message": "Git automation completed with errors",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Fatal error in git automation wrapper: {e}")
            return {
                "status": "error",
                "message": f"Fatal error: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def validate_environment(self):
        """
        Validate that the environment is ready for git automation
        
        Returns:
            dict: Validation results
        """
        results = {
            "git_repository": False,
            "git_credentials": False,
            "task_file_exists": False,
            "log_directory": False
        }
        
        try:
            # Check git repository
            git_automation = GitAutomation()
            results["git_repository"] = git_automation.check_git_repository()
            results["git_credentials"] = git_automation.check_git_credentials()
            
            # Check task file (use relative path from project root)
            task_file = Path("../../../.kiro/specs/personalized-learning-path-generator/tasks.md").resolve()
            results["task_file_exists"] = task_file.exists()
            
            # Check log directory
            log_file = self.hook_config.get("logging", {}).get("file", ".kiro/hooks/logs/git-automation.log")
            log_path = Path(log_file)
            results["log_directory"] = log_path.parent.exists()
            
            self.logger.info(f"Environment validation results: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error validating environment: {e}")
            return results


def main():
    """Main entry point for the wrapper script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Git Automation Wrapper for Kiro Hooks')
    parser.add_argument('--task-file', required=True, help='Path to tasks.md file')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--config', help='Hook configuration file path')
    parser.add_argument('--validate', action='store_true', help='Validate environment only')
    
    args = parser.parse_args()
    
    try:
        # Initialize wrapper
        wrapper = GitAutomationWrapper(args.config)
        
        if args.validate:
            # Validate environment
            results = wrapper.validate_environment()
            all_valid = all(results.values())
            
            print(f"Environment validation: {'PASSED' if all_valid else 'FAILED'}")
            for check, result in results.items():
                status = "✓" if result else "✗"
                print(f"  {status} {check.replace('_', ' ').title()}")
            
            sys.exit(0 if all_valid else 1)
        else:
            # Process hook trigger
            result = wrapper.process_hook_trigger(args.task_file, args.project_root)
            
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["status"] == "success" else 1)
    
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()