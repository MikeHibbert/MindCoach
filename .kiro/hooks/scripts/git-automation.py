#!/usr/bin/env python3
"""
Git Automation Script for Kiro Agent Hooks

This script automatically stages, commits, and pushes changes when top-level tasks
are completed in the tasks.md file.

Requirements addressed:
- 11.1: Automatically stage all new and modified files using git add
- 11.2: Create commit messages with task number and description
- 11.3: Follow commit message format "Complete Task X: [task description]"
- 11.4: Automatically push changes to remote repository
- 11.5: Handle authentication using existing git credentials
- 11.6: Log errors and notify user without interrupting workflow
- 11.7: Create separate commits for each completed task
"""

import os
import sys
import re
import subprocess
import logging
import json
from datetime import datetime
from pathlib import Path


class GitAutomationError(Exception):
    """Custom exception for git automation errors"""
    pass


class GitAutomation:
    def __init__(self, project_root=".", log_file=None):
        self.project_root = Path(project_root).resolve()
        self.setup_logging(log_file)
        
    def setup_logging(self, log_file=None):
        """Set up logging configuration"""
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_path),
                    logging.StreamHandler(sys.stdout)
                ]
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        
        self.logger = logging.getLogger(__name__)
    
    def run_git_command(self, command, check=True):
        """
        Execute a git command and return the result
        
        Args:
            command (list): Git command as list of strings
            check (bool): Whether to raise exception on non-zero exit code
            
        Returns:
            subprocess.CompletedProcess: Command result
            
        Raises:
            GitAutomationError: If command fails and check=True
        """
        try:
            self.logger.info(f"Executing git command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=check
            )
            
            if result.stdout:
                self.logger.debug(f"Git stdout: {result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"Git stderr: {result.stderr.strip()}")
                
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {' '.join(command)}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr.strip()}"
            self.logger.error(error_msg)
            raise GitAutomationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error running git command: {e}"
            self.logger.error(error_msg)
            raise GitAutomationError(error_msg) from e
    
    def check_git_repository(self):
        """
        Check if we're in a git repository
        
        Returns:
            bool: True if in git repository
        """
        try:
            self.run_git_command(['git', 'rev-parse', '--git-dir'])
            return True
        except GitAutomationError:
            return False
    
    def check_git_credentials(self):
        """
        Check if git credentials are configured
        
        Returns:
            bool: True if credentials are available
        """
        try:
            # Check if user.name and user.email are configured
            name_result = self.run_git_command(['git', 'config', 'user.name'])
            email_result = self.run_git_command(['git', 'config', 'user.email'])
            
            if name_result.stdout.strip() and email_result.stdout.strip():
                self.logger.info("Git credentials are configured")
                return True
            else:
                self.logger.warning("Git user.name or user.email not configured")
                return False
                
        except GitAutomationError:
            self.logger.warning("Could not check git credentials")
            return False
    
    def get_git_status(self):
        """
        Get git status information
        
        Returns:
            dict: Status information with modified, added, deleted files
        """
        try:
            result = self.run_git_command(['git', 'status', '--porcelain'])
            
            status = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': []
            }
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                status_code = line[:2]
                filename = line[3:]
                
                if status_code[0] == 'M' or status_code[1] == 'M':
                    status['modified'].append(filename)
                elif status_code[0] == 'A' or status_code[1] == 'A':
                    status['added'].append(filename)
                elif status_code[0] == 'D' or status_code[1] == 'D':
                    status['deleted'].append(filename)
                elif status_code == '??':
                    status['untracked'].append(filename)
            
            return status
            
        except GitAutomationError as e:
            self.logger.error(f"Failed to get git status: {e}")
            return None
    
    def stage_all_changes(self):
        """
        Stage all new and modified files
        
        Requirement 11.1: Automatically stage all new and modified files using git add
        """
        try:
            self.logger.info("Staging all changes...")
            
            # Add all files (new, modified, deleted)
            self.run_git_command(['git', 'add', '-A'])
            
            # Get status after staging
            status = self.get_git_status()
            if status:
                total_changes = (len(status['modified']) + len(status['added']) + 
                               len(status['deleted']) + len(status['untracked']))
                self.logger.info(f"Staged {total_changes} changes")
            
            return True
            
        except GitAutomationError as e:
            self.logger.error(f"Failed to stage changes: {e}")
            return False
    
    def generate_commit_message(self, task_number, task_description):
        """
        Generate commit message using task number and description
        
        Requirements 11.2, 11.3: Create commit message with format "Complete Task X: [task description]"
        
        Args:
            task_number (str): Task number (e.g., "15")
            task_description (str): Task description
            
        Returns:
            str: Formatted commit message
        """
        # Clean up task description (remove markdown formatting, etc.)
        clean_description = re.sub(r'[*_`]', '', task_description).strip()
        
        # Format: "Complete Task X: [task description]"
        commit_message = f"Complete Task {task_number}: {clean_description}"
        
        self.logger.info(f"Generated commit message: {commit_message}")
        return commit_message
    
    def create_commit(self, commit_message):
        """
        Create a git commit with the specified message
        
        Args:
            commit_message (str): Commit message
            
        Returns:
            bool: True if commit was successful
        """
        try:
            self.logger.info(f"Creating commit: {commit_message}")
            
            self.run_git_command(['git', 'commit', '-m', commit_message])
            
            self.logger.info("Commit created successfully")
            return True
            
        except GitAutomationError as e:
            # Check if the error is due to no changes to commit
            if "nothing to commit" in str(e).lower() or "no changes added to commit" in str(e).lower():
                self.logger.info("No changes to commit - skipping")
                return True  # This is not an error, just no changes
            else:
                self.logger.error(f"Failed to create commit: {e}")
                return False
    
    def push_to_remote(self):
        """
        Push changes to remote repository
        
        Requirement 11.4: Automatically push changes to remote repository
        
        Returns:
            bool: True if push was successful
        """
        try:
            self.logger.info("Pushing changes to remote repository...")
            
            # Get current branch name
            branch_result = self.run_git_command(['git', 'branch', '--show-current'])
            current_branch = branch_result.stdout.strip()
            
            if not current_branch:
                self.logger.error("Could not determine current branch")
                return False
            
            # Push to origin
            self.run_git_command(['git', 'push', 'origin', current_branch])
            
            self.logger.info(f"Successfully pushed to origin/{current_branch}")
            return True
            
        except GitAutomationError as e:
            self.logger.error(f"Failed to push to remote: {e}")
            return False
    
    def parse_completed_task(self, tasks_file):
        """
        Parse the tasks.md file to find completed top-level tasks
        
        Args:
            tasks_file (str): Path to tasks.md file
            
        Returns:
            list: List of tuples (task_number, task_description) for completed tasks
        """
        try:
            tasks_path = Path(tasks_file)
            if not tasks_path.exists():
                self.logger.error(f"Tasks file not found: {tasks_file}")
                return []
            
            with open(tasks_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern for completed top-level tasks: - [x] 15. Task description
            # Exclude subtasks: - [x] 15.1 Subtask description
            pattern = r'^- \[x\] (\d+)\. (.+)$'
            
            completed_tasks = []
            for line in content.split('\n'):
                match = re.match(pattern, line.strip())
                if match:
                    task_number = match.group(1)
                    task_description = match.group(2)
                    completed_tasks.append((task_number, task_description))
            
            self.logger.info(f"Found {len(completed_tasks)} completed top-level tasks")
            return completed_tasks
            
        except Exception as e:
            self.logger.error(f"Failed to parse tasks file: {e}")
            return []
    
    def get_last_processed_tasks(self, log_file):
        """
        Get list of tasks that were already processed from log file
        
        Args:
            log_file (str): Path to log file
            
        Returns:
            set: Set of task numbers that were already processed
        """
        processed_tasks = set()
        
        try:
            log_path = Path(log_file)
            if not log_path.exists():
                return processed_tasks
            
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'Successfully processed task' in line:
                        # Extract task number from log line
                        match = re.search(r'task (\d+)', line)
                        if match:
                            processed_tasks.add(match.group(1))
            
        except Exception as e:
            self.logger.warning(f"Could not read processed tasks from log: {e}")
        
        return processed_tasks
    
    def process_completed_tasks(self, tasks_file):
        """
        Process all newly completed tasks
        
        Requirement 11.7: Create separate commits for each completed task
        
        Args:
            tasks_file (str): Path to tasks.md file
            
        Returns:
            bool: True if all tasks were processed successfully
        """
        try:
            # Check if we're in a git repository
            if not self.check_git_repository():
                self.logger.error("Not in a git repository")
                return False
            
            # Check git credentials
            if not self.check_git_credentials():
                self.logger.warning("Git credentials not configured, commits may fail")
            
            # Get completed tasks
            completed_tasks = self.parse_completed_task(tasks_file)
            if not completed_tasks:
                self.logger.info("No completed top-level tasks found")
                return True
            
            # Get previously processed tasks to avoid duplicates
            log_file = self.logger.handlers[0].baseFilename if self.logger.handlers else None
            processed_tasks = self.get_last_processed_tasks(log_file) if log_file else set()
            
            # Process each newly completed task
            success_count = 0
            for task_number, task_description in completed_tasks:
                if task_number in processed_tasks:
                    self.logger.info(f"Task {task_number} already processed, skipping")
                    continue
                
                self.logger.info(f"Processing completed task {task_number}: {task_description}")
                
                # Stage all changes
                if not self.stage_all_changes():
                    self.logger.error(f"Failed to stage changes for task {task_number}")
                    continue
                
                # Check if there are actually changes to commit
                status = self.get_git_status()
                if status:
                    total_changes = (len(status['modified']) + len(status['added']) + 
                                   len(status['deleted']) + len(status['untracked']))
                    if total_changes == 0:
                        self.logger.info(f"No changes to commit for task {task_number} - skipping")
                        continue
                
                # Generate commit message
                commit_message = self.generate_commit_message(task_number, task_description)
                
                # Create commit
                if not self.create_commit(commit_message):
                    self.logger.error(f"Failed to create commit for task {task_number}")
                    continue
                
                # Push to remote
                if not self.push_to_remote():
                    self.logger.error(f"Failed to push changes for task {task_number}")
                    # Don't continue here - commit was created, just push failed
                
                self.logger.info(f"Successfully processed task {task_number}")
                success_count += 1
            
            self.logger.info(f"Processed {success_count} out of {len(completed_tasks)} tasks")
            return success_count == len(completed_tasks)
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing tasks: {e}")
            return False


def main():
    """Main entry point for the git automation script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Git Automation for Kiro Agent Hooks')
    parser.add_argument('--task-file', required=True, help='Path to tasks.md file')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--log-file', help='Log file path')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    try:
        # Initialize git automation
        git_automation = GitAutomation(
            project_root=args.project_root,
            log_file=args.log_file
        )
        
        if args.dry_run:
            git_automation.logger.info("DRY RUN MODE - No changes will be made")
            completed_tasks = git_automation.parse_completed_task(args.task_file)
            for task_number, task_description in completed_tasks:
                commit_message = git_automation.generate_commit_message(task_number, task_description)
                git_automation.logger.info(f"Would create commit: {commit_message}")
        else:
            # Process completed tasks
            success = git_automation.process_completed_tasks(args.task_file)
            
            if success:
                git_automation.logger.info("Git automation completed successfully")
                sys.exit(0)
            else:
                git_automation.logger.error("Git automation completed with errors")
                sys.exit(1)
    
    except Exception as e:
        logging.error(f"Fatal error in git automation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()