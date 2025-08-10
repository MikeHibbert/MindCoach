#!/usr/bin/env python3
"""
Test script for git automation hook

This script tests the git automation functionality without making actual commits.
"""

import sys
import os
from pathlib import Path

# Import the GitAutomation class directly
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


def test_git_automation():
    """Test the git automation functionality"""
    print("Testing Git Automation Hook...")
    
    # Initialize git automation
    git_automation = GitAutomation(project_root="../../..")
    
    # Test 1: Check if we're in a git repository
    print("\n1. Checking git repository...")
    if git_automation.check_git_repository():
        print("✓ Git repository detected")
    else:
        print("✗ Not in a git repository")
        return False
    
    # Test 2: Check git credentials
    print("\n2. Checking git credentials...")
    if git_automation.check_git_credentials():
        print("✓ Git credentials configured")
    else:
        print("⚠ Git credentials not configured (commits may fail)")
    
    # Test 3: Parse tasks file
    print("\n3. Parsing tasks file...")
    tasks_file = "../../../.kiro/specs/personalized-learning-path-generator/tasks.md"
    completed_tasks = git_automation.parse_completed_task(tasks_file)
    
    if completed_tasks:
        print(f"✓ Found {len(completed_tasks)} completed top-level tasks:")
        for task_number, task_description in completed_tasks:
            commit_message = git_automation.generate_commit_message(task_number, task_description)
            print(f"  - Task {task_number}: {task_description}")
            print(f"    Commit message: {commit_message}")
    else:
        print("ℹ No completed top-level tasks found")
    
    # Test 4: Check git status
    print("\n4. Checking git status...")
    status = git_automation.get_git_status()
    if status:
        total_changes = (len(status['modified']) + len(status['added']) + 
                        len(status['deleted']) + len(status['untracked']))
        print(f"✓ Git status retrieved: {total_changes} changes detected")
        if status['modified']:
            print(f"  Modified: {len(status['modified'])} files")
        if status['added']:
            print(f"  Added: {len(status['added'])} files")
        if status['deleted']:
            print(f"  Deleted: {len(status['deleted'])} files")
        if status['untracked']:
            print(f"  Untracked: {len(status['untracked'])} files")
    else:
        print("✗ Could not retrieve git status")
        return False
    
    print("\n✓ All tests passed! Git automation hook is ready.")
    return True


if __name__ == '__main__':
    success = test_git_automation()
    sys.exit(0 if success else 1)