import SubscriptionService from '../subscriptionService';

// Mock fetch globally
global.fetch = jest.fn();

describe('SubscriptionService', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  describe('getUserSubscriptions', () => {
    it('fetches user subscriptions successfully', async () => {
      const mockResponse = {
        user_id: 'test-user',
        subscriptions: [
          {
            id: 1,
            user_id: 'test-user',
            subject: 'python',
            status: 'active',
            subject_info: {
              name: 'Python Programming',
              description: 'Learn Python from basics to advanced concepts'
            }
          }
        ],
        active_subscriptions: [
          {
            id: 1,
            user_id: 'test-user',
            subject: 'python',
            status: 'active'
          }
        ],
        total_subscriptions: 1,
        active_count: 1
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SubscriptionService.getUserSubscriptions('test-user');

      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subscriptions');
      expect(result).toEqual(mockResponse);
    });

    it('handles API errors', async () => {
      const errorResponse = {
        error: {
          code: 'USER_NOT_FOUND',
          message: 'User not found'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(SubscriptionService.getUserSubscriptions('invalid-user'))
        .rejects.toThrow('User not found');
    });

    it('handles network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(SubscriptionService.getUserSubscriptions('test-user'))
        .rejects.toThrow('Network error');
    });

    it('encodes user ID properly', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subscriptions: [] })
      });

      await SubscriptionService.getUserSubscriptions('user@example.com');

      expect(fetch).toHaveBeenCalledWith('/api/users/user%40example.com/subscriptions');
    });
  });

  describe('getSubjectStatus', () => {
    it('fetches subject status successfully', async () => {
      const mockResponse = {
        user_id: 'test-user',
        subject: {
          id: 'python',
          name: 'Python Programming',
          description: 'Learn Python from basics to advanced concepts'
        },
        access_status: {
          has_active_subscription: true,
          is_selected: true,
          can_access_lessons: true,
          requires_payment: false
        },
        subscription: {
          id: 1,
          status: 'active'
        },
        pricing: {
          monthly: 29.99,
          yearly: 299.99
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SubscriptionService.getSubjectStatus('test-user', 'python');

      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subjects/python/status');
      expect(result).toEqual(mockResponse);
    });

    it('handles subject not found error', async () => {
      const errorResponse = {
        error: {
          code: 'SUBJECT_NOT_FOUND',
          message: 'Subject not found'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(SubscriptionService.getSubjectStatus('test-user', 'invalid-subject'))
        .rejects.toThrow('Subject not found');
    });

    it('encodes parameters properly', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_status: {} })
      });

      await SubscriptionService.getSubjectStatus('user@example.com', 'node.js');

      expect(fetch).toHaveBeenCalledWith('/api/users/user%40example.com/subjects/node.js/status');
    });
  });

  describe('purchaseSubscription', () => {
    it('purchases subscription successfully', async () => {
      const mockResponse = {
        message: 'Successfully purchased monthly subscription for Python Programming',
        subscription: {
          id: 1,
          user_id: 'test-user',
          subject: 'python',
          status: 'active'
        },
        payment: {
          transaction_id: 'mock_txn_123',
          plan: 'monthly',
          amount: 29.99
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SubscriptionService.purchaseSubscription('test-user', 'python', 'monthly');

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
      expect(result).toEqual(mockResponse);
    });

    it('defaults to monthly plan', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subscription: {} })
      });

      await SubscriptionService.purchaseSubscription('test-user', 'python');

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
    });

    it('handles yearly plan', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subscription: {} })
      });

      await SubscriptionService.purchaseSubscription('test-user', 'python', 'yearly');

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

    it('handles payment failures', async () => {
      const errorResponse = {
        error: {
          code: 'PAYMENT_FAILED',
          message: 'Payment processing failed'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(SubscriptionService.purchaseSubscription('test-user', 'python'))
        .rejects.toThrow('Payment processing failed');
    });

    it('handles existing subscription conflict', async () => {
      const errorResponse = {
        error: {
          code: 'SUBSCRIPTION_EXISTS',
          message: 'User already has an active subscription for this subject'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(SubscriptionService.purchaseSubscription('test-user', 'python'))
        .rejects.toThrow('User already has an active subscription for this subject');
    });
  });

  describe('cancelSubscription', () => {
    it('cancels subscription successfully', async () => {
      const mockResponse = {
        message: 'Successfully cancelled subscription for Python Programming',
        subscription: {
          id: 1,
          user_id: 'test-user',
          subject: 'python',
          status: 'cancelled'
        },
        cancelled_at: '2024-01-15T10:30:00Z'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SubscriptionService.cancelSubscription('test-user', 'python');

      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subscriptions/python', {
        method: 'DELETE'
      });
      expect(result).toEqual(mockResponse);
    });

    it('handles subscription not found', async () => {
      const errorResponse = {
        error: {
          code: 'SUBSCRIPTION_NOT_FOUND',
          message: 'No subscription found for this subject'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(SubscriptionService.cancelSubscription('test-user', 'python'))
        .rejects.toThrow('No subscription found for this subject');
    });

    it('handles inactive subscription', async () => {
      const errorResponse = {
        error: {
          code: 'SUBSCRIPTION_NOT_ACTIVE',
          message: 'Subscription is not active and cannot be cancelled'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => errorResponse
      });

      await expect(SubscriptionService.cancelSubscription('test-user', 'python'))
        .rejects.toThrow('Subscription is not active and cannot be cancelled');
    });
  });

  describe('checkSubjectAccess', () => {
    it('returns access granted for active subscription', async () => {
      const mockResponse = {
        access_granted: true,
        subject: {
          id: 'python',
          name: 'Python Programming'
        },
        subscription_expires: '2024-12-31T23:59:59Z'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await SubscriptionService.checkSubjectAccess('test-user', 'python');

      expect(fetch).toHaveBeenCalledWith('/api/users/test-user/subjects/python/access');
      expect(result).toEqual(mockResponse);
    });

    it('handles payment required (402) response', async () => {
      const mockResponse = {
        access_granted: false,
        reason: 'SUBSCRIPTION_REQUIRED',
        message: 'Active subscription required to access this subject',
        subscription_options: {
          monthly: 29.99,
          yearly: 299.99
        }
      };

      fetch.mockResolvedValueOnce({
        status: 402,
        ok: false,
        json: async () => mockResponse
      });

      const result = await SubscriptionService.checkSubjectAccess('test-user', 'python');

      expect(result).toEqual({
        access_granted: false,
        reason: 'SUBSCRIPTION_REQUIRED',
        message: 'Active subscription required to access this subject',
        subscription_options: {
          monthly: 29.99,
          yearly: 299.99
        },
        current_subscription: undefined
      });
    });

    it('handles other API errors', async () => {
      const errorResponse = {
        error: {
          code: 'USER_NOT_FOUND',
          message: 'User not found'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => errorResponse
      });

      await expect(SubscriptionService.checkSubjectAccess('invalid-user', 'python'))
        .rejects.toThrow('User not found');
    });
  });

  describe('Error Handling', () => {
    it('handles missing error message gracefully', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({})
      });

      await expect(SubscriptionService.getUserSubscriptions('test-user'))
        .rejects.toThrow('Failed to fetch subscriptions');
    });

    it('handles malformed JSON response', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      await expect(SubscriptionService.getUserSubscriptions('test-user'))
        .rejects.toThrow('Invalid JSON');
    });

    it('logs errors to console', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(SubscriptionService.getUserSubscriptions('test-user'))
        .rejects.toThrow('Network error');

      expect(consoleSpy).toHaveBeenCalledWith(
        'Error fetching user subscriptions:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });
  });
});