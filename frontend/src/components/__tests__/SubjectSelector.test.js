import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SubjectSelector from '../SubjectSelector';

// Mock fetch
global.fetch = jest.fn();

const mockSubjects = [
  {
    id: 'python',
    name: 'Python Programming',
    description: 'Learn Python from basics to advanced concepts',
    pricing: { monthly: 29.99, yearly: 299.99 },
    available: true,
    locked: false
  },
  {
    id: 'javascript',
    name: 'JavaScript Development',
    description: 'Master JavaScript for web development',
    pricing: { monthly: 29.99, yearly: 299.99 },
    available: true,
    locked: true
  },
  {
    id: 'react',
    name: 'React Framework',
    description: 'Build modern web applications with React',
    pricing: { monthly: 34.99, yearly: 349.99 },
    available: true,
    locked: false
  }
];

describe('SubjectSelector', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<SubjectSelector userId="test-user" />);
    
    expect(screen.getByText('Loading subjects...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { hidden: true })).toBeInTheDocument();
  });

  it('renders subjects after successful fetch', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /python programming/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /javascript development/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /react framework/i })).toBeInTheDocument();
    });
  });

  it('shows error state when fetch fails', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading subjects')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('displays locked subjects with lock indicator', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      const lockedSubject = screen.getByText('JavaScript Development').closest('[role="button"]');
      expect(lockedSubject).toHaveAttribute('aria-disabled', 'true');
      expect(screen.getByText('Subscription Required')).toBeInTheDocument();
    });
  });

  it('allows selection of unlocked subjects', async () => {
    const mockOnSelect = jest.fn();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });
    
    // Mock the subject selection API call
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: 'Successfully selected Python Programming',
        subject: { id: 'python', name: 'Python Programming', selected_at: 'now' }
      })
    });

    render(<SubjectSelector userId="test-user" onSubjectSelect={mockOnSelect} />);

    await waitFor(() => {
      const pythonSubject = screen.getByRole('button', { name: /python programming/i });
      fireEvent.click(pythonSubject);
    });

    await waitFor(() => {
      expect(mockOnSelect).toHaveBeenCalledWith(mockSubjects[0]);
      expect(screen.getByText('Python Programming Selected')).toBeInTheDocument();
    });
  });

  it('prevents selection of locked subjects', async () => {
    const mockOnSelect = jest.fn();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector userId="test-user" onSubjectSelect={mockOnSelect} />);

    await waitFor(() => {
      const lockedSubject = screen.getByText('JavaScript Development').closest('[role="button"]');
      fireEvent.click(lockedSubject);
    });

    expect(mockOnSelect).not.toHaveBeenCalled();
  });

  it('supports keyboard navigation', async () => {
    const mockOnSelect = jest.fn();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });
    
    // Mock the subject selection API call
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: 'Successfully selected Python Programming',
        subject: { id: 'python', name: 'Python Programming', selected_at: 'now' }
      })
    });

    render(<SubjectSelector userId="test-user" onSubjectSelect={mockOnSelect} />);

    await waitFor(() => {
      const pythonSubject = screen.getByRole('button', { name: /python programming/i });
      pythonSubject.focus();
      fireEvent.keyDown(pythonSubject, { key: 'Enter' });
    });

    await waitFor(() => {
      expect(mockOnSelect).toHaveBeenCalledWith(mockSubjects[0]);
    });
  });

  it('shows dropdown on mobile view', async () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      expect(screen.getByLabelText('Select a programming subject')).toBeInTheDocument();
    });
  });

  it('toggles between grid and dropdown view on desktop', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      const gridButton = screen.getByRole('button', { name: /grid/i });
      const listButton = screen.getByRole('button', { name: /list/i });
      
      expect(gridButton).toHaveAttribute('aria-pressed', 'true');
      expect(listButton).toHaveAttribute('aria-pressed', 'false');
      
      fireEvent.click(listButton);
      
      expect(gridButton).toHaveAttribute('aria-pressed', 'false');
      expect(listButton).toHaveAttribute('aria-pressed', 'true');
    });
  });

  it('handles dropdown selection', async () => {
    const mockOnSelect = jest.fn();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });
    
    // Mock the subject selection API call
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: 'Successfully selected Python Programming',
        subject: { id: 'python', name: 'Python Programming', selected_at: 'now' }
      })
    });

    render(<SubjectSelector userId="test-user" onSubjectSelect={mockOnSelect} />);

    await waitFor(() => {
      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);
    });

    const dropdown = document.getElementById('desktop-subject-select');
    fireEvent.change(dropdown, { target: { value: 'python' } });

    await waitFor(() => {
      expect(mockOnSelect).toHaveBeenCalledWith(mockSubjects[0]);
    });
  });

  it('shows empty state when no subjects available', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: [] })
    });

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      expect(screen.getByText('No subjects available')).toBeInTheDocument();
      expect(screen.getByText('There are currently no programming subjects available for selection.')).toBeInTheDocument();
    });
  });

  it('fetches subjects without user_id when not provided', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/subjects');
    });
  });

  it('fetches subjects with user_id when provided', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector userId="test-user-123" />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/subjects?user_id=test-user-123');
    });
  });

  it('retries fetch on error button click', async () => {
    fetch
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subjects: mockSubjects })
      });

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Try again');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /python programming/i })).toBeInTheDocument();
    });

    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it('displays pricing information', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      const pricingElements = screen.getAllByText(/From \$\d+\.\d+\/month/);
      expect(pricingElements.length).toBeGreaterThan(0);
      expect(screen.getByText(/From \$34\.99\/month/)).toBeInTheDocument();
    });
  });

  it('shows available status for unlocked subjects', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ subjects: mockSubjects })
    });

    render(<SubjectSelector userId="test-user" />);

    await waitFor(() => {
      const availableElements = screen.getAllByText('Available');
      expect(availableElements).toHaveLength(2); // Python and React are unlocked
    });
  });
});