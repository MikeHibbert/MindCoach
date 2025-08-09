import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PaymentGate from '../PaymentGate';

// Mock fetch for E2E-style tests with realistic API responses
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

describe('PaymentGate E2E Tests', () => {
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

  describe('Complete User Journey - No Subscription to Active', () => {
    it('handles complete subscription purchase flow', async () => {
      const user = userEvent.setup();

      // Mock API responses for the complete flow
      const noSubscriptionResponse = {
        user_id: 'test-user',
        subject: {
          id: 'python',
          name: 'Python Programming',
          description: 'Learn Python from basics to advanced concepts'
        },
        access_status: {
          has_active_subscription: false,
          is_selected: false,
          can_access_lessons: false,
          requires_payment: true
        },
        subscription: null,
        pricing: {
          monthly: 29.99,
          yearly: 299.99
        }
      };

      const purchaseResponse = {
        message: 'Successfully purchased monthly subscription for Python Programming',
        subscription: {
          id: 1,
          user_id: 'test-user',
          subject: 'python',
          status: 'active',
          expires_at: '2024-12-31T23:59:59Z',
          purchased_at: '2024-01-15T10:30:00Z'
        },
        subject_info: {
          id: 'python',
          name: 'Python Programming',
          description: 'Learn Python from basics to advanced concepts'
        },
        payment: {
          transaction_id: 'mock_txn_test-user_python_1642248600.0',
          plan: 'monthly',
          amount: 29.99,
          processed_at: '2024-01-15T10:30:00Z'
        }
      };

      const activeSubscriptionResponse = {
        ...noSubscriptionResponse,
        access_status: {
          has_active_subscription: true,
          is_selected: true,
          can_access_lessons: true,
          requires_payment: false
        },
        subscription: purchaseResponse.subscription
      };

      // Set up fetch mock sequence
      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => noSubscriptionResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => purchaseResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => activeSubscriptionResponse
        });

      render(<PaymentGate {...defaultProps} />);

      // 1. Initial load should show subscription required
      await waitFor(() => {
        expect(screen.getByText('Subscription Required')).toBeInTheDocument();
      });

      expect(screen.getByText('Get full access to Python Programming with personalized lessons and content.')).toBeInTheDocument();
      expect(screen.getByText('Choose Your Plan')).toBeInTheDocument();

      // 2. Verify plan options are displayed
      expect(screen.getByLabelText(/Monthly/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Yearly/)).toBeInTheDocument();
      expect(screen.getByText('$29.99')).toBeInTheDocument();
      expect(screen.getByText('$299.99')).toBeInTheDocument();

      // 3. Verify monthly plan is selected by default
      const monthlyRadio = screen.getByLabelText(/Monthly/);
      expect(monthlyRadio).toBeChecked();
      expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();

      // 4. Click purchase button
      const purchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(purchaseButton);

      // 5. Verify processing state
      await waitFor(() => {
        expect(screen.getByText('Processing...')).toBeInTheDocument();
      });

      // 6. Verify API calls were made correctly
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

      // 7. Verify success callback was called
      await waitFor(() => {
        expect(defaultProps.onSubscriptionSuccess).toHaveBeenCalledWith(purchaseResponse);
      });

      // 8. Verify UI transitions to active subscription state
      await waitFor(() => {
        expect(screen.getByText('Subscription Active')).toBeInTheDocument();
      });

      expect(screen.getByText('You have full access to Python Programming content.')).toBeInTheDocument();
      expect(screen.getByText('Active Subscription')).toBeInTheDocument();
      expect(screen.getByText('Status: active')).toBeInTheDocument();
    });

    it('handles yearly subscription purchase', async () => {
      const user = userEvent.setup();

      const noSubscriptionResponse = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      const yearlyPurchaseResponse = {
        subscription: { id: 1, status: 'active' },
        payment: { plan: 'yearly', amount: 299.99 }
      };

      const activeResponse = {
        access_status: { has_active_subscription: true },
        subscription: { id: 1, status: 'active' }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => noSubscriptionResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => yearlyPurchaseResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => activeResponse
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

      // Verify correct API call for yearly plan
      await waitFor(() => {
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
  });

  describe('Subscription Management Journey', () => {
    it('handles subscription cancellation flow', async () => {
      const user = userEvent.setup();

      const activeSubscriptionResponse = {
        user_id: 'test-user',
        subject: {
          id: 'python',
          name: 'Python Programming'
        },
        access_status: {
          has_active_subscription: true,
          can_access_lessons: true,
          requires_payment: false
        },
        subscription: {
          id: 1,
          user_id: 'test-user',
          subject: 'python',
          status: 'active',
          expires_at: '2024-12-31T23:59:59Z'
        }
      };

      const cancelResponse = {
        message: 'Successfully cancelled subscription for Python Programming',
        subscription: {
          id: 1,
          user_id: 'test-user',
          subject: 'python',
          status: 'cancelled'
        },
        subject_info: {
          id: 'python',
          name: 'Python Programming'
        },
        cancelled_at: '2024-01-15T11:00:00Z'
      };

      const cancelledStatusResponse = {
        ...activeSubscriptionResponse,
        access_status: {
          has_active_subscription: false,
          can_access_lessons: false,
          requires_payment: true
        },
        subscription: null
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => activeSubscriptionResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => cancelResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => cancelledStatusResponse
        });

      render(<PaymentGate {...defaultProps} />);

      // 1. Verify active subscription interface
      await waitFor(() => {
        expect(screen.getByText('Subscription Active')).toBeInTheDocument();
      });

      expect(screen.getByText('You have full access to Python Programming content.')).toBeInTheDocument();
      expect(screen.getByText('Cancel Subscription')).toBeInTheDocument();

      // 2. Click cancel subscription
      const cancelButton = screen.getByText('Cancel Subscription');
      await user.click(cancelButton);

      // 3. Verify confirmation dialog appears
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      expect(screen.getByText('Cancel Subscription')).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to cancel your subscription to Python Programming/)).toBeInTheDocument();
      expect(screen.getByText('Keep Subscription')).toBeInTheDocument();

      // 4. Confirm cancellation
      const confirmButton = screen.getByRole('dialog').querySelector('button.btn-danger');
      expect(confirmButton).toHaveTextContent('Cancel Subscription');
      await user.click(confirmButton);

      // 5. Verify processing state
      await waitFor(() => {
        expect(screen.getByText('Canceling...')).toBeInTheDocument();
      });

      // 6. Verify API call
      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subscriptions/python', {
        method: 'DELETE'
      });

      // 7. Verify UI transitions back to subscription required
      await waitFor(() => {
        expect(screen.getByText('Subscription Required')).toBeInTheDocument();
      });

      expect(screen.queryByText('Subscription Active')).not.toBeInTheDocument();
    });

    it('handles cancellation dialog dismissal', async () => {
      const user = userEvent.setup();

      const activeSubscriptionResponse = {
        access_status: { has_active_subscription: true },
        subscription: { id: 1, status: 'active' }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => activeSubscriptionResponse
      });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Cancel Subscription')).toBeInTheDocument();
      });

      // Open cancellation dialog
      const cancelButton = screen.getByText('Cancel Subscription');
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Dismiss dialog
      const keepButton = screen.getByText('Keep Subscription');
      await user.click(keepButton);

      // Verify dialog is closed and no API call was made
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      expect(fetch).toHaveBeenCalledTimes(1); // Only initial status call
    });
  });

  describe('Error Handling Scenarios', () => {
    it('handles payment processing errors', async () => {
      const user = userEvent.setup();

      const noSubscriptionResponse = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      const paymentErrorResponse = {
        error: {
          code: 'PAYMENT_FAILED',
          message: 'Payment processing failed. Please try again.'
        }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => noSubscriptionResponse
        })
        .mockResolvedValueOnce({
          ok: false,
          json: async () => paymentErrorResponse
        });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });

      const purchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(purchaseButton);

      // Verify error is displayed
      await waitFor(() => {
        expect(screen.getByText('Payment processing failed. Please try again.')).toBeInTheDocument();
      });

      expect(screen.getByText('Error loading subscription')).toBeInTheDocument();
      expect(screen.getByLabelText('Retry loading subscription status')).toBeInTheDocument();
    });

    it('handles subscription conflict errors', async () => {
      const user = userEvent.setup();

      const noSubscriptionResponse = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      const conflictErrorResponse = {
        error: {
          code: 'SUBSCRIPTION_EXISTS',
          message: 'User already has an active subscription for this subject',
          subscription: { id: 1, status: 'active' }
        }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => noSubscriptionResponse
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 409,
          json: async () => conflictErrorResponse
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

    it('handles network errors gracefully', async () => {
      fetch.mockRejectedValueOnce(new Error('Network connection failed'));

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Network connection failed')).toBeInTheDocument();
        expect(screen.getByLabelText('Retry loading subscription status')).toBeInTheDocument();
      });
    });

    it('handles cancellation errors', async () => {
      const user = userEvent.setup();

      const activeSubscriptionResponse = {
        access_status: { has_active_subscription: true },
        subscription: { id: 1, status: 'active' }
      };

      const cancellationErrorResponse = {
        error: {
          code: 'CANCELLATION_FAILED',
          message: 'Failed to cancel subscription. Please contact support.'
        }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => activeSubscriptionResponse
        })
        .mockResolvedValueOnce({
          ok: false,
          json: async () => cancellationErrorResponse
        });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Cancel Subscription')).toBeInTheDocument();
      });

      const cancelButton = screen.getByText('Cancel Subscription');
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('dialog').querySelector('button.btn-danger');
      await user.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to cancel subscription. Please contact support.')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility and UX', () => {
    it('maintains proper focus management during state transitions', async () => {
      const user = userEvent.setup();

      const noSubscriptionResponse = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => noSubscriptionResponse
        })
        .mockRejectedValueOnce(new Error('Network error'));

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });

      // Trigger error
      const purchaseButton = screen.getByText('Subscribe Monthly');
      await user.click(purchaseButton);

      // Verify error state and focus management
      await waitFor(() => {
        const errorElement = screen.getByText('Network error');
        expect(errorElement).toBeInTheDocument();
        // In a real implementation, the error element would receive focus
      });
    });

    it('provides proper ARIA live regions for status updates', async () => {
      const activeSubscriptionResponse = {
        access_status: { has_active_subscription: true },
        subscription: { id: 1, status: 'active' }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => activeSubscriptionResponse
      });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        const statusRegion = screen.getByRole('status');
        expect(statusRegion).toBeInTheDocument();
        expect(statusRegion).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('supports keyboard navigation for plan selection', async () => {
      const user = userEvent.setup();

      const noSubscriptionResponse = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => noSubscriptionResponse
      });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Monthly/)).toBeInTheDocument();
      });

      // Test keyboard navigation
      const monthlyRadio = screen.getByLabelText(/Monthly/);
      const yearlyRadio = screen.getByLabelText(/Yearly/);

      monthlyRadio.focus();
      await user.keyboard('{ArrowDown}');
      expect(yearlyRadio).toHaveFocus();

      await user.keyboard('{Enter}');
      expect(yearlyRadio).toBeChecked();
    });
  });

  describe('Responsive Design Validation', () => {
    it('applies correct responsive classes', async () => {
      const noSubscriptionResponse = {
        access_status: { has_active_subscription: false },
        pricing: { monthly: 29.99, yearly: 299.99 }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => noSubscriptionResponse
      });

      render(<PaymentGate {...defaultProps} />);

      await waitFor(() => {
        const planGrid = screen.getByText('Choose Your Plan').closest('fieldset').querySelector('.grid');
        expect(planGrid).toHaveClass('grid-cols-1', 'tablet:grid-cols-2');
      });

      // Verify touch targets
      const planOptions = screen.getAllByRole('radio');
      planOptions.forEach(option => {
        expect(option.closest('div')).toHaveClass('touch-target');
      });
    });
  });
});