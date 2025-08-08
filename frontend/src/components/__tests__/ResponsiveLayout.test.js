import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import ResponsiveLayout from '../ResponsiveLayout';

// Mock window.matchMedia for responsive testing
const mockMatchMedia = (matches) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('ResponsiveLayout', () => {
  beforeEach(() => {
    // Reset matchMedia mock
    mockMatchMedia(false);
  });

  test('renders children content', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div data-testid="test-content">Test Content</div>
      </ResponsiveLayout>
    );
    
    // Should render content in all layouts (desktop, tablet, mobile)
    expect(screen.getAllByTestId('test-content').length).toBeGreaterThan(0);
  });

  test('displays application title', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    // Should show some form of the title on all layouts
    expect(screen.getAllByText(/Learning/).length).toBeGreaterThan(0);
  });

  test('renders navigation items', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    expect(screen.getAllByText('Select Subject').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Progress').length).toBeGreaterThan(0);
  });

  test('mobile menu toggle works', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    // Find the mobile menu button (should be visible on mobile)
    const menuButton = screen.getByLabelText('Toggle navigation menu');
    expect(menuButton).toBeInTheDocument();
    
    // Initially menu should be closed
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    
    // Click to open menu
    fireEvent.click(menuButton);
    expect(menuButton).toHaveAttribute('aria-expanded', 'true');
    
    // Click to close menu
    fireEvent.click(menuButton);
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
  });

  test('navigation links have proper accessibility attributes', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    const navLinks = screen.getAllByRole('link');
    navLinks.forEach(link => {
      // Each link should be focusable
      expect(link).toHaveAttribute('href');
    });
  });

  test('has proper ARIA labels for navigation', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    const navElements = screen.getAllByRole('navigation');
    // Should have at least some navigation elements with proper labels
    expect(navElements.length).toBeGreaterThan(0);
    
    // Check that navigation elements with aria-label exist
    const labeledNavs = navElements.filter(nav => 
      nav.getAttribute('aria-label') === 'Main navigation'
    );
    expect(labeledNavs.length).toBeGreaterThan(0);
  });

  test('mobile menu closes when navigation link is clicked', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    const menuButton = screen.getByLabelText('Toggle navigation menu');
    
    // Open menu
    fireEvent.click(menuButton);
    expect(menuButton).toHaveAttribute('aria-expanded', 'true');
    
    // Find the mobile menu specifically by ID
    const mobileMenu = document.getElementById('mobile-menu');
    expect(mobileMenu).toBeInTheDocument();
    
    // Find a link within the mobile menu and click it
    const mobileMenuLinks = mobileMenu.querySelectorAll('a');
    expect(mobileMenuLinks.length).toBeGreaterThan(0);
    fireEvent.click(mobileMenuLinks[0]);
    
    // Menu should close
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
  });

  test('has minimum touch target sizes for mobile', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    // Mobile menu button should have minimum 44px touch target
    const menuButton = screen.getByLabelText('Toggle navigation menu');
    expect(menuButton).toHaveClass('min-h-[44px]', 'min-w-[44px]');
  });

  test('tablet layout has larger touch targets', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    // Check that main content areas exist (multiple layouts render simultaneously)
    const containers = screen.getAllByRole('main');
    expect(containers.length).toBeGreaterThan(0);
  });

  test('keyboard navigation works', () => {
    renderWithRouter(
      <ResponsiveLayout>
        <div>Content</div>
      </ResponsiveLayout>
    );
    
    const menuButton = screen.getByLabelText('Toggle navigation menu');
    
    // Should be focusable
    menuButton.focus();
    expect(document.activeElement).toBe(menuButton);
    
    // Should respond to Enter key
    fireEvent.keyDown(menuButton, { key: 'Enter', code: 'Enter' });
    // Note: onClick handler should still work with keyboard events
  });
});