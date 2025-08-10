# Python-Specific Content Templates

## Python Learning Progression

### Beginner Level (Lessons 1-4)
1. **Python Basics and Setup**
   - Python installation and IDLE
   - Running Python scripts
   - Interactive vs script mode
   - Basic syntax rules

2. **Variables and Data Types**
   - Variable assignment and naming
   - Strings, integers, floats, booleans
   - Type conversion functions
   - Input/output with input() and print()

3. **Control Structures**
   - if/elif/else statements
   - Comparison and logical operators
   - for and while loops
   - break and continue

4. **Functions Fundamentals**
   - Function definition and calling
   - Parameters and arguments
   - Return values
   - Local vs global scope

### Intermediate Level (Lessons 5-7)
5. **Data Structures**
   - Lists: creation, indexing, methods
   - Dictionaries: keys, values, methods
   - Sets and tuples
   - List comprehensions

6. **File Handling and I/O**
   - Opening and closing files
   - Reading and writing text files
   - CSV file processing
   - Error handling with try/except

7. **Object-Oriented Programming**
   - Classes and objects
   - Attributes and methods
   - Constructor (__init__)
   - Inheritance basics

### Advanced Level (Lessons 8-10)
8. **Modules and Packages**
   - Importing modules
   - Creating custom modules
   - Package structure
   - Virtual environments

9. **Advanced Features**
   - Decorators
   - Generators and iterators
   - Lambda functions
   - Regular expressions

10. **Testing and Best Practices**
    - Unit testing with unittest
    - Code style (PEP 8)
    - Documentation strings
    - Debugging techniques

## Python Code Example Templates

### Basic Example Template
```python
# Example: [Concept Name]
# This example demonstrates [specific concept]

# Setup or imports (if needed)
import module_name

# Main code with comments
variable_name = "example_value"  # Explain what this does
result = function_name(variable_name)  # Explain the operation

# Output demonstration
print(f"Result: {result}")  # Show expected output
```

### Function Example Template
```python
def function_name(parameter1, parameter2):
    """
    Brief description of what the function does.
    
    Args:
        parameter1 (type): Description of parameter
        parameter2 (type): Description of parameter
    
    Returns:
        type: Description of return value
    """
    # Function logic with comments
    result = parameter1 + parameter2
    return result

# Usage example
example_result = function_name(5, 3)
print(f"Function returned: {example_result}")  # Output: Function returned: 8
```

### Class Example Template
```python
class ClassName:
    """Brief description of the class purpose."""
    
    def __init__(self, attribute1, attribute2):
        """Initialize the class with given attributes."""
        self.attribute1 = attribute1
        self.attribute2 = attribute2
    
    def method_name(self):
        """Description of what this method does."""
        return f"{self.attribute1} and {self.attribute2}"

# Usage example
instance = ClassName("value1", "value2")
result = instance.method_name()
print(result)  # Output: value1 and value2
```

## Python Exercise Templates

### Beginner Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Beginner)

**Objective:** [What the student should accomplish]

**Instructions:**
1. Create a variable called `[variable_name]` and assign it the value `[value]`
2. Use a `[control_structure]` to [specific task]
3. Print the result using an f-string

**Starter Code:**
```python
# Your code here
```

**Expected Output:**
```
[Show exactly what should be printed]
```

**Hints:**
- Remember that [specific Python concept]
- Use the [specific function/method] to [accomplish task]
```

### Intermediate Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Intermediate)

**Objective:** [Complex task requiring multiple concepts]

**Background:** [Context or scenario for the problem]

**Requirements:**
- [Specific requirement 1]
- [Specific requirement 2]
- [Specific requirement 3]

**Starter Code:**
```python
def function_name():
    # TODO: Implement this function
    pass

# Test your function
# [Test cases provided]
```

**Test Cases:**
```python
# Test case 1
assert function_name(input1) == expected_output1

# Test case 2
assert function_name(input2) == expected_output2
```
```

### Advanced Exercise Template
```markdown
### Exercise [N]: [Title] (Difficulty: Advanced)

**Scenario:** [Real-world problem description]

**Challenge:** [Complex problem requiring creative solution]

**Constraints:**
- [Performance or style constraints]
- [Specific Python features to use/avoid]

**Deliverables:**
1. [Main implementation]
2. [Test cases]
3. [Documentation]

**Evaluation Criteria:**
- Code correctness and efficiency
- Proper error handling
- Code style and documentation
- Creative problem-solving approach
```

## Python-Specific Best Practices

### Code Style Guidelines
- Follow PEP 8 style guide
- Use descriptive variable names (snake_case)
- Include docstrings for functions and classes
- Keep lines under 79 characters
- Use meaningful comments

### Common Python Idioms
```python
# List comprehension instead of loops
squares = [x**2 for x in range(10)]

# Dictionary comprehension
word_lengths = {word: len(word) for word in words}

# Enumerate instead of range(len())
for i, item in enumerate(items):
    print(f"{i}: {item}")

# Context managers for file handling
with open('file.txt', 'r') as f:
    content = f.read()

# String formatting with f-strings
message = f"Hello, {name}! You are {age} years old."
```

### Error Handling Patterns
```python
# Specific exception handling
try:
    result = risky_operation()
except ValueError as e:
    print(f"Invalid value: {e}")
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Unexpected error: {e}")
else:
    print("Operation successful")
finally:
    cleanup_resources()
```

## Python Assessment Criteria

### Code Quality Checklist
- [ ] Follows PEP 8 style guidelines
- [ ] Uses appropriate data structures
- [ ] Includes proper error handling
- [ ] Has clear, descriptive variable names
- [ ] Includes docstrings for functions/classes
- [ ] Demonstrates understanding of Python idioms
- [ ] Code is efficient and readable

### Common Python Mistakes to Address
- Using mutable default arguments
- Not understanding variable scope
- Inefficient string concatenation
- Not using context managers for files
- Catching overly broad exceptions
- Not following naming conventions