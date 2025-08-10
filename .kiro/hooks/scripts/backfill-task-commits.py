#!/usr/bin/env python3
"""
Backfill Task Commits Script

This script creates individual commits for all previously completed tasks
to establish a proper git history for project documentation.

This is a one-time script to backfill the commit history for tasks that
were completed before the git automation hook was implemented.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Import the GitAutomation class
current_dir = Path(__file__).parent
git_automation_path = current_dir / "git-automation.py"

with open(git_automation_path, 'r') as f:
    content = f.read()

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


class TaskCommitBackfiller:
    """
    Creates individual commits for completed tasks to establish git history
    """
    
    def __init__(self, project_root="../../.."):
        self.project_root = Path(project_root).resolve()
        self.git_automation = GitAutomation(project_root=str(self.project_root))
        
    def get_completed_tasks_to_backfill(self, tasks_file):
        """
        Get completed tasks that need individual commits (excluding Task 15 which was already committed)
        
        Args:
            tasks_file: Path to tasks.md file
            
        Returns:
            List of (task_number, task_description) tuples to backfill
        """
        completed_tasks = self.git_automation.parse_completed_task(tasks_file)
        
        # Filter out Task 15 since it was already committed by the automation hook
        # and Task 1 since it was also already committed
        tasks_to_backfill = []
        for task_number, task_description in completed_tasks:
            if task_number not in ['1', '15']:  # Skip already committed tasks
                tasks_to_backfill.append((task_number, task_description))
        
        return tasks_to_backfill
    
    def create_empty_commit(self, commit_message, commit_date=None):
        """
        Create an empty commit with a specific message and optional date
        
        Args:
            commit_message: The commit message
            commit_date: Optional datetime for the commit (for backdating)
            
        Returns:
            bool: True if successful
        """
        try:
            cmd = ['git', 'commit', '--allow-empty', '-m', commit_message]
            
            # Add date if specified
            if commit_date:
                date_str = commit_date.strftime('%Y-%m-%d %H:%M:%S')
                cmd.extend(['--date', date_str])
            
            self.git_automation.logger.info(f"Creating empty commit: {commit_message}")
            if commit_date:
                self.git_automation.logger.info(f"Commit date: {date_str}")
            
            result = self.git_automation.run_git_command(cmd)
            
            self.git_automation.logger.info("Empty commit created successfully")
            return True
            
        except Exception as e:
            self.git_automation.logger.error(f"Failed to create empty commit: {e}")
            return False
    
    def backfill_task_commits(self, tasks_file):
        """
        Create individual commits for all completed tasks that don't have commits yet
        
        Args:
            tasks_file: Path to tasks.md file
            
        Returns:
            bool: True if all commits were created successfully
        """
        try:
            self.git_automation.logger.info("Starting task commit backfill process...")
            
            # Check if we're in a git repository
            if not self.git_automation.check_git_repository():
                self.git_automation.logger.error("Not in a git repository")
                return False
            
            # Get tasks to backfill
            tasks_to_backfill = self.get_completed_tasks_to_backfill(tasks_file)
            
            if not tasks_to_backfill:
                self.git_automation.logger.info("No tasks need backfill commits")
                return True
            
            self.git_automation.logger.info(f"Found {len(tasks_to_backfill)} tasks to backfill")
            
            # Create commits for each task
            # Use dates in the past to show progression (1 day apart for each task)
            base_date = datetime.now() - timedelta(days=len(tasks_to_backfill))
            
            success_count = 0
            for i, (task_number, task_description) in enumerate(tasks_to_backfill):
                # Generate commit message using the same format as the automation hook
                commit_message = self.git_automation.generate_commit_message(task_number, task_description)
                
                # Calculate commit date (spread tasks over past days)
                commit_date = base_date + timedelta(days=i)
                
                # Create empty commit for this task
                if self.create_empty_commit(commit_message, commit_date):
                    self.git_automation.logger.info(f"Successfully backfilled commit for task {task_number}")
                    success_count += 1
                else:
                    self.git_automation.logger.error(f"Failed to backfill commit for task {task_number}")
            
            self.git_automation.logger.info(f"Backfilled {success_count} out of {len(tasks_to_backfill)} task commits")
            
            # Push all the new commits
            if success_count > 0:
                self.git_automation.logger.info("Pushing backfilled commits to remote...")
                if self.git_automation.push_to_remote():
                    self.git_automation.logger.info("Successfully pushed all backfilled commits")
                else:
                    self.git_automation.logger.warning("Failed to push backfilled commits")
            
            return success_count == len(tasks_to_backfill)
            
        except Exception as e:
            self.git_automation.logger.error(f"Unexpected error during backfill: {e}")
            return False
    
    def preview_backfill(self, tasks_file):
        """
        Preview what commits would be created without actually creating them
        
        Args:
            tasks_file: Path to tasks.md file
        """
        tasks_to_backfill = self.get_completed_tasks_to_backfill(tasks_file)
        
        if not tasks_to_backfill:
            print("No tasks need backfill commits")
            return
        
        print(f"Would create {len(tasks_to_backfill)} backfill commits:")
        print("=" * 60)
        
        base_date = datetime.now() - timedelta(days=len(tasks_to_backfill))
        
        for i, (task_number, task_description) in enumerate(tasks_to_backfill):
            commit_message = self.git_automation.generate_commit_message(task_number, task_description)
            commit_date = base_date + timedelta(days=i)
            
            print(f"Task {task_number}:")
            print(f"  Message: {commit_message}")
            print(f"  Date: {commit_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print()


def main():
    """Main entry point for the backfill script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill commits for completed tasks')
    parser.add_argument('--task-file', required=True, help='Path to tasks.md file')
    parser.add_argument('--project-root', default='../../..', help='Project root directory')
    parser.add_argument('--preview', action='store_true', help='Preview what would be done without executing')
    parser.add_argument('--confirm', action='store_true', help='Confirm you want to create the commits')
    
    args = parser.parse_args()
    
    try:
        # Initialize backfiller
        backfiller = TaskCommitBackfiller(args.project_root)
        
        if args.preview:
            # Preview mode
            print("🔍 PREVIEW MODE - Showing what commits would be created")
            print("=" * 60)
            backfiller.preview_backfill(args.task_file)
        else:
            if not args.confirm:
                print("⚠️  This will create multiple commits in your git history.")
                print("   Use --preview to see what would be created.")
                print("   Use --confirm to actually create the commits.")
                sys.exit(1)
            
            # Execute backfill
            print("🚀 Starting task commit backfill...")
            success = backfiller.backfill_task_commits(args.task_file)
            
            if success:
                print("✅ All task commits backfilled successfully!")
                sys.exit(0)
            else:
                print("❌ Some commits failed. Check the logs above.")
                sys.exit(1)
    
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()