/**
 * Simple validation tests for accessibility implementation
 */
import { 
  generateId, 
  announceToScreenReader, 
  ariaLabels, 
  colorContrast, 
  touchTargets, 
  formAccessibility 
} from '../accessibility';

describe('Accessibility Implementation Validation', () => {
  beforeEach(() => {
    // Clear DOM before each test
    document.body.innerHTML = '';
  });

  test('generateId creates unique identifiers', () => {
    const id1 = generateId('test');
    const id2 = generateId('test');
    
    expect(id1).toMatch(/^test-/);
    expect(id2).toMatch(/^test-/);
    expect(id1).not.toBe(id2);
  });

  test('announceToScreenReader creates live region', () => {
    announceToScreenReader('Test message');
    
    const liveRegion = document.querySelector('[aria-live]');
    expect(liveRegion).toBeTruthy();
    expect(liveRegion.textContent).toBe('Test message');
    expect(liveRegion.getAttribute('aria-live')).toBe('polite');
    expect(liveRegion.className).toBe('sr-only');
  });

  test('ariaLabels.progressBar generates correct label', () => {
    const label = ariaLabels.progressBar(3, 10, 'Survey');
    expect(label).toBe('Survey progress: 3 of 10 (30%)');
  });

  test('colorContrast.getContrastClasses returns high contrast classes', () => {
    const primaryClasses = colorContrast.getContrastClasses('primary');
    expect(primaryClasses).toBe('bg-blue-800 text-white border-blue-700');
    
    const successClasses = colorContrast.getContrastClasses('success');
    expect(successClasses).toBe('bg-green-800 text-white border-green-700');
  });

  test('touchTargets.getTouchClasses provides minimum touch target sizes', () => {
    const defaultClasses = touchTargets.getTouchClasses();
    expect(defaultClasses).toContain('min-h-[48px]');
    expect(defaultClasses).toContain('min-w-[48px]');
    
    const smallClasses = touchTargets.getTouchClasses('small');
    expect(smallClasses).toContain('min-h-[44px]');
    expect(smallClasses).toContain('min-w-[44px]');
  });

  test('formAccessibility generates proper field relationships', () => {
    const fieldIds = formAccessibility.generateFieldIds('email');
    
    expect(fieldIds.fieldId).toMatch(/^email-/);
    expect(fieldIds.labelId).toMatch(/^email-.*-label$/);
    expect(fieldIds.descriptionId).toMatch(/^email-.*-description$/);
    expect(fieldIds.errorId).toMatch(/^email-.*-error$/);
    
    const aria = formAccessibility.getFieldAria(fieldIds, false, false);
    expect(aria.id).toBe(fieldIds.fieldId);
    expect(aria['aria-labelledby']).toBe(fieldIds.labelId);
  });

  test('formAccessibility handles error states correctly', () => {
    const fieldIds = formAccessibility.generateFieldIds('password');
    const aria = formAccessibility.getFieldAria(fieldIds, true, true);
    
    expect(aria['aria-invalid']).toBe('true');
    expect(aria['aria-describedby']).toBe(`${fieldIds.descriptionId} ${fieldIds.errorId}`);
  });
});