#!/usr/bin/env python3
"""
Git Error Handler for Automated Git Operations

This module provides comprehensive error handling and logging for git operations
as required by the automated git workflow system.

Requirements addressed:
- 11.5: Handle git authentication and network issues
- 11.6: Create logging system for git operations and error tracking
"""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple


class GitErrorType(Enum):
    """Enumeration of different types of git errors"""
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    REPOSITORY = "repository"
    PERMISSION = "permission"
    MERGE_CONFLICT = "merge_conflict"
    NO_CHANGES = "no_changes"
    UNKNOWN = "unknown"


class GitErrorHandler:
    """
    Comprehensive error handler for git operations
    
    Provides categorization, logging, and recovery suggestions for git errors
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_patterns = self._initialize_error_patterns()
    
    def _initialize_error_patterns(self) -> Dict[GitErrorType, List[str]]:
        """
        Initialize regex patterns for different types of git errors
        
        Returns:
            Dict mapping error types to regex patterns
        """
        return {
            GitErrorType.AUTHENTICATION: [
                r"authentication failed",
                r"permission denied \(publickey\)",
                r"could not read from remote repository",
                r"fatal: unable to access.*401",
                r"remote: invalid username or password",
                r"fatal: authentication failed"
            ],
            GitErrorType.NETWORK: [
                r"network is unreachable",
                r"connection timed out",
                r"could not resolve host",
                r"failed to connect to",
                r"operation timed out",
                r"temporary failure in name resolution",
                r"fatal: unable to access.*timeout"
            ],
            GitErrorType.REPOSITORY: [
                r"not a git repository",
                r"fatal: not a git repository",
                r"no such remote",
                r"remote origin does not exist",
                r"fatal: repository.*does not exist"
            ],
            GitErrorType.PERMISSION: [
                r"permission denied",
                r"access denied",
                r"insufficient permission",
                r"fatal: unable to create.*permission denied"
            ],
            GitErrorType.MERGE_CONFLICT: [
                r"merge conflict",
                r"automatic merge failed",
                r"conflict.*merge",
                r"unmerged paths"
            ],
            GitErrorType.NO_CHANGES: [
                r"nothing to commit",
                r"no changes added to commit",
                r"working tree clean",
                r"up to date"
            ]
        }
    
    def categorize_error(self, error_message: str) -> GitErrorType:
        """
        Categorize a git error based on its message
        
        Args:
            error_message: The error message from git command
            
        Returns:
            GitErrorType: The category of the error
        """
        error_lower = error_message.lower()
        
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_lower):
                    return error_type
        
        return GitErrorType.UNKNOWN
    
    def get_error_description(self, error_type: GitErrorType) -> str:
        """
        Get a human-readable description of the error type
        
        Args:
            error_type: The type of error
            
        Returns:
            str: Description of the error
        """
        descriptions = {
            GitErrorType.AUTHENTICATION: "Git authentication failed - check credentials",
            GitErrorType.NETWORK: "Network connectivity issue - check internet connection",
            GitErrorType.REPOSITORY: "Git repository issue - check repository configuration",
            GitErrorType.PERMISSION: "Permission denied - check file/directory permissions",
            GitErrorType.MERGE_CONFLICT: "Merge conflict detected - manual resolution required",
            GitErrorType.NO_CHANGES: "No changes to commit - this is normal",
            GitErrorType.UNKNOWN: "Unknown git error - check git configuration"
        }
        return descriptions.get(error_type, "Unknown error type")
    
    def get_recovery_suggestions(self, error_type: GitErrorType) -> List[str]:
        """
        Get recovery suggestions for different error types
        
        Args:
            error_type: The type of error
            
        Returns:
            List of recovery suggestions
        """
        suggestions = {
            GitErrorType.AUTHENTICATION: [
                "Check if git credentials are configured: git config user.name and user.email",
                "Verify SSH key is added to git hosting service",
                "Try using HTTPS instead of SSH for remote URL",
                "Check if personal access token is valid (for HTTPS)"
            ],
            GitErrorType.NETWORK: [
                "Check internet connectivity",
                "Try again in a few minutes (temporary network issue)",
                "Check if git hosting service is accessible",
                "Verify firewall/proxy settings"
            ],
            GitErrorType.REPOSITORY: [
                "Verify you're in a git repository directory",
                "Check if remote origin is configured: git remote -v",
                "Verify repository URL is correct",
                "Initialize git repository if needed: git init"
            ],
            GitErrorType.PERMISSION: [
                "Check file and directory permissions",
                "Ensure you have write access to the repository",
                "Run with appropriate user permissions",
                "Check if files are locked by another process"
            ],
            GitErrorType.MERGE_CONFLICT: [
                "Resolve merge conflicts manually",
                "Use git status to see conflicted files",
                "Edit conflicted files and remove conflict markers",
                "Stage resolved files and commit"
            ],
            GitErrorType.NO_CHANGES: [
                "This is normal - no action needed",
                "Task was already committed or no files were modified",
                "Check git status to verify repository state"
            ],
            GitErrorType.UNKNOWN: [
                "Check git configuration: git config --list",
                "Verify git installation is working: git --version",
                "Check git documentation for specific error message",
                "Consider running git fsck to check repository integrity"
            ]
        }
        return suggestions.get(error_type, ["No specific suggestions available"])
    
    def handle_error(self, error_message: str, command: List[str]) -> Tuple[GitErrorType, bool]:
        """
        Handle a git error with comprehensive logging and analysis
        
        Args:
            error_message: The error message from git
            command: The git command that failed
            
        Returns:
            Tuple of (error_type, is_recoverable)
        """
        error_type = self.categorize_error(error_message)
        description = self.get_error_description(error_type)
        suggestions = self.get_recovery_suggestions(error_type)
        
        # Determine if error is recoverable
        recoverable_errors = {
            GitErrorType.NETWORK,
            GitErrorType.NO_CHANGES
        }
        is_recoverable = error_type in recoverable_errors
        
        # Log error details
        self.logger.error(f"Git command failed: {' '.join(command)}")
        self.logger.error(f"Error type: {error_type.value}")
        self.logger.error(f"Description: {description}")
        self.logger.error(f"Error message: {error_message}")
        
        if is_recoverable:
            self.logger.info("This error is potentially recoverable")
        else:
            self.logger.warning("This error may require manual intervention")
        
        # Log recovery suggestions
        self.logger.info("Recovery suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            self.logger.info(f"  {i}. {suggestion}")
        
        return error_type, is_recoverable
    
    def should_retry(self, error_type: GitErrorType, attempt: int, max_attempts: int) -> bool:
        """
        Determine if a git operation should be retried based on error type
        
        Args:
            error_type: The type of error that occurred
            attempt: Current attempt number (1-based)
            max_attempts: Maximum number of attempts allowed
            
        Returns:
            bool: True if operation should be retried
        """
        if attempt >= max_attempts:
            return False
        
        # Only retry for network-related errors
        retryable_errors = {
            GitErrorType.NETWORK
        }
        
        should_retry = error_type in retryable_errors
        
        if should_retry:
            self.logger.info(f"Error type {error_type.value} is retryable. Attempt {attempt}/{max_attempts}")
        else:
            self.logger.info(f"Error type {error_type.value} is not retryable")
        
        return should_retry
    
    def log_success(self, command: List[str], operation: str):
        """
        Log successful git operation
        
        Args:
            command: The git command that succeeded
            operation: Description of the operation
        """
        self.logger.info(f"Git operation successful: {operation}")
        self.logger.debug(f"Command: {' '.join(command)}")
    
    def create_error_report(self, errors: List[Tuple[str, List[str], str]]) -> Dict:
        """
        Create a comprehensive error report for multiple git operations
        
        Args:
            errors: List of (error_message, command, operation) tuples
            
        Returns:
            Dict containing error report
        """
        report = {
            "total_errors": len(errors),
            "error_summary": {},
            "detailed_errors": []
        }
        
        # Categorize all errors
        for error_message, command, operation in errors:
            error_type = self.categorize_error(error_message)
            
            # Update summary
            if error_type.value not in report["error_summary"]:
                report["error_summary"][error_type.value] = 0
            report["error_summary"][error_type.value] += 1
            
            # Add detailed error
            report["detailed_errors"].append({
                "operation": operation,
                "command": command,
                "error_type": error_type.value,
                "error_message": error_message,
                "description": self.get_error_description(error_type),
                "suggestions": self.get_recovery_suggestions(error_type)
            })
        
        return report