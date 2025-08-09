import React, { useState, useEffect, useRef } from 'react';
import SubscriptionService from '../services/subscriptionService';
import { 
  announceToScreenReader, 
  keyboardNavigation, 
  ariaLabels, 
  formAccessibility,
  touchTargets 
} from '../utils/accessibility';

const PaymentGate = ({ userId, subject, subjectName, onSubscriptionSuccess, onCancel }) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState('monthly');
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  
  // Refs for accessibility
  const errorRef = useRef(null);
  const statusRef = useRef(null);
  const planSelectorRef = useRef(null);
  const confirmDialogRef = useRef(null);

  useEffect(() => {
    if (userId && subject) {
      fetchSubscriptionStatus();
    }
  }, [userId, subject]);

  useEffect(() => {
    // Focus management for error announcements
    if (error && errorRef.current) {
      errorRef.current.focus();
    }
  }, [error]);

  const fetchSubscriptionStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const statusData = await SubscriptionService.getSubjectStatus(userId, subject);
      setSubscriptionStatus(statusData);
      
      // Announce status to screen readers
      const statusMessage = statusData.access_status?.has_active_subscription 
        ? `You have an active subscription for ${subjectName}`
        : `Subscription required for ${subjectName}`;
      announceToScreenReader(statusMessage);
      
    } catch (err) {
      console.error('Error fetching subscription status:', err);
      setError(err.message);
      announceToScreenReader(`Error loading subscription status: ${err.message}`, 'assertive');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchaseSubscription = async () => {
    if (!userId || !subject) return;
    
    try {
      setProcessingPayment(true);
      setError(null);
      
      announceToScreenReader(`Processing ${selectedPlan} subscription purchase for ${subjectName}`);
      
      const result = await SubscriptionService.purchaseSubscription(userId, subject, selectedPlan);
      
      // Refresh subscription status
      await fetchSubscriptionStatus();
      
      announceToScreenReader(`Successfully purchased ${selectedPlan} subscription for ${subjectName}`, 'assertive');
      
      // Call success callback
      if (onSubscriptionSuccess) {
        onSubscriptionSuccess(result);
      }
      
    } catch (err) {
      console.error('Error purchasing subscription:', err);
      setError(err.message);
      announceToScreenReader(`Payment failed: ${err.message}`, 'assertive');
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!userId || !subject) return;
    
    try {
      setProcessingPayment(true);
      setError(null);
      setShowCancelConfirm(false);
      
      announceToScreenReader(`Canceling subscription for ${subjectName}`);
      
      await SubscriptionService.cancelSubscription(userId, subject);
      
      // Refresh subscription status
      await fetchSubscriptionStatus();
      
      announceToScreenReader(`Successfully canceled subscription for ${subjectName}`, 'assertive');
      
    } catch (err) {
      console.error('Error canceling subscription:', err);
      setError(err.message);
      announceToScreenReader(`Cancellation failed: ${err.message}`, 'assertive');
    } finally {
      setProcessingPayment(false);
    }
  };

  const handlePlanChange = (plan) => {
    setSelectedPlan(plan);
    announceToScreenReader(`Selected ${plan} plan`);
  };

  const handleKeyDown = (e, action) => {
    keyboardNavigation.handleActivation(e, action);
  };

  // Generate form field IDs for accessibility
  const planFieldIds = formAccessibility.generateFieldIds('subscription-plan');

  const PlanSelector = () => (
    <div className="mb-6">
      <fieldset className="border border-gray-300 rounded-lg p-4">
        <legend className="text-lg font-semibold text-gray-900 px-2">
          Choose Your Plan
        </legend>
        
        <div className="grid grid-cols-1 tablet:grid-cols-2 gap-4 mt-4">
          {/* Monthly Plan */}
          <div
            className={`
              relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 touch-target
              ${selectedPlan === 'monthly' 
                ? 'border-blue-600 bg-blue-50 shadow-md' 
                : 'border-gray-300 bg-white hover:border-blue-400 hover:shadow-sm'
              }
              focus-within:ring-3 focus-within:ring-blue-500 focus-within:ring-offset-2
            `}
            onClick={() => handlePlanChange('monthly')}
          >
            <label className="flex items-start cursor-pointer">
              <input
                type="radio"
                name="subscription-plan"
                value="monthly"
                checked={selectedPlan === 'monthly'}
                onChange={() => handlePlanChange('monthly')}
                className="mt-1 mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                aria-describedby="monthly-plan-description"
              />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Monthly</h3>
                  <span className="text-2xl font-bold text-blue-600">
                    ${subscriptionStatus?.pricing?.monthly || '29.99'}
                  </span>
                </div>
                <p id="monthly-plan-description" className="text-sm text-gray-600 mt-1">
                  Billed monthly • Cancel anytime
                </p>
                <div className="text-sm text-gray-500 mt-2">
                  Perfect for trying out the course
                </div>
              </div>
            </label>
          </div>

          {/* Yearly Plan */}
          <div
            className={`
              relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 touch-target
              ${selectedPlan === 'yearly' 
                ? 'border-blue-600 bg-blue-50 shadow-md' 
                : 'border-gray-300 bg-white hover:border-blue-400 hover:shadow-sm'
              }
              focus-within:ring-3 focus-within:ring-blue-500 focus-within:ring-offset-2
            `}
            onClick={() => handlePlanChange('yearly')}
          >
            {/* Popular badge */}
            <div className="absolute -top-2 left-4 bg-green-500 text-white text-xs font-semibold px-2 py-1 rounded">
              Save 17%
            </div>
            
            <label className="flex items-start cursor-pointer">
              <input
                type="radio"
                name="subscription-plan"
                value="yearly"
                checked={selectedPlan === 'yearly'}
                onChange={() => handlePlanChange('yearly')}
                className="mt-1 mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                aria-describedby="yearly-plan-description"
              />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Yearly</h3>
                  <div className="text-right">
                    <span className="text-2xl font-bold text-blue-600">
                      ${subscriptionStatus?.pricing?.yearly || '299.99'}
                    </span>
                    <div className="text-sm text-gray-500 line-through">
                      ${((subscriptionStatus?.pricing?.monthly || 29.99) * 12).toFixed(2)}
                    </div>
                  </div>
                </div>
                <p id="yearly-plan-description" className="text-sm text-gray-600 mt-1">
                  Billed annually • Best value
                </p>
                <div className="text-sm text-gray-500 mt-2">
                  Full access with significant savings
                </div>
              </div>
            </label>
          </div>
        </div>
      </fieldset>
    </div>
  );

  const CancelConfirmDialog = () => (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cancel-dialog-title"
      aria-describedby="cancel-dialog-description"
    >
      <div 
        ref={confirmDialogRef}
        className="bg-white rounded-lg p-6 max-w-md w-full shadow-xl"
        tabIndex={-1}
      >
        <h3 id="cancel-dialog-title" className="text-lg font-semibold text-gray-900 mb-4">
          Cancel Subscription
        </h3>
        <p id="cancel-dialog-description" className="text-gray-600 mb-6">
          Are you sure you want to cancel your subscription to {subjectName}? 
          You will lose access to all lessons and content immediately.
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={() => setShowCancelConfirm(false)}
            className="btn-secondary"
            disabled={processingPayment}
          >
            Keep Subscription
          </button>
          <button
            onClick={handleCancelSubscription}
            className="btn-danger"
            disabled={processingPayment}
          >
            {processingPayment ? 'Canceling...' : 'Cancel Subscription'}
          </button>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
          <div 
            className="loading-spinner h-8 w-8 border-blue-600" 
            aria-hidden="true"
          ></div>
          <span className="ml-3 text-gray-700">Loading subscription status...</span>
          <span className="sr-only">Loading subscription information, please wait</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div 
          ref={errorRef}
          className="error-message"
          role="alert"
          aria-live="assertive"
          tabIndex={-1}
        >
          <div className="flex">
            <svg
              className="w-6 h-6 text-red-700 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-900">Error loading subscription</h3>
              <p className="text-sm text-red-800 mt-1">{error}</p>
              <button
                onClick={fetchSubscriptionStatus}
                className="mt-3 btn-secondary focus:ring-red-500"
                aria-label="Retry loading subscription status"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // If user has active subscription, show management interface
  if (subscriptionStatus?.access_status?.has_active_subscription) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Subscription Active</h2>
          <p className="text-gray-600">
            You have full access to {subjectName} content.
          </p>
        </div>

        <div 
          ref={statusRef}
          className="success-message mb-6"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-start">
            <svg
              className="w-6 h-6 text-green-700 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-900">
                Active Subscription
              </h3>
              <p className="text-sm text-green-800 mt-1">
                Status: {subscriptionStatus.subscription?.status || 'Active'}
                {subscriptionStatus.subscription?.expires_at && (
                  <span className="block">
                    Expires: {new Date(subscriptionStatus.subscription.expires_at).toLocaleDateString()}
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex flex-col tablet:flex-row tablet:items-center tablet:justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {subjectName} Subscription
              </h3>
              <p className="text-gray-600 mt-1">
                Full access to all lessons and content
              </p>
            </div>
            
            <div className="flex flex-col mobile:flex-row gap-3">
              <button
                onClick={() => onCancel && onCancel()}
                className="btn-secondary"
              >
                Back to Lessons
              </button>
              <button
                onClick={() => setShowCancelConfirm(true)}
                className="btn-danger"
                disabled={processingPayment}
              >
                Cancel Subscription
              </button>
            </div>
          </div>
        </div>

        {showCancelConfirm && <CancelConfirmDialog />}
      </div>
    );
  }

  // Show subscription purchase interface
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Subscription Required</h2>
        <p className="text-gray-600">
          Get full access to {subjectName} with personalized lessons and content.
        </p>
      </div>

      {/* Subject info card */}
      <div className="card mb-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">
              {subjectName}
            </h3>
            <p className="text-gray-600 mt-1">
              {subscriptionStatus?.subject?.description || 'Comprehensive programming course with personalized learning path'}
            </p>
            <div className="mt-3">
              <h4 className="text-sm font-medium text-gray-900 mb-2">What's included:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Personalized learning path based on your skill level
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  AI-generated lessons tailored to your needs
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Interactive exercises and practical examples
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Progress tracking and skill assessments
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Plan selector */}
      <PlanSelector />

      {/* Purchase button */}
      <div className="card">
        <div className="flex flex-col tablet:flex-row tablet:items-center tablet:justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Ready to start learning?
            </h3>
            <p className="text-gray-600 mt-1">
              Get instant access to all {subjectName} content
            </p>
          </div>
          
          <div className="flex flex-col mobile:flex-row gap-3">
            {onCancel && (
              <button
                onClick={onCancel}
                className="btn-secondary"
                disabled={processingPayment}
              >
                Back
              </button>
            )}
            <button
              onClick={handlePurchaseSubscription}
              className="btn-primary"
              disabled={processingPayment}
              aria-describedby="purchase-button-description"
            >
              {processingPayment ? (
                <span className="flex items-center">
                  <div className="loading-spinner h-4 w-4 border-white mr-2" aria-hidden="true"></div>
                  Processing...
                </span>
              ) : (
                `Subscribe ${selectedPlan === 'monthly' ? 'Monthly' : 'Yearly'}`
              )}
            </button>
          </div>
        </div>
        <p id="purchase-button-description" className="text-xs text-gray-500 mt-3">
          Secure payment processing • Cancel anytime • 30-day money-back guarantee
        </p>
      </div>
    </div>
  );
};

export default PaymentGate;