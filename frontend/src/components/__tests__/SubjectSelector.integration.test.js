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
    available: true
  },
  {
    id: 'javascript',
    name: 'JavaScript Development',
    description: 'Master JavaScript for web development',
    available: true
  }
];

describe('SubjectSelector Integration Tests', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Subject Selection Persistence', () => {
    it('persists subject selection to backend when user selects an unlocked subject', async () => {
      const mockOnSelect = jest.fn();
      
      // Mock subjects fetch
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subjects: mockSubjects })
      });

      // Mock subject selection API
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'Successfully selected Python Programming',
          subject: {
            id: 'python',
            name: 'Python Programming',
            selected_at: '2024-01-15T10:30:00Z'
          }
        })
      });

      render(<SubjectSelector userId="test-user-123" onSubjectSelect={mockOnSelect} />);

      // Wait for subjects to load
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /python programming/i })).toBeInTheDocument();
      });

      // Select Python subject
      const pythonSubject = screen.getByRole('button', { name: /python programming/i });
      fireEvent.click(pythonSubject);

      // Verify API calls
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(2);
        expect(fetch).toHaveBeenNthCalledWith(1, '/api/subjects?user_id=test-user-123');
        expect(fetch).toHaveBeenNthCalledWith(2, '/api/users/test-user-123/subjects/python/select', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
      });

      // Verify callback was called and success state
      await waitFor(() => {
        expect(mockOnSelect).toHaveBeenCalledWith(mockSubjects[0]);
        expect(screen.getByText('Python Programming Selected')).toBeInTheDocument();
      });
    });



    it('handles API errors during subject selection', async () => {
      const mockOnSelect = jest.fn();
      
      // Mock subjects fetch
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subjects: mockSubjects })
      });

      // Mock subject selection API with server error
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          error: {
            code: 'INTERNAL_ERROR',
            message: 'Failed to select subject'
          }
        })
      });

      render(<SubjectSelector userId="test-user-123" onSubjectSelect={mockOnSelect} />);

      // Wait for subjects to load
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /python programming/i })).toBeInTheDocument();
      });

      // Select Python subject
      const pythonSubject = screen.getByRole('button', { name: /python programming/i });
      fireEvent.click(pythonSubject);

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/Failed to select subject/)).toBeInTheDocument();
      });

      // Verify callback was not called due to error
      expect(mockOnSelect).not.toHaveBeenCalled();
    });

    it('works without userId (no persistence)', async () => {
      const mockOnSelect = jest.fn();
      
      // Mock subjects fetch
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subjects: mockSubjects })
      });

      render(<SubjectSelector onSubjectSelect={mockOnSelect} />);

      // Wait for subjects to load
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /python programming/i })).toBeInTheDocument();
      });

      // Select Python subject
      const pythonSubject = screen.getByRole('button', { name: /python programming/i });
      fireEvent.click(pythonSubject);

      // Verify only subjects fetch was called (no selection persistence)
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(fetch).toHaveBeenCalledWith('/api/subjects');
      });

      // Verify callback was still called
      expect(mockOnSelect).toHaveBeenCalledWith(mockSubjects[0]);
      
      // Verify success state
      expect(screen.getByText('Python Programming Selected')).toBeInTheDocument();
    });
  });


        const availableElements = screen.getAllByText('Available');
        expect(availableElements).toHaveLength(2); // Python and React

        // Check locked subject shows subscription required
        expect(screen.getByText('Subscription Required')).toBeInTheDocument();

        // Check lock icon is present for locked subject
        const jsSubject = screen.getByRole('button', { name: /javascript development/i });
        expect(jsSubject).toHaveAttribute('aria-disabled', 'true');
      });
    });

    it('refreshes subscription status when subjects are refetched', async () => {
      // Initial fetch fails
      fetch.mockRejectedValueOnce(new Error('Network error'));

      // Second fetch with unlocked subject (after retry)
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          subjects: [
            { ...mockSubjects[0], locked: false } // Now unlocked
          ]
        })
      });

      render(<SubjectSelector userId="test-user-123" />);

      // Initially shows error
      await waitFor(() => {
        expect(screen.getByText('Error loading subjects')).toBeInTheDocument();
      });

      // Simulate retry (e.g., after network is restored)
      const retryButton = screen.getByText('Try again');
      fireEvent.click(retryButton);

      // Now shows subjects
      await waitFor(() => {
        expect(screen.getByText('Available')).toBeInTheDocument();
        expect(screen.queryByText('Error loading subjects')).not.toBeInTheDocument();
      });
    });
  });

  describe('Complete Subject Selection Flow', () => {
    it('completes full subject selection workflow', async () => {
      const mockOnSelect = jest.fn();
      
      // Mock subjects fetch
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subjects: mockSubjects })
      });

      // Mock successful subject selection
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'Successfully selected Python Programming',
          subject: {
            id: 'python',
            name: 'Python Programming',
            selected_at: '2024-01-15T10:30:00Z'
          }
        })
      });

      render(<SubjectSelector userId="test-user-123" onSubjectSelect={mockOnSelect} />);

      // 1. Wait for subjects to load
      await waitFor(() => {
        expect(screen.getByText('Select a Subject')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /python programming/i })).toBeInTheDocument();
      });

      // 2. Verify initial state
      expect(screen.getByText('2 subjects available')).toBeInTheDocument();
      expect(screen.queryByText('Python Programming Selected')).not.toBeInTheDocument();

      // 3. Select an available subject
      const pythonSubject = screen.getByRole('button', { name: /python programming/i });
      fireEvent.click(pythonSubject);

      // 4. Verify selection was processed
      await waitFor(() => {
        expect(screen.getByText('Python Programming Selected')).toBeInTheDocument();
        expect(screen.getByText('You can now proceed to take the knowledge assessment survey.')).toBeInTheDocument();
      });

      // 5. Verify all API calls were made correctly
      expect(fetch).toHaveBeenCalledTimes(2);
      expect(fetch).toHaveBeenNthCalledWith(1, '/api/subjects?user_id=test-user-123');
      expect(fetch).toHaveBeenNthCalledWith(2, '/api/users/test-user-123/subjects/python/select', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // 6. Verify callback was called with correct data
      await waitFor(() => {
        expect(mockOnSelect).toHaveBeenCalledWith(mockSubjects[0]);
      });
    });
  });
});