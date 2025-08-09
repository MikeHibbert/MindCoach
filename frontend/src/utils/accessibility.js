/**
 * Accessibility utilities for the Personalized Learning Path Generator
 * Provides helper functions for ARIA labels, keyboard navigation, and focus management
 */

/**
 * Generate unique IDs for form elements and ARIA relationships
 */
export const generateId = (prefix = 'element') => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Announce content to screen readers using live regions
 */
export const announceToScreenReader = (message, priority = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Focus management utilities
 */
export const focusManagement = {
  /**
   * Set focus to element with optional delay
   */
  setFocus: (element, delay = 0) => {
    if (!element) return;
    
    setTimeout(() => {
      element.focus();
    }, delay);
  },

  /**
   * Focus first focusable element in container
   */
  focusFirstElement: (container) => {
    if (!container) return;
    
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
  },

  /**
   * Trap focus within a container (for modals, dropdowns)
   */
  trapFocus: (container) => {
    if (!container) return () => {};
    
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return;
      
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };
    
    container.addEventListener('keydown', handleTabKey);
    
    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  }
};

/**
 * Keyboard navigation helpers
 */
export const keyboardNavigation = {
  /**
   * Handle arrow key navigation for lists/grids
   */
  handleArrowKeys: (e, items, currentIndex, onNavigate) => {
    let newIndex = currentIndex;
    
    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        e.preventDefault();
        newIndex = (currentIndex + 1) % items.length;
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
        e.preventDefault();
        newIndex = currentIndex === 0 ? items.length - 1 : currentIndex - 1;
        break;
      case 'Home':
        e.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        newIndex = items.length - 1;
        break;
      default:
        return;
    }
    
    onNavigate(newIndex);
  },

  /**
   * Handle Enter and Space key activation
   */
  handleActivation: (e, callback) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      callback();
    }
  }
};

/**
 * ARIA label generators
 */
export const ariaLabels = {
  /**
   * Generate progress bar label
   */
  progressBar: (current, total, context = '') => {
    const percentage = Math.round((current / total) * 100);
    return `${context} progress: ${current} of ${total} (${percentage}%)`;
  },

  /**
   * Generate navigation label
   */
  navigation: (current, total, type = 'page') => {
    return `${type} ${current} of ${total}`;
  },

  /**
   * Generate form field description
   */
  fieldDescription: (fieldName, isRequired = false, additionalInfo = '') => {
    let description = `${fieldName}`;
    if (isRequired) description += ', required';
    if (additionalInfo) description += `, ${additionalInfo}`;
    return description;
  },

  /**
   * Generate button action description
   */
  buttonAction: (action, context = '', state = '') => {
    let label = action;
    if (context) label += ` ${context}`;
    if (state) label += `, ${state}`;
    return label;
  }
};

/**
 * Color contrast utilities
 */
export const colorContrast = {
  /**
   * High contrast color pairs for accessibility
   */
  colors: {
    primary: {
      background: '#1e40af', // blue-800
      text: '#ffffff',
      border: '#1d4ed8' // blue-700
    },
    secondary: {
      background: '#374151', // gray-700
      text: '#ffffff',
      border: '#4b5563' // gray-600
    },
    success: {
      background: '#166534', // green-800
      text: '#ffffff',
      border: '#15803d' // green-700
    },
    warning: {
      background: '#ca8a04', // yellow-600
      text: '#000000',
      border: '#a16207' // yellow-700
    },
    error: {
      background: '#dc2626', // red-600
      text: '#ffffff',
      border: '#b91c1c' // red-700
    }
  },

  /**
   * Get high contrast class names
   */
  getContrastClasses: (type = 'primary') => {
    const colorMap = {
      primary: 'bg-blue-800 text-white border-blue-700',
      secondary: 'bg-gray-700 text-white border-gray-600',
      success: 'bg-green-800 text-white border-green-700',
      warning: 'bg-yellow-600 text-black border-yellow-700',
      error: 'bg-red-600 text-white border-red-700'
    };
    
    return colorMap[type] || colorMap.primary;
  }
};

/**
 * Screen reader utilities
 */
export const screenReader = {
  /**
   * Create screen reader only text
   */
  createSROnlyText: (text) => {
    const span = document.createElement('span');
    span.className = 'sr-only';
    span.textContent = text;
    return span;
  },

  /**
   * Check if screen reader is likely being used
   */
  isScreenReaderActive: () => {
    // Basic heuristic - not 100% accurate but helpful
    return window.navigator.userAgent.includes('NVDA') ||
           window.navigator.userAgent.includes('JAWS') ||
           window.speechSynthesis?.speaking ||
           document.querySelector('[aria-live]') !== null;
  }
};

/**
 * Touch target utilities for mobile accessibility
 */
export const touchTargets = {
  /**
   * Minimum touch target size (44px x 44px per WCAG)
   */
  minSize: 44,

  /**
   * Get touch-friendly classes
   */
  getTouchClasses: (size = 'default') => {
    const sizeMap = {
      small: 'min-h-[44px] min-w-[44px] p-2',
      default: 'min-h-[48px] min-w-[48px] p-3',
      large: 'min-h-[56px] min-w-[56px] p-4'
    };
    
    return sizeMap[size] || sizeMap.default;
  }
};

/**
 * Form accessibility helpers
 */
export const formAccessibility = {
  /**
   * Generate form field IDs and relationships
   */
  generateFieldIds: (fieldName) => {
    const baseId = generateId(fieldName);
    return {
      fieldId: baseId,
      labelId: `${baseId}-label`,
      descriptionId: `${baseId}-description`,
      errorId: `${baseId}-error`
    };
  },

  /**
   * Get ARIA attributes for form field
   */
  getFieldAria: (fieldIds, hasError = false, hasDescription = false) => {
    const aria = {
      id: fieldIds.fieldId,
      'aria-labelledby': fieldIds.labelId
    };

    const describedBy = [];
    if (hasDescription) describedBy.push(fieldIds.descriptionId);
    if (hasError) describedBy.push(fieldIds.errorId);
    
    if (describedBy.length > 0) {
      aria['aria-describedby'] = describedBy.join(' ');
    }

    if (hasError) {
      aria['aria-invalid'] = 'true';
    }

    return aria;
  }
};