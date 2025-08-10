# React-Specific Content Templates

## React Learning Progression

### Beginner Level (Lessons 1-4)
1. **React Fundamentals**
   - What is React and why use it
   - JSX syntax and rules
   - Creating your first component
   - React development environment setup

2. **Components and Props**
   - Functional vs class components
   - Props and prop types
   - Component composition
   - Conditional rendering

3. **State and Events**
   - useState hook introduction
   - Event handling in React
   - Controlled components
   - State updates and re-rendering

4. **Lists and Keys**
   - Rendering lists of data
   - Key prop importance
   - Dynamic list updates
   - List manipulation patterns

### Intermediate Level (Lessons 5-7)
5. **Component Lifecycle and Effects**
   - useEffect hook basics
   - Effect dependencies
   - Cleanup functions
   - Common effect patterns

6. **Forms and User Input**
   - Controlled vs uncontrolled components
   - Form validation
   - Multiple input handling
   - Form submission patterns

7. **State Management Patterns**
   - Lifting state up
   - useReducer hook
   - Context API basics
   - State management best practices

### Advanced Level (Lessons 8-10)
8. **Advanced Hooks**
   - Custom hooks creation
   - useMemo and useCallback
   - useRef and DOM manipulation
   - Performance optimization

9. **Component Patterns**
   - Higher-order components
   - Render props pattern
   - Compound components
   - Error boundaries

10. **Testing and Best Practices**
    - Component testing with React Testing Library
    - Mocking and test utilities
    - Performance monitoring
    - Production optimization

## React Code Example Templates

### Basic Component Template
```jsx
// Example: [Component Name]
// This component demonstrates [specific React concept]

import React from 'react';

// Functional component with props
function ComponentName({ prop1, prop2, children }) {
    // Component logic here
    const handleClick = () => {
        console.log('Button clicked!');
    };

    return (
        <div className="component-container">
            <h2>{prop1}</h2>
            <p>{prop2}</p>
            <button onClick={handleClick}>
                Click me
            </button>
            {children}
        </div>
    );
}

// Usage example
function App() {
    return (
        <ComponentName 
            prop1="Hello" 
            prop2="This is a prop"
        >
            <p>This is children content</p>
        </ComponentName>
    );
}

export default ComponentName;
```

### State Management Template
```jsx
import React, { useState, useEffect } from 'react';

function StatefulComponent() {
    // State declarations with descriptive names
    const [count, setCount] = useState(0);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);

    // Effect for side effects
    useEffect(() => {
        // Effect logic here
        console.log(`Count changed to: ${count}`);
        
        // Cleanup function (if needed)
        return () => {
            console.log('Cleanup');
        };
    }, [count]); // Dependencies array

    // Event handlers
    const handleIncrement = () => {
        setCount(prevCount => prevCount + 1);
    };

    const handleUserUpdate = (newUser) => {
        setUser(prevUser => ({
            ...prevUser,
            ...newUser
        }));
    };

    // Conditional rendering
    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h3>Count: {count}</h3>
            <button onClick={handleIncrement}>
                Increment
            </button>
            {user && (
                <div>
                    <p>Welcome, {user.name}!</p>
                </div>
            )}
        </div>
    );
}

export default StatefulComponent;
```

### Custom Hook Template
```jsx
import { useState, useEffect } from 'react';

// Custom hook for [specific functionality]
function useCustomHook(initialValue) {
    const [value, setValue] = useState(initialValue);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Hook logic
    useEffect(() => {
        // Side effect logic
        setLoading(true);
        
        // Async operation example
        const fetchData = async () => {
            try {
                // Simulate API call
                const result = await someAsyncOperation(value);
                setValue(result);
                setError(null);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [value]);

    // Return hook interface
    return {
        value,
        setValue,
        loading,
        error,
        // Additional helper functions
        reset: () => setValue(initialValue),
        isValid: value !== null && !error
    };
}

// Usage in component
function ComponentUsingHook() {
    const { value, setValue, loading, error, reset } = useCustomHook('initial');

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div>
            <p>Value: {value}</p>
            <button onClick={() => setValue('new value')}>
                Update
            </button>
            <button onClick={reset}>
                Reset
            </button>
        </div>
    );
}
```

### Form Handling Template
```jsx
import React, { useState } from 'react';

function FormComponent() {
    // Form state
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        message: ''
    });
    const [errors, setErrors] = useState({});
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Input change handler
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        
        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }
    };

    // Form validation
    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.name.trim()) {
            newErrors.name = 'Name is required';
        }
        
        if (!formData.email.trim()) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Email is invalid';
        }
        
        return newErrors;
    };

    // Form submission
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const newErrors = validateForm();
        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }

        setIsSubmitting(true);
        try {
            // Submit form data
            await submitFormData(formData);
            
            // Reset form on success
            setFormData({ name: '', email: '', message: '' });
            alert('Form submitted successfully!');
        } catch (error) {
            alert('Submission failed: ' + error.message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label htmlFor="name">Name:</label>
                <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    disabled={isSubmitting}
                />
                {errors.name && <span className="error">{errors.name}</span>}
            </div>

            <div>
                <label htmlFor="email">Email:</label>
                <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    disabled={isSubmitting}
                />
                {errors.email && <span className="error">{errors.email}</span>}
            </div>

            <div>
                <label htmlFor="message">Message:</label>
                <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleInputChange}
                    disabled={isSubmitting}
                />
            </div>

            <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Submitting...' : 'Submit'}
            </button>
        </form>
    );
}
```

## React Exercise Templates

### Beginner Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Beginner)

**Objective:** Create a React component that [specific functionality]

**Requirements:**
- Use functional component syntax
- Accept props: `[prop1]`, `[prop2]`
- Display [specific UI elements]
- Handle [specific user interaction]

**Starter Code:**
```jsx
import React from 'react';

function ComponentName(/* props here */) {
    // Your code here
    
    return (
        <div>
            {/* Your JSX here */}
        </div>
    );
}

export default ComponentName;
```

**Expected Behavior:**
- When [user action], then [expected result]
- Props should be displayed as [specific format]

**Testing:**
```jsx
// Test your component with:
<ComponentName prop1="test" prop2={42} />
```
```

### Intermediate Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Intermediate)

**Scenario:** [Real-world application context]

**Features to Implement:**
1. [Feature 1 with state management]
2. [Feature 2 with event handling]
3. [Feature 3 with conditional rendering]

**Technical Requirements:**
- Use appropriate hooks (useState, useEffect)
- Implement proper event handling
- Include form validation (if applicable)
- Handle loading and error states

**Starter Structure:**
```jsx
import React, { useState, useEffect } from 'react';

function ComponentName() {
    // State declarations
    
    // Effect hooks
    
    // Event handlers
    
    // Helper functions
    
    return (
        // JSX implementation
    );
}
```

**Bonus Challenges:**
- Add keyboard navigation support
- Implement local storage persistence
- Create reusable sub-components
```

### Advanced Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Advanced)

**Project Description:** [Complex application or feature]

**Architecture Requirements:**
- Create multiple interconnected components
- Implement custom hooks for shared logic
- Use Context API for state management (if applicable)
- Include comprehensive error handling

**Performance Considerations:**
- Optimize re-renders with useMemo/useCallback
- Implement proper key props for lists
- Consider component lazy loading

**Testing Requirements:**
- Write unit tests for components
- Test user interactions and edge cases
- Mock external dependencies

**Deliverables:**
1. Component implementation with proper structure
2. Custom hooks (if applicable)
3. Test suite with good coverage
4. Documentation of design decisions

**Evaluation Criteria:**
- Code organization and reusability
- Proper React patterns and best practices
- Performance optimization
- Error handling and user experience
```

## React-Specific Best Practices

### Component Design Principles
```jsx
// Keep components small and focused
function UserCard({ user, onEdit, onDelete }) {
    return (
        <div className="user-card">
            <h3>{user.name}</h3>
            <p>{user.email}</p>
            <button onClick={() => onEdit(user.id)}>Edit</button>
            <button onClick={() => onDelete(user.id)}>Delete</button>
        </div>
    );
}

// Use prop destructuring for cleaner code
function Welcome({ name, isLoggedIn = false }) {
    if (!isLoggedIn) {
        return <div>Please log in</div>;
    }
    
    return <h1>Welcome, {name}!</h1>;
}

// Prefer functional components and hooks
function Counter() {
    const [count, setCount] = useState(0);
    
    const increment = useCallback(() => {
        setCount(prev => prev + 1);
    }, []);
    
    return (
        <div>
            <p>Count: {count}</p>
            <button onClick={increment}>+</button>
        </div>
    );
}
```

### State Management Patterns
```jsx
// Use functional updates for state that depends on previous state
const [count, setCount] = useState(0);
const increment = () => setCount(prev => prev + 1);

// Use objects for related state
const [user, setUser] = useState({
    name: '',
    email: '',
    preferences: {}
});

const updateUser = (updates) => {
    setUser(prev => ({ ...prev, ...updates }));
};

// Use useReducer for complex state logic
const initialState = { count: 0, step: 1 };

function reducer(state, action) {
    switch (action.type) {
        case 'increment':
            return { ...state, count: state.count + state.step };
        case 'decrement':
            return { ...state, count: state.count - state.step };
        case 'setStep':
            return { ...state, step: action.step };
        default:
            return state;
    }
}

function Counter() {
    const [state, dispatch] = useReducer(reducer, initialState);
    
    return (
        <div>
            <p>Count: {state.count}</p>
            <button onClick={() => dispatch({ type: 'increment' })}>+</button>
            <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
        </div>
    );
}
```

### Performance Optimization
```jsx
// Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data, onUpdate }) => {
    // Expensive rendering logic
    return <div>{/* Complex UI */}</div>;
});

// Use useMemo for expensive calculations
function DataProcessor({ items }) {
    const processedData = useMemo(() => {
        return items.map(item => expensiveProcessing(item));
    }, [items]);
    
    return <div>{processedData.map(/* render */)}</div>;
}

// Use useCallback for event handlers passed to child components
function Parent() {
    const [count, setCount] = useState(0);
    
    const handleClick = useCallback(() => {
        setCount(prev => prev + 1);
    }, []);
    
    return <Child onClick={handleClick} />;
}
```

## React Assessment Criteria

### Code Quality Checklist
- [ ] Uses functional components and hooks appropriately
- [ ] Implements proper state management patterns
- [ ] Handles events correctly with proper binding
- [ ] Uses keys properly in lists
- [ ] Implements conditional rendering effectively
- [ ] Follows React naming conventions
- [ ] Includes proper error boundaries (for advanced)
- [ ] Optimizes performance where appropriate

### Common React Mistakes to Address
- Mutating state directly instead of using setState
- Missing keys in list items
- Using array indices as keys
- Not cleaning up effects properly
- Overusing useEffect
- Not memoizing expensive calculations
- Improper event handler binding
- Not handling loading and error states