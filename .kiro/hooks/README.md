# Kiro Agent Hooks

This directory contains agent hook configurations and scripts for automated workflows.

## Git Automation Hook

The git automation hook automatically commits and pushes code changes when top-level tasks are completed in the tasks.md file.

### Configuration

- **Hook Config**: `git-automation-hook.json`
- **Script**: `scripts/git-automation.py`
- **Logs**: `logs/git-automation.log`

### How it Works

1. **Trigger**: Monitors changes to `.kiro/specs/personalized-learning-path-generator/tasks.md`
2. **Detection**: Detects when top-level tasks are marked as completed (pattern: `- [x] N. Task description`)
3. **Actions**: 
   - Stages all new and modified files (`git add -A`)
   - Creates commit with format: `Complete Task N: Task description`
   - Pushes changes to remote repository

### Requirements Addressed

- **11.1**: Automatically stage all new and modified files using git add
- **11.2**: Create commit messages with task number and description  
- **11.3**: Follow commit message format "Complete Task X: [task description]"
- **11.4**: Automatically push changes to remote repository
- **11.5**: Handle authentication using existing git credentials
- **11.6**: Log errors and notify user without interrupting workflow
- **11.7**: Create separate commits for each completed task

### Usage

The hook runs automatically when tasks are completed. You can also run the script manually:

```bash
# Run normally
python .kiro/hooks/scripts/git-automation.py --task-file .kiro/specs/personalized-learning-path-generator/tasks.md

# Dry run (show what would be done)
python .kiro/hooks/scripts/git-automation.py --task-file .kiro/specs/personalized-learning-path-generator/tasks.md --dry-run

# With custom log file
python .kiro/hooks/scripts/git-automation.py --task-file .kiro/specs/personalized-learning-path-generator/tasks.md --log-file .kiro/hooks/logs/git-automation.log
```

### Error Handling

- Git authentication errors are logged but don't interrupt the workflow
- Network issues during push are logged as warnings
- Failed operations are retried according to hook configuration
- All operations are logged to `logs/git-automation.log`

### Security

- Uses existing git credentials (no additional authentication required)
- Only processes top-level task completions (ignores subtasks)
- Validates git repository status before making changes
- Logs all operations for audit trail