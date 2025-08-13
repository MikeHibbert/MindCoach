import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const RegisterForm = () => {
  const [userId, setUserId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const { register, loading, error } = useAuth();
  const navigate = useNavigate();

  const validateForm = () => {
    const errors = {};

    // User ID validation
    if (!userId) {
      errors.userId = 'User ID is required';
    } else if (userId.length < 3) {
      errors.userId = 'User ID must be at least 3 characters';
    } else if (userId.length > 50) {
      errors.userId = 'User ID must be less than 50 characters';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(userId)) {
      errors.userId = 'User ID can only contain letters, numbers, hyphens, and underscores';
    }

    // Email validation
    if (!email) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else {
      const hasUpper = /[A-Z]/.test(password);
      const hasLower = /[a-z]/.test(password);
      const hasDigit = /\d/.test(password);
      const hasSpecial = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password);

      if (!hasUpper || !hasLower || !hasDigit || !hasSpecial) {
        errors.password = 'Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character';
      }
    }

    // Confirm password validation
    if (!confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const result = await register(userId, email, password);
    
    if (result.success) {
      // Redirect to subjects page after successful registration
      navigate('/subjects');
    }
  };

  const handleInputChange = (field, value) => {
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }

    switch (field) {
      case 'userId':
        setUserId(value);
        break;
      case 'email':
        setEmail(value);
        break;
      case 'password':
        setPassword(value);
        break;
      case 'confirmPassword':
        setConfirmPassword(value);
        break;
      default:
        break;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
            <span className="text-2xl">🧠</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your MindCoach account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{' '}
            <Link
              to="/login"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              sign in to your existing account
            </Link>
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="userId" className="block text-sm font-medium text-gray-700">
                User ID
              </label>
              <input
                id="userId"
                name="userId"
                type="text"
                required
                value={userId}
                onChange={(e) => handleInputChange('userId', e.target.value)}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  validationErrors.userId ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="Choose a unique user ID"
                disabled={loading}
              />
              {validationErrors.userId && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.userId}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                3-50 characters, letters, numbers, hyphens, and underscores only
              </p>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border ${
                  validationErrors.email ? 'border-red-300' : 'border-gray-300'
                } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                placeholder="Enter your email"
                disabled={loading}
              />
              {validationErrors.email && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.email}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={`appearance-none relative block w-full px-3 py-2 pr-10 border ${
                    validationErrors.password ? 'border-red-300' : 'border-gray-300'
                  } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                  placeholder="Create a strong password"
                  disabled={loading}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={loading}
                >
                  {showPassword ? (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {validationErrors.password && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.password}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                At least 8 characters with uppercase, lowercase, number, and special character
              </p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className={`appearance-none relative block w-full px-3 py-2 pr-10 border ${
                    validationErrors.confirmPassword ? 'border-red-300' : 'border-gray-300'
                  } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                  placeholder="Confirm your password"
                  disabled={loading}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  disabled={loading}
                >
                  {showConfirmPassword ? (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {validationErrors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.confirmPassword}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading || !userId || !email || !password || !confirmPassword}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                loading || !userId || !email || !password || !confirmPassword
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating account...
                </div>
              ) : (
                'Create account'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterForm;