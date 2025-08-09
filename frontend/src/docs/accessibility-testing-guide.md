# Accessibility Testing Guide

This guide provides comprehensive instructions for manual accessibility testing of the Personalized Learning Path Generator application.

## Table of Contents

1. [Overview](#overview)
2. [Testing Tools](#testing-tools)
3. [Keyboard Navigation Testing](#keyboard-navigation-testing)
4. [Screen Reader Testing](#screen-reader-testing)
5. [Visual Testing](#visual-testing)
6. [WCAG 2.1 AA Compliance Checklist](#wcag-21-aa-compliance-checklist)
7. [Common Issues and Solutions](#common-issues-and-solutions)

## Overview

The application has been designed to meet WCAG 2.1 AA accessibility standards. This guide helps verify that all accessibility features work correctly across different devices and assistive technologies.

## Testing Tools

### Automated Testing Tools
- **axe-core**: Integrated into our test suite for automated accessibility scanning
- **axe DevTools**: Browser extension for manual testing
- **Lighthouse**: Built into Chrome DevTools for accessibility audits
- **WAVE**: Web accessibility evaluation tool

### Screen Readers
- **NVDA** (Windows): Free, widely used
- **JAWS** (Windows): Commercial, industry standard
- **VoiceOver** (macOS/iOS): Built-in Apple screen reader
- **TalkBack** (Android): Built-in Android screen reader

### Browser Extensions
- **axe DevTools**: Automated accessibility testing
- **Colour Contrast Analyser**: Check color contrast ratios
- **HeadingsMap**: Verify heading structure
- **Landmarks**: Check ARIA landmarks

## Keyboard Navigation Testing

### General Keyboard Navigation
Test all interactive elements can be reached and activated using only the keyboard.

#### Key Combinations to Test
- **Tab**: Move forward through interactive elements
- **Shift + Tab**: Move backward through interactive elements
- **Enter**: Activate buttons and links
- **Space**: Activate buttons, check checkboxes
- **Arrow Keys**: Navigate within groups (radio buttons, menus)
- **Escape**: Close modals, menus, or cancel operations
- **Home/End**: Jump to first/last item in lists

#### Test Scenarios

##### ResponsiveLayout Component
1. **Skip Link**
   - Press Tab when page loads
   - Verify skip link appears and is focused
   - Press Enter to skip to main content
   - Verify focus moves to main content area

2. **Navigation Menu**
   - Tab through all navigation items
   - Verify focus indicators are visible
   - Test arrow key navigation between menu items
   - Verify current page is properly indicated

3. **Mobile Menu**
   - On mobile viewport, tab to hamburger menu button
   - Press Enter to open menu
   - Verify focus moves into menu
   - Test Escape key to close menu
   - Verify focus returns to menu button

##### SubjectSelector Component
1. **Subject Cards (Grid View)**
   - Tab through all subject cards
   - Use arrow keys to navigate between cards
   - Press Enter or Space to select subjects
   - Verify locked subjects cannot be selected

2. **Subject Dropdown**
   - Tab to dropdown
   - Use arrow keys to navigate options
   - Press Enter to select
   - Verify disabled options cannot be selected

##### Survey Component
1. **Question Navigation**
   - Tab through all form elements
   - Use arrow keys within radio button groups
   - Test Previous/Next button navigation
   - Verify focus moves to question title when changing questions

2. **Form Validation**
   - Try to proceed without answering
   - Verify focus moves to error message
   - Verify error is announced to screen readers

##### LessonViewer Component
1. **Lesson Sidebar**
   - Tab through lesson list
   - Use arrow keys to navigate between lessons
   - Press Enter to select lessons
   - Verify current lesson is indicated

2. **Lesson Content**
   - Tab through headings and interactive elements
   - Verify code blocks are focusable
   - Test lesson completion button

3. **Navigation Controls**
   - Tab to Previous/Next buttons
   - Verify disabled state when appropriate
   - Test keyboard activation

### Focus Management Checklist
- [ ] Focus is visible on all interactive elements
- [ ] Focus order is logical and follows visual layout
- [ ] Focus is trapped in modals and menus
- [ ] Focus returns to trigger element when closing modals
- [ ] Skip links work correctly
- [ ] No keyboard traps (can always navigate away)

## Screen Reader Testing

### NVDA Testing (Windows)
1. **Installation**
   - Download from https://www.nvaccess.org/
   - Install and restart computer
   - Launch NVDA before opening browser

2. **Basic Commands**
   - **NVDA + Space**: Toggle speech mode
   - **Insert + F7**: Elements list (headings, links, etc.)
   - **H**: Navigate by headings
   - **B**: Navigate by buttons
   - **F**: Navigate by form fields
   - **L**: Navigate by links
   - **R**: Navigate by regions/landmarks

### VoiceOver Testing (macOS)
1. **Activation**
   - System Preferences > Accessibility > VoiceOver
   - Or press Cmd + F5

2. **Basic Commands**
   - **VO + A**: Read all
   - **VO + Right/Left Arrow**: Navigate elements
   - **VO + U**: Rotor (navigate by element type)
   - **VO + H**: Navigate by headings
   - **VO + B**: Navigate by buttons

### Screen Reader Test Scenarios

#### Content Structure
1. **Headings**
   - Navigate using heading shortcuts (H key in NVDA)
   - Verify heading hierarchy is logical (H1 > H2 > H3)
   - Check that headings describe content sections

2. **Landmarks**
   - Navigate using region shortcuts (R key in NVDA)
   - Verify main, navigation, and complementary landmarks
   - Check landmark labels are descriptive

3. **Lists**
   - Navigate to lists using L key
   - Verify list structure is announced correctly
   - Check list item count is announced

#### Interactive Elements
1. **Forms**
   - Navigate to form fields using F key
   - Verify labels are read with fields
   - Check error messages are announced
   - Test required field indicators

2. **Buttons**
   - Navigate using B key
   - Verify button purposes are clear
   - Check state changes are announced (pressed, expanded)

3. **Links**
   - Navigate using link shortcuts
   - Verify link purposes are clear from text alone
   - Check external links are identified

#### Dynamic Content
1. **Live Regions**
   - Test status updates are announced
   - Verify loading states are communicated
   - Check error messages interrupt speech

2. **Progress Indicators**
   - Verify progress is announced as it changes
   - Check completion states are communicated

### Screen Reader Checklist
- [ ] All content is readable by screen reader
- [ ] Navigation shortcuts work correctly
- [ ] Form labels and instructions are clear
- [ ] Error messages are announced
- [ ] Dynamic content changes are announced
- [ ] Images have appropriate alt text
- [ ] Complex content has proper descriptions

## Visual Testing

### Color Contrast Testing
Use the Colour Contrast Analyser or similar tools to verify:

1. **Text Contrast**
   - Normal text: minimum 4.5:1 ratio
   - Large text (18pt+ or 14pt+ bold): minimum 3:1 ratio
   - Test all text/background combinations

2. **Interactive Element Contrast**
   - Button borders and backgrounds
   - Form field borders
   - Focus indicators
   - Link colors

### High Contrast Mode Testing
1. **Windows High Contrast**
   - Enable: Alt + Left Shift + Print Screen
   - Test all components render correctly
   - Verify interactive elements are visible

2. **macOS Increase Contrast**
   - System Preferences > Accessibility > Display
   - Enable "Increase contrast"
   - Test component visibility

### Zoom Testing
Test at different zoom levels:
- 100% (baseline)
- 200% (WCAG requirement)
- 400% (enhanced accessibility)

#### Zoom Test Checklist
- [ ] All content remains visible
- [ ] No horizontal scrolling required
- [ ] Interactive elements remain usable
- [ ] Text doesn't overlap
- [ ] Images scale appropriately

### Motion and Animation Testing
1. **Reduced Motion**
   - Enable in OS settings
   - Verify animations are reduced/removed
   - Check transitions still provide feedback

2. **Animation Control**
   - Test pause/play controls where applicable
   - Verify no auto-playing content causes seizures

## WCAG 2.1 AA Compliance Checklist

### Perceivable
- [ ] **1.1.1** Non-text content has text alternatives
- [ ] **1.2.1** Audio-only and video-only content has alternatives
- [ ] **1.2.2** Captions provided for videos
- [ ] **1.2.3** Audio descriptions or media alternatives for videos
- [ ] **1.3.1** Information and relationships are programmatically determinable
- [ ] **1.3.2** Meaningful sequence is preserved
- [ ] **1.3.3** Instructions don't rely solely on sensory characteristics
- [ ] **1.3.4** Content adapts to different orientations
- [ ] **1.3.5** Input purpose is identified
- [ ] **1.4.1** Color is not the only means of conveying information
- [ ] **1.4.2** Audio control is available
- [ ] **1.4.3** Color contrast meets minimum requirements (4.5:1)
- [ ] **1.4.4** Text can be resized up to 200% without loss of functionality
- [ ] **1.4.5** Images of text are avoided
- [ ] **1.4.10** Content reflows at 320px width
- [ ] **1.4.11** Non-text contrast meets requirements (3:1)
- [ ] **1.4.12** Text spacing can be adjusted
- [ ] **1.4.13** Content on hover/focus is dismissible and persistent

### Operable
- [ ] **2.1.1** All functionality is keyboard accessible
- [ ] **2.1.2** No keyboard traps exist
- [ ] **2.1.4** Character key shortcuts can be turned off or remapped
- [ ] **2.2.1** Timing is adjustable
- [ ] **2.2.2** Moving content can be paused, stopped, or hidden
- [ ] **2.3.1** Content doesn't cause seizures (flash threshold)
- [ ] **2.4.1** Blocks of content can be bypassed
- [ ] **2.4.2** Pages have descriptive titles
- [ ] **2.4.3** Focus order is logical
- [ ] **2.4.4** Link purpose is clear from context
- [ ] **2.4.5** Multiple ways to locate pages exist
- [ ] **2.4.6** Headings and labels are descriptive
- [ ] **2.4.7** Focus indicators are visible
- [ ] **2.5.1** Complex gestures have simple alternatives
- [ ] **2.5.2** Touch cancellation is supported
- [ ] **2.5.3** Labels match accessible names
- [ ] **2.5.4** Motion actuation has alternatives

### Understandable
- [ ] **3.1.1** Page language is identified
- [ ] **3.1.2** Language changes are identified
- [ ] **3.2.1** Focus doesn't cause unexpected context changes
- [ ] **3.2.2** Input doesn't cause unexpected context changes
- [ ] **3.2.3** Navigation is consistent
- [ ] **3.2.4** Components are consistently identified
- [ ] **3.3.1** Errors are identified
- [ ] **3.3.2** Labels and instructions are provided
- [ ] **3.3.3** Error suggestions are provided
- [ ] **3.3.4** Error prevention for legal/financial/data submissions

### Robust
- [ ] **4.1.1** Markup is valid
- [ ] **4.1.2** Name, role, value are available to assistive technologies
- [ ] **4.1.3** Status messages are programmatically determinable

## Common Issues and Solutions

### Focus Management Issues
**Issue**: Focus disappears or jumps unexpectedly
**Solution**: 
- Use `focusManagement.setFocus()` utility
- Ensure dynamic content updates don't break focus
- Test with keyboard navigation

### Screen Reader Announcements
**Issue**: Important changes aren't announced
**Solution**:
- Use `aria-live` regions for dynamic content
- Implement `announceToScreenReader()` utility
- Test with actual screen readers

### Color Contrast Failures
**Issue**: Text doesn't meet contrast requirements
**Solution**:
- Use high contrast color palette
- Test with contrast analyzer tools
- Provide high contrast mode option

### Keyboard Navigation Problems
**Issue**: Elements can't be reached with keyboard
**Solution**:
- Ensure `tabindex` is set correctly
- Implement arrow key navigation for groups
- Test focus order thoroughly

### Form Accessibility Issues
**Issue**: Form fields lack proper labels
**Solution**:
- Use `formAccessibility.getFieldAria()` utility
- Associate labels with form controls
- Provide clear error messages

## Testing Schedule

### During Development
- Run automated axe tests with every build
- Test keyboard navigation for new features
- Verify color contrast for new designs

### Before Release
- Complete manual screen reader testing
- Full keyboard navigation audit
- Visual testing at different zoom levels
- High contrast mode verification

### Regular Audits
- Monthly accessibility review
- User testing with disabled users
- Update testing procedures as needed

## Resources

### Documentation
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Resources](https://webaim.org/)

### Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE](https://wave.webaim.org/)
- [Colour Contrast Analyser](https://www.tpgi.com/color-contrast-checker/)
- [NVDA Screen Reader](https://www.nvaccess.org/)

### Testing Services
- [AccessibilityOz](https://www.accessibilityoz.com/)
- [Deque Systems](https://www.deque.com/)
- [Level Access](https://www.levelaccess.com/)

Remember: Automated testing catches about 30% of accessibility issues. Manual testing and user feedback are essential for comprehensive accessibility.