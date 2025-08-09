import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { focusManagement, announceToScreenReader, keyboardNavigation } from '../utils/accessibility';

const ResponsiveLayout = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [focusedNavIndex, setFocusedNavIndex] = useState(-1);
  const location = useLocation();
  const mobileMenuRef = useRef(null);
  const skipLinkRef = useRef(null);
  const mainContentRef = useRef(null);
  const navigationRefs = useRef([]);

  const navigationItems = [
    { 
      path: '/', 
      label: 'Select Subject', 
      icon: '📚',
      ariaLabel: 'Navigate to subject selection page'
    },
    { 
      path: '/dashboard', 
      label: 'Dashboard', 
      icon: '📊',
      ariaLabel: 'Navigate to dashboard page'
    },
    { 
      path: '/progress', 
      label: 'Progress', 
      icon: '📈',
      ariaLabel: 'Navigate to progress tracking page'
    },
  ];

  const isActivePath = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  // Handle mobile menu toggle with accessibility
  const toggleMobileMenu = () => {
    const newState = !mobileMenuOpen;
    setMobileMenuOpen(newState);
    
    // Announce state change to screen readers
    announceToScreenReader(
      newState ? 'Navigation menu opened' : 'Navigation menu closed'
    );
    
    // Focus management
    if (newState && mobileMenuRef.current) {
      setTimeout(() => {
        focusManagement.focusFirstElement(mobileMenuRef.current);
      }, 100);
    }
  };

  // Handle keyboard navigation in mobile menu
  const handleMobileMenuKeyDown = (e) => {
    if (!mobileMenuOpen) return;
    
    if (e.key === 'Escape') {
      setMobileMenuOpen(false);
      announceToScreenReader('Navigation menu closed');
      // Focus back to menu button
      document.querySelector('[aria-controls="mobile-menu"]')?.focus();
    }
  };

  // Handle keyboard navigation for navigation items
  const handleNavKeyDown = (e, index) => {
    keyboardNavigation.handleArrowKeys(
      e, 
      navigationItems, 
      index, 
      (newIndex) => {
        setFocusedNavIndex(newIndex);
        navigationRefs.current[newIndex]?.focus();
      }
    );
  };

  // Skip to main content functionality
  const skipToMainContent = (e) => {
    e.preventDefault();
    if (mainContentRef.current) {
      mainContentRef.current.focus();
      mainContentRef.current.scrollIntoView({ behavior: 'smooth' });
      announceToScreenReader('Skipped to main content');
    }
  };

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Set up focus trap for mobile menu
  useEffect(() => {
    if (mobileMenuOpen && mobileMenuRef.current) {
      const cleanup = focusManagement.trapFocus(mobileMenuRef.current);
      return cleanup;
    }
  }, [mobileMenuOpen]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Skip to main content link */}
      <a
        ref={skipLinkRef}
        href="#main-content"
        onClick={skipToMainContent}
        className="skip-link focus-visible-only"
      >
        Skip to main content
      </a>

      {/* Desktop Layout - Sidebar + Main Content */}
      <div className="hidden desktop:flex">
        {/* Desktop Sidebar */}
        <nav 
          className="w-64 bg-white shadow-lg border-r-2 border-gray-200 flex flex-col"
          role="navigation"
          aria-label="Main navigation"
        >
          <div className="p-6 border-b-2 border-gray-200">
            <h1 className="text-xl font-bold text-gray-900">
              Personalized Learning
            </h1>
            <p className="text-sm text-gray-700 mt-1">Path Generator</p>
          </div>
          
          <div className="flex-1 px-4 py-6">
            <ul className="space-y-2">
              {navigationItems.map((item, index) => (
                <li key={item.path}>
                  <Link
                    ref={(el) => navigationRefs.current[index] = el}
                    to={item.path}
                    className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2 touch-target ${
                      isActivePath(item.path)
                        ? 'bg-blue-100 text-blue-900 border-r-3 border-blue-700'
                        : 'text-gray-800 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                    aria-current={isActivePath(item.path) ? 'page' : undefined}
                    aria-label={item.ariaLabel}
                    onKeyDown={(e) => handleNavKeyDown(e, index)}
                  >
                    <span className="mr-3 text-lg" role="img" aria-hidden="true">
                      {item.icon}
                    </span>
                    {item.label}
                    {isActivePath(item.path) && (
                      <span className="sr-only">(current page)</span>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              © 2024 Learning Platform
            </div>
          </div>
        </nav>
        
        {/* Desktop Main Content */}
        <main 
          id="main-content"
          ref={mainContentRef}
          className="flex-1 overflow-auto"
          role="main"
          aria-label="Main content"
          tabIndex="-1"
        >
          <div className="p-8 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      {/* Tablet Layout - Stacked with larger touch targets */}
      <div className="hidden tablet:block desktop:hidden">
        <header className="bg-white shadow-sm border-b-2 border-gray-200 sticky top-0 z-10">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Personalized Learning
                </h1>
                <p className="text-sm text-gray-700">Path Generator</p>
              </div>
              
              {/* Tablet Navigation Menu */}
              <nav 
                className="flex space-x-1" 
                role="navigation" 
                aria-label="Main navigation"
              >
                {navigationItems.map((item, index) => (
                  <Link
                    key={item.path}
                    ref={(el) => navigationRefs.current[index] = el}
                    to={item.path}
                    className={`flex flex-col items-center px-4 py-3 touch-target-large text-xs font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2 ${
                      isActivePath(item.path)
                        ? 'bg-blue-100 text-blue-900'
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                    aria-current={isActivePath(item.path) ? 'page' : undefined}
                    aria-label={item.ariaLabel}
                    onKeyDown={(e) => handleNavKeyDown(e, index)}
                  >
                    <span className="text-lg mb-1" role="img" aria-hidden="true">
                      {item.icon}
                    </span>
                    <span className="text-center leading-tight">
                      {item.label}
                    </span>
                    {isActivePath(item.path) && (
                      <span className="sr-only">(current page)</span>
                    )}
                  </Link>
                ))}
              </nav>
            </div>
          </div>
        </header>
        
        <main 
          id="main-content"
          ref={mainContentRef}
          className="p-6"
          role="main"
          aria-label="Main content"
          tabIndex="-1"
        >
          <div className="max-w-4xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      {/* Mobile Layout - Single column with hamburger menu */}
      <div className="block tablet:hidden">
        <header className="bg-white shadow-sm border-b-2 border-gray-200 sticky top-0 z-20">
          <div className="px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-lg font-bold text-gray-900">
                  Learning Path
                </h1>
              </div>
              
              {/* Mobile Menu Button */}
              <button
                onClick={toggleMobileMenu}
                className="p-2 rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2 touch-target"
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-menu"
                aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  {mobileMenuOpen ? (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  ) : (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  )}
                </svg>
              </button>
            </div>
            
            {/* Mobile Navigation Menu */}
            {mobileMenuOpen && (
              <nav
                id="mobile-menu"
                ref={mobileMenuRef}
                className="mt-4 pb-3 border-t-2 border-gray-200 pt-4"
                role="navigation"
                aria-label="Main navigation"
                onKeyDown={handleMobileMenuKeyDown}
              >
                <ul className="space-y-2">
                  {navigationItems.map((item, index) => (
                    <li key={item.path}>
                      <Link
                        ref={(el) => navigationRefs.current[index] = el}
                        to={item.path}
                        onClick={() => {
                          setMobileMenuOpen(false);
                          announceToScreenReader(`Navigated to ${item.label}`);
                        }}
                        className={`flex items-center px-4 py-4 text-base font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-3 focus:ring-blue-500 focus:ring-offset-2 touch-target-large ${
                          isActivePath(item.path)
                            ? 'bg-blue-100 text-blue-900'
                            : 'text-gray-800 hover:bg-gray-100 hover:text-gray-900'
                        }`}
                        aria-current={isActivePath(item.path) ? 'page' : undefined}
                        aria-label={item.ariaLabel}
                        onKeyDown={(e) => handleNavKeyDown(e, index)}
                      >
                        <span className="mr-4 text-xl" role="img" aria-hidden="true">
                          {item.icon}
                        </span>
                        {item.label}
                        {isActivePath(item.path) && (
                          <span className="sr-only">(current page)</span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            )}
          </div>
        </header>
        
        <main 
          id="main-content"
          ref={mainContentRef}
          className="p-4"
          role="main"
          aria-label="Main content"
          tabIndex="-1"
        >
          <div className="max-w-sm mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default ResponsiveLayout;