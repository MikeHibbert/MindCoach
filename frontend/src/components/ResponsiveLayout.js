import React from 'react';

const ResponsiveLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop Layout */}
      <div className="hidden desktop:flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-lg">
          <div className="p-6">
            <h1 className="text-xl font-bold text-gray-800">Learning Path</h1>
          </div>
          <div className="px-6 py-4">
            <ul className="space-y-2">
              <li>
                <a href="/" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
                  Subjects
                </a>
              </li>
            </ul>
          </div>
        </nav>
        
        {/* Main Content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
      
      {/* Tablet Layout */}
      <div className="hidden tablet:block desktop:hidden">
        <header className="bg-white shadow-sm p-4">
          <h1 className="text-xl font-bold text-gray-800">Learning Path</h1>
        </header>
        <main className="p-6">
          {children}
        </main>
      </div>
      
      {/* Mobile Layout */}
      <div className="block tablet:hidden">
        <header className="bg-white shadow-sm p-4">
          <h1 className="text-lg font-bold text-gray-800">Learning Path</h1>
        </header>
        <main className="p-4">
          {children}
        </main>
      </div>
    </div>
  );
};

export default ResponsiveLayout;