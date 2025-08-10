# JavaScript-Specific Content Templates

## JavaScript Learning Progression

### Beginner Level (Lessons 1-4)
1. **JavaScript Fundamentals**
   - JavaScript in the browser vs Node.js
   - Variables (var, let, const)
   - Basic data types and operators
   - Console.log and debugging

2. **Functions and Scope**
   - Function declarations vs expressions
   - Arrow functions
   - Parameters and return values
   - Scope and hoisting

3. **Control Structures**
   - if/else statements and ternary operator
   - for, while, and for...of loops
   - switch statements
   - break and continue

4. **Objects and Arrays**
   - Object creation and property access
   - Array creation and methods
   - Destructuring assignment
   - Spread and rest operators

### Intermediate Level (Lessons 5-7)
5. **DOM Manipulation**
   - Selecting elements
   - Modifying content and attributes
   - Event handling
   - Creating and removing elements

6. **Asynchronous JavaScript**
   - Callbacks and callback hell
   - Promises and .then()/.catch()
   - Async/await syntax
   - Fetch API for HTTP requests

7. **ES6+ Features**
   - Template literals
   - Classes and inheritance
   - Modules (import/export)
   - Map, Set, and Symbol

### Advanced Level (Lessons 8-10)
8. **Advanced Functions**
   - Closures and lexical scope
   - Higher-order functions
   - Function binding and call/apply
   - Currying and partial application

9. **Error Handling and Testing**
   - Try/catch/finally blocks
   - Custom error types
   - Unit testing basics
   - Debugging techniques

10. **Modern JavaScript Practices**
    - Package managers (npm/yarn)
    - Build tools and bundlers
    - Code linting and formatting
    - Performance optimization

## JavaScript Code Example Templates

### Basic Example Template
```javascript
// Example: [Concept Name]
// This example demonstrates [specific concept]

// Setup or variable declarations
const exampleVariable = 'example value';
let mutableVariable = 42;

// Main logic with comments
const result = processData(exampleVariable); // Explain what this does
console.log(`Result: ${result}`); // Show expected output

// Helper function (if needed)
function processData(input) {
    // Function logic with explanation
    return input.toUpperCase();
}
```

### Function Example Template
```javascript
/**
 * Brief description of what the function does
 * @param {type} parameter1 - Description of parameter
 * @param {type} parameter2 - Description of parameter
 * @returns {type} Description of return value
 */
function functionName(parameter1, parameter2) {
    // Function logic with comments
    const result = parameter1 + parameter2;
    return result;
}

// Arrow function alternative
const arrowFunction = (param1, param2) => {
    return param1 + param2;
};

// Usage examples
const example1 = functionName(5, 3);
const example2 = arrowFunction(10, 7);
console.log(`Results: ${example1}, ${example2}`); // Output: Results: 8, 17
```

### Object and Class Example Template
```javascript
// Object literal example
const objectExample = {
    property1: 'value1',
    property2: 42,
    
    method1() {
        return `${this.property1} - ${this.property2}`;
    },
    
    // Arrow function method (note: no 'this' binding)
    method2: () => {
        return 'Arrow function method';
    }
};

// Class example
class ExampleClass {
    constructor(prop1, prop2) {
        this.property1 = prop1;
        this.property2 = prop2;
    }
    
    methodName() {
        return `${this.property1} and ${this.property2}`;
    }
    
    static staticMethod() {
        return 'This is a static method';
    }
}

// Usage examples
console.log(objectExample.method1()); // Output: value1 - 42
const instance = new ExampleClass('hello', 'world');
console.log(instance.methodName()); // Output: hello and world
```

### Async/Await Example Template
```javascript
// Async function example
async function fetchData(url) {
    try {
        // Await the promise resolution
        const response = await fetch(url);
        
        // Check if request was successful
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Parse and return JSON data
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error; // Re-throw for caller to handle
    }
}

// Usage with error handling
async function useData() {
    try {
        const result = await fetchData('https://api.example.com/data');
        console.log('Data received:', result);
    } catch (error) {
        console.log('Failed to get data:', error.message);
    }
}
```

## JavaScript Exercise Templates

### Beginner Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Beginner)

**Objective:** [What the student should accomplish]

**Instructions:**
1. Create a function called `[functionName]` that takes `[parameters]`
2. Inside the function, [specific task]
3. Return the result and test with the provided examples

**Starter Code:**
```javascript
function functionName(/* parameters */) {
    // Your code here
}

// Test your function
console.log(functionName(/* test input */)); // Expected: [expected output]
```

**Expected Behavior:**
- Input: `[example input]` → Output: `[example output]`
- Input: `[example input 2]` → Output: `[example output 2]`

**Hints:**
- Remember that [specific JavaScript concept]
- Use [specific method/operator] to [accomplish task]
```

### Intermediate Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Intermediate)

**Scenario:** [Real-world context for the problem]

**Requirements:**
- [Specific requirement 1]
- [Specific requirement 2]
- [Error handling requirement]

**Starter Code:**
```javascript
// Provided setup code
const data = [/* sample data */];

function solutionFunction(input) {
    // TODO: Implement your solution
    // Consider edge cases and error handling
}

// Test cases
console.log(solutionFunction(testInput1)); // Expected: [output1]
console.log(solutionFunction(testInput2)); // Expected: [output2]
```

**Bonus Challenges:**
- Implement using [specific ES6+ feature]
- Add input validation
- Optimize for performance
```

### Advanced Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Advanced)

**Problem Statement:** [Complex, open-ended problem]

**Technical Requirements:**
- Use [specific JavaScript features/patterns]
- Implement proper error handling
- Include comprehensive testing
- Follow modern JavaScript best practices

**Constraints:**
- [Performance constraints]
- [Browser compatibility requirements]
- [Code style requirements]

**Deliverables:**
1. Main implementation with documentation
2. Test suite with edge cases
3. Performance analysis (if applicable)

**Evaluation Criteria:**
- Code correctness and robustness
- Use of appropriate JavaScript patterns
- Error handling and edge case coverage
- Code readability and maintainability
```

## JavaScript-Specific Best Practices

### Code Style Guidelines
```javascript
// Use const for values that don't change, let for variables
const API_URL = 'https://api.example.com';
let currentUser = null;

// Use descriptive names (camelCase)
const getUserPreferences = () => { /* ... */ };
const isUserLoggedIn = false;

// Use template literals for string interpolation
const message = `Hello, ${userName}! You have ${messageCount} messages.`;

// Use arrow functions for short, simple functions
const double = x => x * 2;
const add = (a, b) => a + b;

// Use object destructuring
const { name, email, age } = user;
const [first, second, ...rest] = array;

// Use default parameters
function greet(name = 'Guest') {
    return `Hello, ${name}!`;
}
```

### Common JavaScript Patterns
```javascript
// Module pattern
const myModule = (() => {
    let privateVariable = 0;
    
    return {
        publicMethod() {
            return privateVariable++;
        }
    };
})();

// Promise chaining
fetch('/api/data')
    .then(response => response.json())
    .then(data => processData(data))
    .then(result => updateUI(result))
    .catch(error => handleError(error));

// Array methods for functional programming
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(x => x * 2);
const evens = numbers.filter(x => x % 2 === 0);
const sum = numbers.reduce((acc, x) => acc + x, 0);

// Event handling with proper cleanup
function setupEventListeners() {
    const button = document.getElementById('myButton');
    const handler = () => console.log('Clicked!');
    
    button.addEventListener('click', handler);
    
    // Return cleanup function
    return () => button.removeEventListener('click', handler);
}
```

### Error Handling Patterns
```javascript
// Try-catch for synchronous code
try {
    const result = riskyOperation();
    console.log(result);
} catch (error) {
    console.error('Operation failed:', error.message);
} finally {
    cleanup();
}

// Promise error handling
asyncOperation()
    .then(result => {
        // Success handling
        return processResult(result);
    })
    .catch(error => {
        // Error handling
        console.error('Async operation failed:', error);
        return defaultValue;
    });

// Async/await error handling
async function handleAsyncOperation() {
    try {
        const result = await asyncOperation();
        return processResult(result);
    } catch (error) {
        console.error('Async operation failed:', error);
        return defaultValue;
    }
}
```

## JavaScript Assessment Criteria

### Code Quality Checklist
- [ ] Uses modern JavaScript features appropriately
- [ ] Follows consistent naming conventions (camelCase)
- [ ] Implements proper error handling
- [ ] Uses appropriate array/object methods
- [ ] Handles asynchronous operations correctly
- [ ] Includes proper documentation/comments
- [ ] Demonstrates understanding of scope and closures

### Common JavaScript Mistakes to Address
- Using var instead of let/const
- Not understanding hoisting and scope
- Callback hell instead of promises/async-await
- Not handling promise rejections
- Mutating objects/arrays unintentionally
- Not understanding 'this' binding
- Memory leaks from event listeners
- Not validating input parameters