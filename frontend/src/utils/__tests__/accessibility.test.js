/**
 * Tests for accessibility utilities
 */
import { 
  generateId, 
  announceToScreenReader, 
  focusManagement, 
  keyboardNavigation, 
  ariaLabels, 
  colorContrast, 
  screenReader, 
  touchTargets, 
  formAccessibility 
} from '../accessibility';

describe('Accessibility Utilities', () => {
  beforeEach(() => {
    // Clear DOM before each test
    document.body.innerHTML = '';
  });

  describe('generateId', () => {
    it('should generate unique IDs with prefix', () => {
      const id1 = generateId('test');
      const id2 = generateId('test');
      
      expect(id1).toMatch(/^test-/);
      expect(id2).toMatch(/^test-/);
      expect(id1).not.toBe(id2);
    });

    it('should use default prefix when none provided', () => {
      const id = generateId();
      expect(id).toMatch(/^element-/);
    });
  });

  describe('announceToScreenReader', () => {
    it('should create and remove announcement element', (done) => {
      announceToScreenReader('Test announcement');
      
      // Check that element was created
      const announcement = document.querySelector('[aria-live]');
      expect(announcement).toBeTruthy();
      expect(announcement.textContent).toBe('Test announcement');
      expect(announcement.getAttribute('aria-live')).toBe('polite');
      expect(announcement.className).toBe('sr-only');
      
      // Check that element is removed after timeout
      setTimeout(() => {
        const removedAnnouncement = document.querySelector('[aria-live]');
        expect(removedAnnouncement).toBeFalsy();
        done();
      }, 1100);
    });

    it('should use assertive priority when specified', () => {
      announceToScreenReader('Urgent message', 'assertive');
      
      const announcement = document.querySelector('[aria-live]');
      expect(announcement.getAttribute('aria-live')).toBe('assertive');
    });
  });

  describe('focusManagement', () => {
    let testElement;

    beforeEach(() => {
      testElement = document.createElement('button');
      testElement.textContent = 'Test Button';
      document.body.appendChild(testElement);
    });

    describe('setFocus', () => {
      it('should focus element immediately when no delay', () => {
        const focusSpy = jest.spyOn(testElement, 'focus');
        focusManagement.setFocus(testElement);
        
        expect(focusSpy).toHaveBeenCalled();
      });

      it('should focus element after delay', (done) => {
        const focusSpy = jest.spyOn(testElement, 'focus');
        focusManagement.setFocus(testElement, 100);
        
        expect(focusSpy).not.toHaveBeenCalled();
        
        setTimeout(() => {
          expect(focusSpy).toHaveBeenCalled();
          done();
        }, 150);
      });

      it('should handle null element gracefully', () => {
        expect(() => {
          focusManagement.setFocus(null);
        }).not.toThrow();
      });
    });

    describe('focusFirstElement', () => {
      it('should focus first focusable element in container', () => {
        const container = document.createElement('div');
        const button1 = document.createElement('button');
        const button2 = document.createElement('button');
        
        container.appendChild(button1);
        container.appendChild(button2);
        document.body.appendChild(container);
        
        const focusSpy = jest.spyOn(button1, 'focus');
        focusManagement.focusFirstElement(container);
        
        expect(focusSpy).toHaveBeenCalled();
      });

      it('should handle container with no focusable elements', () => {
        const container = document.createElement('div');
        container.innerHTML = '<p>No focusable elements</p>';
        document.body.appendChild(container);
        
        expect(() => {
          focusManagement.focusFirstElement(container);
        }).not.toThrow();
      });
    });
  });

  describe('keyboardNavigation', () => {
    const mockItems = ['item1', 'item2', 'item3'];
    let mockNavigate;

    beforeEach(() => {
      mockNavigate = jest.fn();
    });

    describe('handleArrowKeys', () => {
      it('should navigate down with ArrowDown', () => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        const preventDefaultSpy = jest.spyOn(event, 'preventDefault');
        
        keyboardNavigation.handleArrowKeys(event, mockItems, 0, mockNavigate);
        
        expect(preventDefaultSpy).toHaveBeenCalled();
        expect(mockNavigate).toHaveBeenCalledWith(1);
      });

      it('should navigate up with ArrowUp', () => {
        const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
        const preventDefaultSpy = jest.spyOn(event, 'preventDefault');
        
        keyboardNavigation.handleArrowKeys(event, mockItems, 1, mockNavigate);
        
        expect(preventDefaultSpy).toHaveBeenCalled();
        expect(mockNavigate).toHaveBeenCalledWith(0);
      });

      it('should wrap around at boundaries', () => {
        // Test wrapping from last to first
        const downEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' });
        keyboardNavigation.handleArrowKeys(downEvent, mockItems, 2, mockNavigate);
        expect(mockNavigate).toHaveBeenCalledWith(0);
        
        // Test wrapping from first to last
        const upEvent = new KeyboardEvent('keydown', { key: 'ArrowUp' });
        keyboardNavigation.handleArrowKeys(upEvent, mockItems, 0, mockNavigate);
        expect(mockNavigate).toHaveBeenCalledWith(2);
      });

      it('should navigate to first item with Home key', () => {
        const event = new KeyboardEvent('keydown', { key: 'Home' });
        keyboardNavigation.handleArrowKeys(event, mockItems, 2, mockNavigate);
        
        expect(mockNavigate).toHaveBeenCalledWith(0);
      });

      it('should navigate to last item with End key', () => {
        const event = new KeyboardEvent('keydown', { key: 'End' });
        keyboardNavigation.handleArrowKeys(event, mockItems, 0, mockNavigate);
        
        expect(mockNavigate).toHaveBeenCalledWith(2);
      });

      it('should not navigate with other keys', () => {
        const event = new KeyboardEvent('keydown', { key: 'Tab' });
        keyboardNavigation.handleArrowKeys(event, mockItems, 0, mockNavigate);
        
        expect(mockNavigate).not.toHaveBeenCalled();
      });
    });

    describe('handleActivation', () => {
      let mockCallback;

      beforeEach(() => {
        mockCallback = jest.fn();
      });

      it('should activate with Enter key', () => {
        const event = new KeyboardEvent('keydown', { key: 'Enter' });
        const preventDefaultSpy = jest.spyOn(event, 'preventDefault');
        
        keyboardNavigation.handleActivation(event, mockCallback);
        
        expect(preventDefaultSpy).toHaveBeenCalled();
        expect(mockCallback).toHaveBeenCalled();
      });

      it('should activate with Space key', () => {
        const event = new KeyboardEvent('keydown', { key: ' ' });
        const preventDefaultSpy = jest.spyOn(event, 'preventDefault');
        
        keyboardNavigation.handleActivation(event, mockCallback);
        
        expect(preventDefaultSpy).toHaveBeenCalled();
        expect(mockCallback).toHaveBeenCalled();
      });

      it('should not activate with other keys', () => {
        const event = new KeyboardEvent('keydown', { key: 'Tab' });
        keyboardNavigation.handleActivation(event, mockCallback);
        
        expect(mockCallback).not.toHaveBeenCalled();
      });
    });
  });

  describe('ariaLabels', () => {
    describe('progressBar', () => {
      it('should generate progress bar label', () => {
        const label = ariaLabels.progressBar(3, 10, 'Survey');
        expect(label).toBe('Survey progress: 3 of 10 (30%)');
      });

      it('should work without context', () => {
        const label = ariaLabels.progressBar(5, 8);
        expect(label).toBe(' progress: 5 of 8 (63%)');
      });
    });

    describe('navigation', () => {
      it('should generate navigation label', () => {
        const label = ariaLabels.navigation(2, 5, 'lesson');
        expect(label).toBe('lesson 2 of 5');
      });

      it('should use default type', () => {
        const label = ariaLabels.navigation(1, 3);
        expect(label).toBe('page 1 of 3');
      });
    });

    describe('fieldDescription', () => {
      it('should generate field description', () => {
        const label = ariaLabels.fieldDescription('Email', true, 'Must be valid format');
        expect(label).toBe('Email, required, Must be valid format');
      });

      it('should work with minimal parameters', () => {
        const label = ariaLabels.fieldDescription('Name');
        expect(label).toBe('Name');
      });
    });

    describe('buttonAction', () => {
      it('should generate button action description', () => {
        const label = ariaLabels.buttonAction('Submit', 'form', 'enabled');
        expect(label).toBe('Submit form, enabled');
      });

      it('should work with minimal parameters', () => {
        const label = ariaLabels.buttonAction('Click');
        expect(label).toBe('Click');
      });
    });
  });

  describe('colorContrast', () => {
    describe('getContrastClasses', () => {
      it('should return primary classes by default', () => {
        const classes = colorContrast.getContrastClasses();
        expect(classes).toBe('bg-blue-800 text-white border-blue-700');
      });

      it('should return correct classes for each type', () => {
        expect(colorContrast.getContrastClasses('success')).toBe('bg-green-800 text-white border-green-700');
        expect(colorContrast.getContrastClasses('warning')).toBe('bg-yellow-600 text-black border-yellow-700');
        expect(colorContrast.getContrastClasses('error')).toBe('bg-red-600 text-white border-red-700');
      });

      it('should fallback to primary for unknown type', () => {
        const classes = colorContrast.getContrastClasses('unknown');
        expect(classes).toBe('bg-blue-800 text-white border-blue-700');
      });
    });
  });

  describe('touchTargets', () => {
    describe('getTouchClasses', () => {
      it('should return default classes', () => {
        const classes = touchTargets.getTouchClasses();
        expect(classes).toBe('min-h-[48px] min-w-[48px] p-3');
      });

      it('should return correct classes for each size', () => {
        expect(touchTargets.getTouchClasses('small')).toBe('min-h-[44px] min-w-[44px] p-2');
        expect(touchTargets.getTouchClasses('large')).toBe('min-h-[56px] min-w-[56px] p-4');
      });
    });
  });

  describe('formAccessibility', () => {
    describe('generateFieldIds', () => {
      it('should generate all required IDs', () => {
        const ids = formAccessibility.generateFieldIds('email');
        
        expect(ids.fieldId).toMatch(/^email-/);
        expect(ids.labelId).toMatch(/^email-.*-label$/);
        expect(ids.descriptionId).toMatch(/^email-.*-description$/);
        expect(ids.errorId).toMatch(/^email-.*-error$/);
      });
    });

    describe('getFieldAria', () => {
      it('should generate basic ARIA attributes', () => {
        const fieldIds = {
          fieldId: 'test-field',
          labelId: 'test-label',
          descriptionId: 'test-description',
          errorId: 'test-error'
        };
        
        const aria = formAccessibility.getFieldAria(fieldIds);
        
        expect(aria.id).toBe('test-field');
        expect(aria['aria-labelledby']).toBe('test-label');
        expect(aria['aria-describedby']).toBeUndefined();
        expect(aria['aria-invalid']).toBeUndefined();
      });

      it('should include description and error in describedby', () => {
        const fieldIds = {
          fieldId: 'test-field',
          labelId: 'test-label',
          descriptionId: 'test-description',
          errorId: 'test-error'
        };
        
        const aria = formAccessibility.getFieldAria(fieldIds, true, true);
        
        expect(aria['aria-describedby']).toBe('test-description test-error');
        expect(aria['aria-invalid']).toBe('true');
      });
    });
  });
});