import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SubjectSelector from '../SubjectSelector';

// Mock fetch
global.fetch = jest.fn();

// This test file demonstrates the complete integration flow
// In a real e2e test, this would connect to an actual backend
describe('SubjectSelector End-to-End Integration', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('completes the full subject selection workflow with backend integration', async () => {
    const mockOnSelect = jest.fn();
    
    // Mock the subjects API response (simulating backend)
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        subjects: [
          {
            id: 'python',
            name: 'Python Programming',
            description: 'Learn Python from basics to advanced concepts',
            pricing: { monthly: 29.99, yearly: 299.99 },
            available: true,
            locked: false // User has subscription
          },
          {
            id: 'javascript',
            name: 'JavaScript Development',
            description: 'Master JavaScript for web development',
            pricing: { monthly: 29.99, yearly: 299.99 },
            available: true,
            locked: true // User doesn't have subscription
          }
        ],
        total_count: 2
      })
    });

    // Mock the subject selection API response (simulating backend)
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

    // 1. Wait for subjects to load from backend
    await waitFor(() => {
      expect(screen.getByText('Select a Subject')).toBeInTheDocument();
      expect(screen.getByText('2 subjects available')).toBeInTheDocument();
    });

    // 2. Verify subscription status is correctly displayed
    expect(screen.getByText('Available')).toBeInTheDocument(); // Python is unlocked
    expect(screen.getByText('Subscription Required')).toBeInTheDocument(); // JavaScript is locked

    // 3. Select an available subject
    const pythonSubject = screen.getByRole('button', { name: /python programming/i });
    fireEvent.click(pythonSubject);

    // 4. Wait for selection to be persisted to backend
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

    // 5. Verify callback was called with correct subject data
    await waitFor(() => {
      expect(mockOnSelect).toHaveBeenCalledWith({
        id: 'python',
        name: 'Python Programming',
        description: 'Learn Python from basics to advanced concepts',
        pricing: { monthly: 29.99, yearly: 299.99 },
        available: true,
        locked: false
      });
    });

    // 6. Verify success state is displayed
    expect(screen.getByText('Python Programming Selected')).toBeInTheDocument();
    expect(screen.getByText('You can now proceed to take the knowledge assessment survey.')).toBeInTheDocument();
  });

  it('handles subscription required error from backend', async () => {
    const mockOnSelect = jest.fn();
    
    // Mock subjects API response with locked subject
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        subjects: [
          {
            id: 'python',
            name: 'Python Programming',
            description: 'Learn Python from basics to advanced concepts',
            pricing: { monthly: 29.99, yearly: 299.99 },
            available: true,
            locked: true // User doesn't have subscription
          }
        ],
        total_count: 1
      })
    });

    render(<SubjectSelector userId="test-user-123" onSubjectSelect={mockOnSelect} />);

    // Wait for subjects to load
    await waitFor(() => {
      expect(screen.getByText('Subscription Required')).toBeInTheDocument();
    });

    // Try to click the locked subject - should not trigger API call
    const pythonSubject = screen.getByRole('button', { name: /python programming/i });
    fireEvent.click(pythonSubject);

    // Verify no selection API call was made (only the initial subjects fetch)
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(mockOnSelect).not.toHaveBeenCalled();
  });

  it('handles backend API errors gracefully', async () => {
    const mockOnSelect = jest.fn();
    
    // Mock subjects API response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        subjects: [
          {
            id: 'python',
            name: 'Python Programming',
            description: 'Learn Python from basics to advanced concepts',
            pricing: { monthly: 29.99, yearly: 299.99 },
            available: true,
            locked: false
          }
        ],
        total_count: 1
      })
    });

    // Mock subject selection API error
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
      expect(screen.getByText('Available')).toBeInTheDocument();
    });

    // Select the subject
    const pythonSubject = screen.getByRole('button', { name: /python programming/i });
    fireEvent.click(pythonSubject);

    // Wait for error to be handled
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    // Give some time for the error to be processed
    await waitFor(() => {
      // Verify callback was not called due to error
      expect(mockOnSelect).not.toHaveBeenCalled();
    });
    
    // Verify no success state is shown (the error should clear the selected state)
    await waitFor(() => {
      expect(screen.queryByText('Python Programming Selected')).not.toBeInTheDocument();
    });
  });
});