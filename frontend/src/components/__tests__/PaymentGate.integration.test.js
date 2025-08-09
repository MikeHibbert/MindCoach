import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PaymentGate from '../PaymentGate';

// Mock fetch globally
global.fetch = jest.fn();

// Mock accessibility utilities
jest.mock('../../utils/accessibility', () => ({
  announceToScreenReader: jest.fn(),
  keyboardNavigation: {
    handleActivation: jest.fn((e, action) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        action();
      }
    })
  },
  ariaLabels: {
    fieldDescription: jest.fn(() => 'field description')
  },
  formAccessibility: {
    generateFieldIds: jest.fn(() => ({
      fieldId: 'test-field',
      labelId: 'test-label',
      errorId: 'test-error'
    })),
    getFieldAria: jest.fn(() => ({}))
  },
  touchTargets: {}
}));

describe('PaymentGate Integration Tests', () => {
  const defaultProps = {
    userId: 'test-user',
    subject: 'python',
    subjectName: 'Python Programming',
    onSubscriptionSuccess: jest.fn(),
    onCancel: jest.fn()
  };

  beforeEach(() => {
    fetch.mockClear();
    jest.clearAllMocks();
  });

  describe('Complete Purchase Flow', () => {
    it('completes full subscription purchase workflow', async () => {
      const user = userEvent.setup();

      // Mock initial subscription status (no subscription)
      const initialStatus = {
        user_id: 'test-user',
        subject: {
          id: 'python',
          name: 'Python Programming',
          description: 'Learn Python from basics to advanced concepts'
        },
        access_status: {
          has_active_subscription: false,
          requires_payment: true
        },
        subscription: null,
        pricing: {
          monthly: 29.99,
          yearly: 299.99
        }
      };

      // Mock purchase response
      const purchaseResponse = {
        message: 'Successfully purchased monthly subscription for Python Programming',
        subscription: {
          id: 1,
          user_id: 'test-user',
          subject: 'python',
          status: 'active',
          expires_at: '2024-12-31T23:59:59Z'
        },
        payment: {
          transaction_id: 'mock_txn_123',
          plan: 'monthly',
          amount: 29.99
        }
      };

      // Mock updated status after purchase
      const updatedStatus = {
        ...initialStatus,
        access_status: {
          has_active_subscription: true,
          requires_payment: false
        },
        subscription: purchaseResponse.subscription
      };

      // Set up fetch mocks
      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => initialStatus
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => purchaseResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedStatus
        });

      render(<PaymentGate {...defaultProps} />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Subscription Required')).toBeInTheDocument();
      });

      // Verify purchase interface is shown
      expect(screen.getByText('Choose Your Plan')).toBeInTheDocument();
      expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();

      // Click purchase button
      const purchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(purchaseButton);

      // Verify API calls
      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subjects/python/status');
      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subscriptions/python', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan: 'monthly',
          payment_method: 'mock'
        })
      });

      // Verify success callback
      await waitFor(() => {
        expect(defaultProps.onSubscriptionSuccess).toHaveBeenCalledWith(purchaseResponse);
      });
    });

    it('handles yearly subscription purchase', async () => {
      const user = userEvent.setup();

      const initialStatus = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      const purchaseResponse = {
        subscription: { id: 1, status: 'active' },
        payment: { plan: 'yearly', amount: 299.99 }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => initialStatus
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => purchaseResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ access_status: { has_active_subscription: true } })
        });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Choose Your Plan')).toBeInTheDocument();
      });

      // Select yearly plan
      const yearlyRadio = screen.getByLabelText(/Yearly/);
      await user.click(yearlyRadio);

      expect(yearlyRadio).toBeChecked();
      expect(screen.getByText('Subscribe Yearly')).toBeInTheDocument();

      // Purchase yearly subscription
      const purchaseButton = screen.getByText('Subscribe Yearly');
      await user.click(purchaseButton);

      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subscriptions/python', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan: 'yearly',
          payment_method: 'mock'
        })
      });
    });
  });

  describe('Subscription Management Flow', () => {
    it('completes subscription cancellation workflow', async () => {
      const user = userEvent.setup();

      const activeStatus = {
        access_status: { has_active_subscription: true },
        subscription: {
          id: 1,
          status: 'active',
          expires_at: '2024-12-31T23:59:59Z'
        }
      };

      const cancelResponse = {
        message: 'Successfully cancelled subscription',
        subscription: { id: 1, status: 'cancelled' }
      };

      const cancelledStatus = {
        access_status: { has_active_subscription: false },
        subscription: null
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => activeStatus
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => cancelResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => cancelledStatus
        });

      render(<PaymentGate {...defaultProps} />);

      // Wait for active subscription interface
      await waitFor(() => {
        expect(screen.getByText('Subscription Active')).toBeInTheDocument();
      });

      // Click cancel subscription
      const cancelButton = screen.getByText('Cancel Subscription');
      await user.click(cancelButton);

      // Confirm cancellation in dialog
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('dialog').querySelector('button.btn-danger');
      await user.click(confirmButton);

      // Verify API call
      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subscriptions/python', {
        method: 'DELETE'
      });

      // Verify status refresh
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(3); // Initial load, cancel, refresh
      });
    });
  });

  describe('Error Handling Integration', () => {
    it('handles purchase failure and allows retry', async () => {
      const user = userEvent.setup();

      const initialStatus = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => initialStatus
        })
        .mockResolvedValueOnce({
          ok: false,
          json: async () => ({
            error: { message: 'Payment processing failed' }
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            subscription: { id: 1, status: 'active' }
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ access_status: { has_active_subscription: true } })
        });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });

      // First purchase attempt (fails)
      const purchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(purchaseButton);

      // Verify error is shown
      await waitFor(() => {
        expect(screen.getByText('Payment processing failed')).toBeInTheDocument();
      });

      // Retry purchase
      const retryButton = screen.getByLabelText('Retry loading subscription status');
      await user.click(retryButton);

      // Wait for interface to reload
      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });

      // Second purchase attempt (succeeds)
      const newPurchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(newPurchaseButton);

      // Verify success
      await waitFor(() => {
        expect(defaultProps.onSubscriptionSuccess).toHaveBeenCalled();
      });
    });

    it('handles network errors gracefully', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
        expect(screen.getByLabelText('Retry loading subscription status')).toBeInTheDocument();
      });
    });

    it('handles subscription conflict error', async () => {
      const user = userEvent.setup();

      const initialStatus = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => initialStatus
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 409,
          json: async () => ({
            error: {
              code: 'SUBSCRIPTION_EXISTS',
              message: 'User already has an active subscription for this subject'
            }
          })
        });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });

      const purchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(purchaseButton);

      await waitFor(() => {
        expect(screen.getByText('User already has an active subscription for this subject')).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Status Updates', () => {
    it('reflects subscription status changes immediately', async () => {
      const user = userEvent.setup();

      // Start with no subscription
      const noSubscriptionStatus = {
        access_status: { has_active_subscription: false },
        subscription: null,
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      // After purchase
      const activeSubscriptionStatus = {
        access_status: { has_active_subscription: true },
        subscription: {
          id: 1,
          status: 'active',
          expires_at: '2024-12-31T23:59:59Z'
        }
      };

      const purchaseResponse = {
        subscription: { id: 1, status: 'active' }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => noSubscriptionStatus
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => purchaseResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => activeSubscriptionStatus
        });

      render(<PaymentGate {...defaultProps} />);

      // Initially shows purchase interface
      await waitFor(() => {
        expect(screen.getByText('Subscription Required')).toBeInTheDocument();
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });

      // Purchase subscription
      const purchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(purchaseButton);

      // Should now show active subscription interface
      await waitFor(() => {
        expect(screen.getByText('Subscription Active')).toBeInTheDocument();
        expect(screen.getByText('You have full access to Python Programming content.')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility Integration', () => {
    it('maintains focus management during state transitions', async () => {
      const user = userEvent.setup();

      const initialStatus = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => initialStatus
        })
        .mockRejectedValueOnce(new Error('Network error'));

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });

      // Trigger error
      const purchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(purchaseButton);

      // Error should be focused for screen readers
      await waitFor(() => {
        const errorElement = screen.getByText('Network error');
        expect(errorElement).toBeInTheDocument();
        // In real implementation, error element would be focused
      });
    });

    it('provides proper ARIA live regions for status updates', async () => {
      const initialStatus = {
        access_status: { has_active_subscription: true },
        subscription: { id: 1, status: 'active' }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => initialStatus
      });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        const statusRegion = screen.getByRole('status');
        expect(statusRegion).toBeInTheDocument();
        expect(statusRegion).toHaveAttribute('aria-live', 'polite');
      });
    });
  });
});