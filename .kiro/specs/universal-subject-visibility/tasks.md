# Implementation Plan

- [x] 1. Update backend subjects API to remove subscription dependencies







  - Remove SubscriptionService imports and calls from subjects.py
  - Simplify subject response format by removing pricing and locked fields
  - Remove subscription validation logic from all subject endpoints
  - Add therapy subject to AVAILABLE_SUBJECTS configuration
  - _Requirements: 1.1, 3.1, 5.1_

- [ ] 2. Simplify subject listing endpoint
  - Remove subscription status checking logic from list_subjects() function
  - Update subject data structure to exclude locked and pricing fields
  - Ensure all subjects return with available: true
  - Remove user-specific subscription filtering
  - _Requirements: 1.1, 1.3, 4.4_

- [ ] 3. Remove payment gate endpoints
  - Remove or simplify /users/<user_id>/subjects/<subject>/select endpoint
  - Remove /users/<user_id>/subjects/<subject>/status endpoint  
  - Remove /users/<user_id>/subjects/<subject>/access endpoint
  - Update remaining endpoints to bypass subscription checks
  - _Requirements: 5.1, 5.4_

- [ ] 4. Update frontend SubjectSelector component
  - Remove subscription-related state variables and logic
  - Simplify SubjectCard component to remove lock indicators
  - Remove payment-related UI elements and styling
  - Update subject selection flow to proceed directly to survey
  - _Requirements: 2.1, 2.3, 4.3, 6.5_

- [ ] 5. Clean up frontend subscription handling
  - Remove subscription status checking in component lifecycle
  - Simplify API response processing to ignore subscription fields
  - Update error handling to remove payment-related error cases
  - Ensure consistent styling for all subject cards
  - _Requirements: 2.4, 4.1, 4.2_

- [ ] 6. Add therapy subject to configuration
  - Add therapy entry to AVAILABLE_SUBJECTS dictionary in subjects.py
  - Ensure therapy subject appears in API responses
  - Verify therapy subject works with existing survey and lesson generation
  - Test therapy subject accessibility in frontend
  - _Requirements: 1.1, 1.5, 3.2_

- [ ] 7. Update API response format
  - Remove pricing information from subject response objects
  - Remove locked field from subject responses
  - Maintain backward compatibility for existing fields (id, name, description, available)
  - Update API documentation comments to reflect simplified format
  - _Requirements: 4.4, 5.5_

- [ ] 8. Test end-to-end subject access flow
  - Write tests for simplified subject listing without subscription checks
  - Test direct subject selection without payment gates
  - Verify therapy subject appears and functions correctly
  - Test new subject addition still works without subscription logic
  - _Requirements: 1.1, 1.2, 3.4, 5.4_

- [ ] 9. Clean up unused subscription-related code
  - Remove subscription service imports where no longer needed
  - Remove subscription-related error handling code
  - Remove payment-related constants and configurations
  - Update code comments to reflect simplified access model
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 10. Verify accessibility and UI consistency
  - Test that all subjects have consistent visual styling
  - Verify keyboard navigation works across all subjects
  - Test screen reader compatibility with simplified subject cards
  - Ensure mobile responsiveness is maintained
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_