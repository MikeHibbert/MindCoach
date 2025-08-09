/**
 * Subscription Service
 * Handles subscription management API calls
 */

class SubscriptionService {
  static async getUserSubscriptions(userId) {
    try {
      const response = await fetch(`/api/users/${encodeURIComponent(userId)}/subscriptions`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to fetch subscriptions');
      }
      
      return data;
    } catch (error) {
      console.error('Error fetching user subscriptions:', error);
      throw error;
    }
  }

  static async getSubjectStatus(userId, subject) {
    try {
      const response = await fetch(`/api/users/${encodeURIComponent(userId)}/subjects/${encodeURIComponent(subject)}/status`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to fetch subject status');
      }
      
      return data;
    } catch (error) {
      console.error('Error fetching subject status:', error);
      throw error;
    }
  }

  static async purchaseSubscription(userId, subject, plan = 'monthly') {
    try {
      const response = await fetch(`/api/users/${encodeURIComponent(userId)}/subscriptions/${encodeURIComponent(subject)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan: plan,
          payment_method: 'mock' // For now, using mock payment
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to purchase subscription');
      }
      
      return data;
    } catch (error) {
      console.error('Error purchasing subscription:', error);
      throw error;
    }
  }

  static async cancelSubscription(userId, subject) {
    try {
      const response = await fetch(`/api/users/${encodeURIComponent(userId)}/subscriptions/${encodeURIComponent(subject)}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to cancel subscription');
      }
      
      return data;
    } catch (error) {
      console.error('Error canceling subscription:', error);
      throw error;
    }
  }

  static async checkSubjectAccess(userId, subject) {
    try {
      const response = await fetch(`/api/users/${encodeURIComponent(userId)}/subjects/${encodeURIComponent(subject)}/access`);
      const data = await response.json();
      
      // 402 Payment Required is expected for locked subjects
      if (response.status === 402) {
        return {
          access_granted: false,
          reason: data.reason || 'SUBSCRIPTION_REQUIRED',
          message: data.message,
          subscription_options: data.subscription_options,
          current_subscription: data.current_subscription
        };
      }
      
      if (!response.ok) {
        throw new Error(data.error?.message || 'Failed to check subject access');
      }
      
      return data;
    } catch (error) {
      console.error('Error checking subject access:', error);
      throw error;
    }
  }
}

export default SubscriptionService;