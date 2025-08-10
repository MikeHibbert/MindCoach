import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import App from '../App';

// Mock the components to avoid complex dependencies
jest.mock('../SubjectSelector', () => {
  return function MockSubjectSelector({ onSubjectSelect }) {
    return (
      <div data-testid="subject-selector">
        <button onClick={() => onSubjectSelect({ id: 'python', name: 'Python' })}>
          Select Python
        </button>
      </div>
    );
  };
});

jest.mock('../Survey', () => {
  return function MockSurvey({ onSurveyComplete }) {
    return (
      <div data-testid="survey">
        <button onClick={() => onSurveyComplete({ skill_level: 'intermediate' })}>
          Complete Survey
        </button>
      </div>
    );
  };
});

jest.mock('../LessonViewer', () => {
  return function MockLessonViewer() {
    return <div data-testid="lesson-viewer">Lesson Content</div>;
  };
});

jest.mock('../PaymentGate', () => {
  return function MockPaymentGate({ onSubscriptionComplete }) {
    return (
      <div data-testid="payment-gate">
        <button onClick={() => onSubscriptionComplete()}>
          Complete Payment
        </button>
      </div>
    );
  };
});

const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
};

describe('App Component', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    jest.clearAllMocks();
  });

  test('renders without crashing', () => {
    renderApp();
    expect(screen.getByTestId('app-container')).toBeInTheDocument();
  });

  test('displays subject selector initially', () => {
    renderApp();
    expect(screen.getByTestId('subject-selector')).toBeInTheDocument();
  });

  test('progresses through the learning flow', async () => {
    renderApp();
    
    // Start with subject selection
    expect(screen.getByTestId('subject-selector')).toBeInTheDocument();
    
    // Select a subject
    const selectButton = screen.getByText('Select Python');
    selectButton.click();
    
    // Should show survey after subject selection
    await waitFor(() => {
      expect(screen.getByTestId('survey')).toBeInTheDocument();
    });
    
    // Complete survey
    const completeButton = screen.getByText('Complete Survey');
    completeButton.click();
    
    // Should show lesson viewer after survey completion
    await waitFor(() => {
      expect(screen.getByTestId('lesson-viewer')).toBeInTheDocument();
    });
  });

  test('handles subscription required flow', async () => {
    // Mock a locked subject
    const MockSubjectSelectorWithLocked = ({ onSubjectSelect }) => (
      <div data-testid="subject-selector">
        <button onClick={() => onSubjectSelect({ id: 'javascript', name: 'JavaScript', locked: true })}>
          Select JavaScript (Locked)
        </button>
      </div>
    );

    jest.doMock('../SubjectSelector', () => MockSubjectSelectorWithLocked);

    renderApp();
    
    // Select locked subject
    const selectButton = screen.getByText('Select JavaScript (Locked)');
    selectButton.click();
    
    // Should show payment gate
    await waitFor(() => {
      expect(screen.getByTestId('payment-gate')).toBeInTheDocument();
    });
    
    // Complete payment
    const paymentButton = screen.getByText('Complete Payment');
    paymentButton.click();
    
    // Should proceed to survey after payment
    await waitFor(() => {
      expect(screen.getByTestId('survey')).toBeInTheDocument();
    });
  });

  test('maintains responsive layout structure', () => {
    renderApp();
    
    const appContainer = screen.getByTestId('app-container');
    expect(appContainer).toHaveClass('min-h-screen');
    
    // Check for responsive layout wrapper
    const layoutWrapper = screen.getByTestId('responsive-layout');
    expect(layoutWrapper).toBeInTheDocument();
  });

  test('handles error states gracefully', async () => {
    // Mock component that throws an error
    const ErrorComponent = () => {
      throw new Error('Test error');
    };

    jest.doMock('../SubjectSelector', () => ErrorComponent);

    // Mock console.error to avoid noise in test output
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    renderApp();
    
    // Should show error boundary
    await waitFor(() => {
      expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  test('persists user progress in localStorage', async () => {
    renderApp();
    
    // Select subject
    const selectButton = screen.getByText('Select Python');
    selectButton.click();
    
    // Check that selection is persisted
    await waitFor(() => {
      const storedData = localStorage.getItem('userProgress');
      expect(storedData).toBeTruthy();
      const parsed = JSON.parse(storedData);
      expect(parsed.selectedSubject).toEqual({ id: 'python', name: 'Python' });
    });
  });

  test('restores user progress from localStorage', () => {
    // Pre-populate localStorage
    const userProgress = {
      selectedSubject: { id: 'python', name: 'Python' },
      surveyCompleted: true,
      skillLevel: 'intermediate'
    };
    localStorage.setItem('userProgress', JSON.stringify(userProgress));

    renderApp();
    
    // Should skip to lesson viewer since survey is completed
    expect(screen.getByTestId('lesson-viewer')).toBeInTheDocument();
  });

  test('handles routing correctly', () => {
    // Test with different initial routes
    const routes = [
      '/',
      '/survey/python',
      '/lessons/python',
      '/payment/javascript'
    ];

    routes.forEach(route => {
      window.history.pushState({}, 'Test page', route);
      renderApp();
      
      // Should render appropriate component based on route
      const appContainer = screen.getByTestId('app-container');
      expect(appContainer).toBeInTheDocument();
    });
  });

  test('implements proper accessibility structure', () => {
    renderApp();
    
    // Check for main landmark
    const main = screen.getByRole('main');
    expect(main).toBeInTheDocument();
    
    // Check for proper heading hierarchy
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeInTheDocument();
    
    // Check for skip link
    const skipLink = screen.getByText(/skip to main content/i);
    expect(skipLink).toBeInTheDocument();
  });

  test('handles keyboard navigation', async () => {
    renderApp();
    
    // Test tab navigation
    const firstFocusable = screen.getByText('Select Python');
    firstFocusable.focus();
    
    expect(document.activeElement).toBe(firstFocusable);
    
    // Test Enter key activation
    firstFocusable.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    
    await waitFor(() => {
      expect(screen.getByTestId('survey')).toBeInTheDocument();
    });
  });

  test('provides proper loading states', async () => {
    // Mock delayed component loading
    const DelayedComponent = () => {
      const [loading, setLoading] = React.useState(true);
      
      React.useEffect(() => {
        setTimeout(() => setLoading(false), 100);
      }, []);
      
      if (loading) {
        return <div data-testid="loading">Loading...</div>;
      }
      
      return <div data-testid="loaded-content">Content loaded</div>;
    };

    jest.doMock('../SubjectSelector', () => DelayedComponent);

    renderApp();
    
    // Should show loading state initially
    expect(screen.getByTestId('loading')).toBeInTheDocument();
    
    // Should show content after loading
    await waitFor(() => {
      expect(screen.getByTestId('loaded-content')).toBeInTheDocument();
    });
  });
});