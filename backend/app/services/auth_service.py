"""
Authentication service for user login, registration, and token management
"""
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from app import db
from app.models.user import User
from app.services.user_service import UserService
from datetime import datetime, timedelta
import re

class AuthService:
    """Service for handling authentication operations"""
    
    # Token blacklist (in production, use Redis or database)
    blacklisted_tokens = set()
    
    @staticmethod
    def register_user(user_id, email, password):
        """
        Register a new user with authentication credentials
        
        Args:
            user_id (str): Unique user identifier
            email (str): User email address
            password (str): Plain text password
            
        Returns:
            tuple: (User object, access_token, refresh_token) or (None, None, None) if failed
        """
        try:
            # Validate input
            validation_error = AuthService._validate_registration_data(user_id, email, password)
            if validation_error:
                raise ValueError(validation_error)
            
            # Check if user already exists
            existing_user = UserService.get_user_by_id(user_id)
            if existing_user:
                raise ValueError("User ID already exists")
            
            existing_email = UserService.get_user_by_email(email)
            if existing_email:
                raise ValueError("Email already registered")
            
            # Create user
            user = User(user_id=user_id, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Create user directory structure
            from app.services.file_service import FileService
            FileService.ensure_user_directory(user_id)
            
            # Generate tokens
            access_token = create_access_token(identity=user_id)
            refresh_token = create_refresh_token(identity=user_id)
            
            current_app.logger.info(f'User registered successfully: {user_id}')
            
            return user, access_token, refresh_token
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration failed for {user_id}: {str(e)}')
            raise
    
    @staticmethod
    def login_user(email, password):
        """
        Authenticate user and generate tokens
        
        Args:
            email (str): User email
            password (str): Plain text password
            
        Returns:
            tuple: (User object, access_token, refresh_token) or (None, None, None) if failed
        """
        try:
            # Find user by email
            user = UserService.get_user_by_email(email)
            if not user:
                raise ValueError("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                raise ValueError("Account is deactivated")
            
            # Verify password
            if not user.check_password(password):
                raise ValueError("Invalid email or password")
            
            # Update last login
            user.update_last_login()
            
            # Generate tokens
            access_token = create_access_token(identity=user.user_id)
            refresh_token = create_refresh_token(identity=user.user_id)
            
            current_app.logger.info(f'User logged in successfully: {user.user_id}')
            
            return user, access_token, refresh_token
            
        except Exception as e:
            current_app.logger.error(f'Login failed for {email}: {str(e)}')
            raise
    
    @staticmethod
    def refresh_token():
        """
        Generate new access token using refresh token
        
        Returns:
            str: New access token
        """
        try:
            current_user_id = get_jwt_identity()
            
            # Verify user still exists and is active
            user = UserService.get_user_by_id(current_user_id)
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")
            
            # Generate new access token
            access_token = create_access_token(identity=current_user_id)
            
            return access_token
            
        except Exception as e:
            current_app.logger.error(f'Token refresh failed: {str(e)}')
            raise
    
    @staticmethod
    def logout_user():
        """
        Logout user by blacklisting current token
        
        Returns:
            bool: True if successful
        """
        try:
            jti = get_jwt()['jti']
            AuthService.blacklisted_tokens.add(jti)
            
            current_user_id = get_jwt_identity()
            current_app.logger.info(f'User logged out successfully: {current_user_id}')
            
            return True
            
        except Exception as e:
            current_app.logger.error(f'Logout failed: {str(e)}')
            raise
    
    @staticmethod
    def is_token_blacklisted(jti):
        """
        Check if token is blacklisted
        
        Args:
            jti (str): JWT ID
            
        Returns:
            bool: True if blacklisted
        """
        return jti in AuthService.blacklisted_tokens
    
    @staticmethod
    def get_current_user():
        """
        Get current authenticated user
        
        Returns:
            User: Current user object or None
        """
        try:
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return None
            
            return UserService.get_user_by_id(current_user_id)
            
        except Exception as e:
            current_app.logger.error(f'Failed to get current user: {str(e)}')
            return None
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """
        Change user password
        
        Args:
            user_id (str): User ID
            old_password (str): Current password
            new_password (str): New password
            
        Returns:
            bool: True if successful
        """
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Verify old password
            if not user.check_password(old_password):
                raise ValueError("Current password is incorrect")
            
            # Validate new password
            if not AuthService._validate_password(new_password):
                raise ValueError("New password does not meet requirements")
            
            # Set new password
            user.set_password(new_password)
            db.session.commit()
            
            current_app.logger.info(f'Password changed successfully for user: {user_id}')
            
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Password change failed for {user_id}: {str(e)}')
            raise
    
    @staticmethod
    def _validate_registration_data(user_id, email, password):
        """
        Validate registration data
        
        Args:
            user_id (str): User ID
            email (str): Email address
            password (str): Password
            
        Returns:
            str: Error message or None if valid
        """
        # Validate user_id
        if not user_id or len(user_id) < 3 or len(user_id) > 50:
            return "User ID must be between 3 and 50 characters"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            return "User ID can only contain letters, numbers, hyphens, and underscores"
        
        # Validate email
        if not email or len(email) > 100:
            return "Email is required and must be less than 100 characters"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return "Invalid email format"
        
        # Validate password
        if not AuthService._validate_password(password):
            return "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character"
        
        return None
    
    @staticmethod
    def _validate_password(password):
        """
        Validate password strength
        
        Args:
            password (str): Password to validate
            
        Returns:
            bool: True if valid
        """
        if not password or len(password) < 8:
            return False
        
        # Check for at least one uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        return has_upper and has_lower and has_digit and has_special