import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PaymentGate from '../PaymentGate';
import SubscriptionService from '../../services/subscriptionService';

// Mock the subscription service
jest.mock('../../services/subscriptionService');

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

const mockSubscriptionStatus = {
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

const mockActiveSubscriptionStatus = {
  ...mockSubscriptionStatus,
  access_status: {
    has_active_subscription: true,
    is_selected: true,
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

describe('PaymentGate Component', () => {
  const defaultProps = {
    userId: 'test-user',
    subject: 'python',
    subjectName: 'Python Programming',
    onSubscriptionSuccess: jest.fn(),
    onCancel: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('shows loading spinner while fetching subscription status', () => {
      SubscriptionService.getSubjectStatus.mockImplementation(() => new Promise(() => {}));
      
      render(<PaymentGate {...defaultProps} />);
      
      expect(screen.getByText('Loading subscription status...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('displays error message when subscription status fetch fails', async () => {
      const errorMessage = 'Failed to fetch subscription status';
      SubscriptionService.getSubjectStatus.mockRejectedValue(new Error(errorMessage));
      
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Error loading subscription')).toBeInTheDocument();
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it('allows retry when error occurs', async () => {
      SubscriptionService.getSubjectStatus
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockSubscriptionStatus);
      
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Error loading subscription')).toBeInTheDocument();
      });
      
      const retryButton = screen.getByLabelText('Retry loading subscription status');
      fireEvent.click(retryButton);
      
      await waitFor(() => {
        expect(screen.getByText('Subscription Required')).toBeInTheDocument();
      });
    });
  });

  describe('Subscription Purchase Interface', () => {
    beforeEach(() => {
      SubscriptionService.getSubjectStatus.mockResolvedValue(mockSubscriptionStatus);
    });

    it('renders subscription purchase interface for users without subscription', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Subscription Required')).toBeInTheDocument();
        expect(screen.getByText('Get full access to Python Programming with personalized lessons and content.')).toBeInTheDocument();
      });
    });

    it('displays subject information and features', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Python Programming')).toBeInTheDocument();
        expect(screen.getByText('Personalized learning path based on your skill level')).toBeInTheDocument();
        expect(screen.getByText('AI-generated lessons tailored to your needs')).toBeInTheDocument();
        expect(screen.getByText('Interactive exercises and practical examples')).toBeInTheDocument();
        expect(screen.getByText('Progress tracking and skill assessments')).toBeInTheDocument();
      });
    });

    it('shows plan selector with monthly and yearly options', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Choose Your Plan')).toBeInTheDocument();
        expect(screen.getByLabelText(/Monthly/)).toBeInTheDocument();
        expect(screen.getByLabelText(/Yearly/)).toBeInTheDocument();
        expect(screen.getByText('$29.99')).toBeInTheDocument();
        expect(screen.getByText('$299.99')).toBeInTheDocument();
        expect(screen.getByText('Save 17%')).toBeInTheDocument();
      });
    });

    it('allows plan selection', async () => {
      const user = userEvent.setup();
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Choose Your Plan')).toBeInTheDocument();
      });
      
      const yearlyPlan = screen.getByLabelText(/Yearly/);
      await user.click(yearlyPlan);
      
      expect(yearlyPlan).toBeChecked();
      expect(screen.getByText('Subscribe Yearly')).toBeInTheDocument();
    });

    it('handles subscription purchase', async () => {
      const user = userEvent.setup();
      const mockPurchaseResult = {
        subscription: { id: 1, status: 'active' },
        message: 'Successfully purchased monthly subscription'
      };
      
      SubscriptionService.purchaseSubscription.mockResolvedValue(mockPurchaseResult);
      SubscriptionService.getSubjectStatus
        .mockResolvedValueOnce(mockSubscriptionStatus)
        .mockResolvedValueOnce(mockActiveSubscriptionStatus);
      
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });
      
      const subscribeButton = screen.getByText('Subscribe Monthly');
      await user.click(subscribeButton);
      
      expect(SubscriptionService.purchaseSubscription).toHaveBeenCalledWith('test-user', 'python', 'monthly');
      expect(defaultProps.onSubscriptionSuccess).toHaveBeenCalledWith(mockPurchaseResult);
    });

    it('shows processing state during purchase', async () => {
      const user = userEvent.setup();
      SubscriptionService.purchaseSubscription.mockImplementation(() => new Promise(() => {}));
      
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });
      
      const subscribeButton = screen.getByText('Subscribe Monthly');
      await user.click(subscribeButton);
      
      expect(screen.getByText('Processing...')).toBeInTheDocument();
      expect(subscribeButton).toBeDisabled();
    });

    it('handles purchase errors', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Payment failed';
      SubscriptionService.purchaseSubscription.mockRejectedValue(new Error(errorMessage));
      
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Subscribe Monthly')).toBeInTheDocument();
      });
      
      const subscribeButton = screen.getByText('Subscribe Monthly');
      await user.click(subscribeButton);
      
      await waitFor(() => {
        expect(screen.getByText('Error loading subscription')).toBeInTheDocument();
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });
  });

  describe('Active Subscription Management', () => {
    beforeEach(() => {
      SubscriptionService.getSubjectStatus.mockResolvedValue(mockActiveSubscriptionStatus);
    });

    it('renders subscription management interface for active subscribers', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Subscription Active')).toBeInTheDocument();
        expect(screen.getByText('You have full access to Python Programming content.')).toBeInTheDocument();
        expect(screen.getByText('Active Subscription')).toBeInTheDocument();
      });
    });

    it('shows subscription details', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Status: active')).toBeInTheDocument();
        expect(screen.getByText(/Expires: /)).toBeInTheDocument();
      });
    });

    it('shows cancel subscription button', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Cancel Subscription')).toBeInTheDocument();
      });
    });

    it('shows cancel confirmation dialog', async () => {
      const user = userEvent.setup();
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Cancel Subscription')).toBeInTheDocument();
      });
      
      const cancelButton = screen.getByText('Cancel Subscription');
      await user.click(cancelButton);
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Are you sure you want to cancel your subscription to Python Programming?')).toBeInTheDocument();
      expect(screen.getByText('Keep Subscription')).toBeInTheDocument();
    });

    it('handles subscription cancellation', async () => {
      const user = userEvent.setup();
      SubscriptionService.cancelSubscription.mockResolvedValue({ message: 'Subscription cancelled' });
      SubscriptionService.getSubjectStatus
        .mockResolvedValueOnce(mockActiveSubscriptionStatus)
        .mockResolvedValueOnce(mockSubscriptionStatus);
      
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Cancel Subscription')).toBeInTheDocument();
      });
      
      const cancelButton = screen.getByText('Cancel Subscription');
      await user.click(cancelButton);
      
      const confirmButton = screen.getByRole('dialog').querySelector('button.btn-danger');
      await user.click(confirmButton);
      
      expect(SubscriptionService.cancelSubscription).toHaveBeenCalledWith('test-user', 'python');
    });

    it('calls onCancel when back button is clicked', async () => {
      const user = userEvent.setup();
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Back to Lessons')).toBeInTheDocument();
      });
      
      const backButton = screen.getByText('Back to Lessons');
      await user.click(backButton);
      
      expect(defaultProps.onCancel).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      SubscriptionService.getSubjectStatus.mockResolvedValue(mockSubscriptionStatus);
    });

    it('has proper ARIA labels and roles', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByRole('group')).toBeInTheDocument(); // Plan selector fieldset
        expect(screen.getByText('Choose Your Plan')).toBeInTheDocument(); // Legend
      });
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByLabelText(/Monthly/)).toBeInTheDocument();
      });
      
      const monthlyRadio = screen.getByLabelText(/Monthly/);
      monthlyRadio.focus();
      await user.keyboard('{Enter}');
      
      expect(monthlyRadio).toBeChecked();
    });

    it('announces status changes to screen readers', async () => {
      const { announceToScreenReader } = require('../../utils/accessibility');
      
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        expect(announceToScreenReader).toHaveBeenCalledWith(
          'Subscription required for Python Programming'
        );
      });
    });
  });

  describe('Responsive Design', () => {
    beforeEach(() => {
      SubscriptionService.getSubjectStatus.mockResolvedValue(mockSubscriptionStatus);
    });

    it('applies responsive classes for different screen sizes', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        const planGrid = screen.getByText('Choose Your Plan').closest('fieldset').querySelector('.grid');
        expect(planGrid).toHaveClass('grid-cols-1', 'tablet:grid-cols-2');
      });
    });

    it('has touch-friendly targets', async () => {
      render(<PaymentGate {...defaultProps} />);
      
      await waitFor(() => {
        const planOptions = screen.getAllByRole('radio');
        planOptions.forEach(option => {
          expect(option.closest('div')).toHaveClass('touch-target');
        });
      });
    });
  });
});