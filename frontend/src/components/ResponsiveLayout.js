import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const ResponsiveLayout = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const navigationItems = [
    { path: '/', label: 'Select Subject', icon: '📚' },
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/progress', label: 'Progress', icon: '📈' },
  ];

  const isActivePath = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop Layout - Sidebar + Main Content */}
      <div className="hidden desktop:flex">
        {/* Desktop Sidebar */}
        <nav className="w-64 bg-white shadow-lg border-r border-gray-200 flex flex-col">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-xl font-bold text-gray-800">
              Personalized Learning
            </h1>
            <p className="text-sm text-gray-600 mt-1">Path Generator</p>
          </div>
          
          <div className="flex-1 px-4 py-6">
            <ul className="space-y-2" role="navigation" aria-label="Main navigation">
              {navigationItems.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                      isActivePath(item.path)
                        ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                    aria-current={isActivePath(item.path) ? 'page' : undefined}
                  >
                    <span className="mr-3 text-lg" role="img" aria-hidden="true">
                      {item.icon}
                    </span>
                    {item.label}
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
        <main className="flex-1 overflow-auto">
          <div className="p-8 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      {/* Tablet Layout - Stacked with larger touch targets */}
      <div className="hidden tablet:block desktop:hidden">
        <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-800">
                  Personalized Learning
                </h1>
                <p className="text-sm text-gray-600">Path Generator</p>
              </div>
              
              {/* Tablet Navigation Menu */}
              <nav className="flex space-x-1" role="navigation" aria-label="Main navigation">
                {navigationItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex flex-col items-center px-4 py-3 min-h-[60px] min-w-[80px] text-xs font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                      isActivePath(item.path)
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                    aria-current={isActivePath(item.path) ? 'page' : undefined}
                  >
                    <span className="text-lg mb-1" role="img" aria-hidden="true">
                      {item.icon}
                    </span>
                    <span className="text-center leading-tight">
                      {item.label}
                    </span>
                  </Link>
                ))}
              </nav>
            </div>
          </div>
        </header>
        
        <main className="p-6">
          <div className="max-w-4xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      {/* Mobile Layout - Single column with hamburger menu */}
      <div className="block tablet:hidden">
        <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-20">
          <div className="px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-lg font-bold text-gray-800">
                  Learning Path
                </h1>
              </div>
              
              {/* Mobile Menu Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px] min-w-[44px]"
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-menu"
                aria-label="Toggle navigation menu"
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
                className="mt-4 pb-3 border-t border-gray-200 pt-4"
                role="navigation"
                aria-label="Main navigation"
              >
                <ul className="space-y-2">
                  {navigationItems.map((item) => (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center px-4 py-4 text-base font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[56px] ${
                          isActivePath(item.path)
                            ? 'bg-primary-50 text-primary-700'
                            : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                        }`}
                        aria-current={isActivePath(item.path) ? 'page' : undefined}
                      >
                        <span className="mr-4 text-xl" role="img" aria-hidden="true">
                          {item.icon}
                        </span>
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            )}
          </div>
        </header>
        
        <main className="p-4">
          <div className="max-w-sm mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default ResponsiveLayout;