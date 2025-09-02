"""
Lesson generation service for creating personalized lesson content based on survey results
"""

import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from app.services.survey_analysis_service import SurveyAnalysisService
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

class LessonGenerationService:
    """Service for generating personalized lesson content based on user skill level and survey results"""
    
    # Lesson templates organized by subject, skill level, and topic
    LESSON_TEMPLATES = {
        'python': {
            'beginner': {
                'variables_and_data_types': {
                    'title': 'Variables and Data Types in Python',
                    'estimated_time': '30 minutes',
                    'prerequisites': [],
                    'content_template': """# Variables and Data Types in Python

## Introduction
Variables are containers for storing data values. Python has several built-in data types that help you work with different kinds of information.

## What You'll Learn
- How to create and use variables
- Understanding Python's basic data types
- Type conversion and checking

## Variables in Python

In Python, you don't need to declare variables explicitly. You can create a variable by simply assigning a value to it:

```python
# Creating variables
name = "Alice"
age = 25
height = 5.6
is_student = True
```

## Basic Data Types

### 1. Strings (str)
Strings are sequences of characters enclosed in quotes:

```python
first_name = "John"
last_name = 'Doe'
full_name = first_name + " " + last_name
print(full_name)  # Output: John Doe
```

### 2. Integers (int)
Whole numbers without decimal points:

```python
score = 100
year = 2024
negative_number = -42
```

### 3. Floats (float)
Numbers with decimal points:

```python
price = 19.99
temperature = -5.5
pi = 3.14159
```

### 4. Booleans (bool)
True or False values:

```python
is_active = True
is_complete = False
```

## Type Checking and Conversion

You can check the type of a variable using the `type()` function:

```python
name = "Alice"
print(type(name))  # <class 'str'>

age = 25
print(type(age))   # <class 'int'>
```

Convert between types using built-in functions:

```python
# String to integer
age_str = "25"
age_int = int(age_str)

# Integer to string
score = 100
score_str = str(score)

# String to float
price_str = "19.99"
price_float = float(price_str)
```

## Practice Exercise

Try this exercise to test your understanding:

```python
# Create variables for a person's information
person_name = "Your Name"
person_age = 20
person_height = 5.8
is_employed = False

# Print the information
print(f"Name: {person_name}")
print(f"Age: {person_age}")
print(f"Height: {person_height} feet")
print(f"Employed: {is_employed}")

# Check the types
print(f"Name type: {type(person_name)}")
print(f"Age type: {type(person_age)}")
```

## Quiz

1. What is the correct way to create a string variable in Python?
   a) string name = "Alice"
   b) name = "Alice"
   c) var name = "Alice"
   d) name := "Alice"

2. Which function is used to check the type of a variable?
   a) check_type()
   b) typeof()
   c) type()
   d) get_type()

3. What is the output of `print(type(3.14))`?
   a) <class 'int'>
   b) <class 'float'>
   c) <class 'decimal'>
   d) <class 'number'>

**Answers: 1-b, 2-c, 3-b**

## Summary

In this lesson, you learned:
- How to create variables in Python
- The four basic data types: strings, integers, floats, and booleans
- How to check and convert between data types
- Practical examples of using variables and data types

Next, you'll learn about working with lists and other data structures!
""",
                    'topics': ['variables', 'data_types', 'type_conversion']
                },
                'lists_and_indexing': {
                    'title': 'Lists and Indexing in Python',
                    'estimated_time': '35 minutes',
                    'prerequisites': ['variables_and_data_types'],
                    'content_template': """# Lists and Indexing in Python

## Introduction
Lists are one of the most versatile data structures in Python. They allow you to store multiple items in a single variable and access them using indices.

## What You'll Learn
- How to create and modify lists
- Understanding list indexing and slicing
- Common list methods and operations

## Creating Lists

Lists are created using square brackets `[]`:

```python
# Empty list
empty_list = []

# List with items
fruits = ["apple", "banana", "orange"]
numbers = [1, 2, 3, 4, 5]
mixed_list = ["hello", 42, 3.14, True]
```

## Accessing List Items

Use indices to access individual items (starting from 0):

```python
fruits = ["apple", "banana", "orange"]

print(fruits[0])   # apple (first item)
print(fruits[1])   # banana (second item)
print(fruits[-1])  # orange (last item)
print(fruits[-2])  # banana (second to last)
```

## Modifying Lists

Lists are mutable, meaning you can change their contents:

```python
fruits = ["apple", "banana", "orange"]

# Change an item
fruits[1] = "grape"
print(fruits)  # ["apple", "grape", "orange"]

# Add items
fruits.append("kiwi")        # Add to end
fruits.insert(1, "mango")    # Insert at position 1
print(fruits)  # ["apple", "mango", "grape", "orange", "kiwi"]
```

## List Slicing

Extract portions of a list using slicing:

```python
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

print(numbers[2:5])    # [2, 3, 4] (items 2 to 4)
print(numbers[:3])     # [0, 1, 2] (first 3 items)
print(numbers[7:])     # [7, 8, 9] (from item 7 to end)
print(numbers[::2])    # [0, 2, 4, 6, 8] (every 2nd item)
```

## Common List Methods

```python
fruits = ["apple", "banana", "orange", "banana"]

# Length of list
print(len(fruits))     # 4

# Remove items
fruits.remove("banana")  # Removes first occurrence
print(fruits)           # ["apple", "orange", "banana"]

# Find index of item
index = fruits.index("orange")
print(index)           # 1

# Count occurrences
count = fruits.count("banana")
print(count)           # 1

# Sort list
numbers = [3, 1, 4, 1, 5]
numbers.sort()
print(numbers)         # [1, 1, 3, 4, 5]
```

## Practice Exercise

Create a shopping list program:

```python
# Create a shopping list
shopping_list = ["milk", "bread", "eggs"]

# Add items
shopping_list.append("cheese")
shopping_list.insert(0, "apples")

# Print the list
print("Shopping List:")
for i, item in enumerate(shopping_list):
    print(f"{i+1}. {item}")

# Remove an item
shopping_list.remove("bread")
print(f"Updated list: {shopping_list}")
```

## Quiz

1. What is the index of the first item in a Python list?
   a) 1
   b) 0
   c) -1
   d) It depends on the list

2. Which method adds an item to the end of a list?
   a) add()
   b) insert()
   c) append()
   d) push()

3. What does `my_list[2:5]` return?
   a) Items at indices 2, 3, 4, 5
   b) Items at indices 2, 3, 4
   c) Items at indices 3, 4, 5
   d) The 2nd and 5th items

**Answers: 1-b, 2-c, 3-b**

## Summary

In this lesson, you learned:
- How to create and access lists
- List indexing and negative indexing
- Modifying lists with append, insert, and remove
- List slicing for extracting portions
- Common list methods for manipulation

Next, you'll learn about functions and how to organize your code!
""",
                    'topics': ['lists', 'indexing', 'slicing', 'list_methods']
                },
                'functions_basics': {
                    'title': 'Functions in Python',
                    'estimated_time': '40 minutes',
                    'prerequisites': ['variables_and_data_types'],
                    'content_template': """# Functions in Python

## Introduction
Functions are reusable blocks of code that perform specific tasks. They help you organize your code and avoid repetition.

## What You'll Learn
- How to define and call functions
- Working with parameters and arguments
- Return values and scope

## Defining Functions

Use the `def` keyword to create functions:

```python
def greet():
    print("Hello, World!")

# Call the function
greet()  # Output: Hello, World!
```

## Functions with Parameters

Functions can accept input values called parameters:

```python
def greet_person(name):
    print(f"Hello, {name}!")

def add_numbers(a, b):
    result = a + b
    print(f"{a} + {b} = {result}")

# Call functions with arguments
greet_person("Alice")     # Hello, Alice!
add_numbers(5, 3)         # 5 + 3 = 8
```

## Return Values

Functions can return values using the `return` statement:

```python
def multiply(x, y):
    return x * y

def get_full_name(first, last):
    return f"{first} {last}"

# Use returned values
result = multiply(4, 7)
print(result)  # 28

name = get_full_name("John", "Doe")
print(name)    # John Doe
```

## Default Parameters

Provide default values for parameters:

```python
def greet_with_title(name, title="Mr."):
    return f"Hello, {title} {name}!"

print(greet_with_title("Smith"))           # Hello, Mr. Smith!
print(greet_with_title("Johnson", "Dr."))  # Hello, Dr. Johnson!
```

## Variable Scope

Variables have different scopes inside and outside functions:

```python
# Global variable
global_var = "I'm global"

def my_function():
    # Local variable
    local_var = "I'm local"
    print(global_var)  # Can access global
    print(local_var)   # Can access local

my_function()
print(global_var)  # Can access global
# print(local_var)  # Error! Can't access local variable outside function
```

## Practice Exercise

Create a simple calculator:

```python
def calculator(num1, num2, operation):
    if operation == "add":
        return num1 + num2
    elif operation == "subtract":
        return num1 - num2
    elif operation == "multiply":
        return num1 * num2
    elif operation == "divide":
        if num2 != 0:
            return num1 / num2
        else:
            return "Error: Division by zero!"
    else:
        return "Error: Invalid operation!"

# Test the calculator
print(calculator(10, 5, "add"))       # 15
print(calculator(10, 5, "subtract"))  # 5
print(calculator(10, 5, "multiply"))  # 50
print(calculator(10, 5, "divide"))    # 2.0
```

## Quiz

1. Which keyword is used to define a function in Python?
   a) function
   b) def
   c) define
   d) func

2. What does the `return` statement do?
   a) Prints a value
   b) Ends the function and optionally returns a value
   c) Creates a variable
   d) Calls another function

3. What happens if you try to access a local variable outside its function?
   a) It returns None
   b) It returns the last value
   c) It causes an error
   d) It returns 0

**Answers: 1-b, 2-b, 3-c**

## Summary

In this lesson, you learned:
- How to define functions with the `def` keyword
- Using parameters and arguments
- Returning values from functions
- Default parameters for flexibility
- Understanding variable scope

Next, you'll learn about conditional statements and decision making!
""",
                    'topics': ['functions', 'parameters', 'return_values', 'scope']
                }
            },
            'intermediate': {
                'classes_and_objects': {
                    'title': 'Classes and Objects in Python',
                    'estimated_time': '45 minutes',
                    'prerequisites': ['functions_basics'],
                    'content_template': """# Classes and Objects in Python

## Introduction
Object-Oriented Programming (OOP) is a programming paradigm that uses classes and objects to structure code. Python supports OOP, making it easier to create reusable and organized code.

## What You'll Learn
- Understanding classes and objects
- Creating and using class methods
- Instance variables and the `self` parameter
- Constructor methods with `__init__`

## Creating Classes

Use the `class` keyword to define a class:

```python
class Dog:
    # Class variable (shared by all instances)
    species = "Canis familiaris"
    
    def __init__(self, name, age):
        # Instance variables (unique to each instance)
        self.name = name
        self.age = age
    
    def bark(self):
        return f"{self.name} says Woof!"
    
    def get_info(self):
        return f"{self.name} is {self.age} years old"
```

## Creating Objects

Create instances (objects) of a class:

```python
# Create dog objects
dog1 = Dog("Buddy", 3)
dog2 = Dog("Max", 5)

# Access instance variables
print(dog1.name)  # Buddy
print(dog2.age)   # 5

# Call methods
print(dog1.bark())      # Buddy says Woof!
print(dog2.get_info())  # Max is 5 years old

# Access class variable
print(dog1.species)     # Canis familiaris
```

## The `self` Parameter

`self` refers to the current instance of the class:

```python
class Person:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def introduce(self):
        # self refers to the current instance
        return f"Hi, I'm {self.name} and my email is {self.email}"
    
    def update_email(self, new_email):
        self.email = new_email
        return f"Email updated to {self.email}"

person = Person("Alice", "alice@email.com")
print(person.introduce())  # Hi, I'm Alice and my email is alice@email.com
print(person.update_email("alice.new@email.com"))
```

## Class Methods and Instance Methods

```python
class BankAccount:
    # Class variable
    bank_name = "Python Bank"
    
    def __init__(self, account_holder, initial_balance=0):
        self.account_holder = account_holder
        self.balance = initial_balance
    
    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            return f"Deposited ${amount}. New balance: ${self.balance}"
        return "Invalid deposit amount"
    
    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            return f"Withdrew ${amount}. New balance: ${self.balance}"
        return "Insufficient funds or invalid amount"
    
    def get_balance(self):
        return f"Current balance: ${self.balance}"

# Create and use account
account = BankAccount("John Doe", 1000)
print(account.get_balance())    # Current balance: $1000
print(account.deposit(500))     # Deposited $500. New balance: $1500
print(account.withdraw(200))    # Withdrew $200. New balance: $1300
```

## Practice Exercise

Create a simple library book system:

```python
class Book:
    def __init__(self, title, author, isbn):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.is_available = True
    
    def borrow(self):
        if self.is_available:
            self.is_available = False
            return f"'{self.title}' has been borrowed"
        return f"'{self.title}' is not available"
    
    def return_book(self):
        if not self.is_available:
            self.is_available = True
            return f"'{self.title}' has been returned"
        return f"'{self.title}' was not borrowed"
    
    def get_info(self):
        status = "Available" if self.is_available else "Borrowed"
        return f"'{self.title}' by {self.author} - {status}"

# Test the Book class
book1 = Book("Python Programming", "John Smith", "123-456-789")
print(book1.get_info())    # 'Python Programming' by John Smith - Available
print(book1.borrow())      # 'Python Programming' has been borrowed
print(book1.get_info())    # 'Python Programming' by John Smith - Borrowed
print(book1.return_book()) # 'Python Programming' has been returned
```

## Quiz

1. What does the `self` parameter represent in a class method?
   a) The class itself
   b) The current instance of the class
   c) A global variable
   d) The parent class

2. Which method is automatically called when creating a new object?
   a) __new__
   b) __create__
   c) __init__
   d) __start__

3. What is the difference between class variables and instance variables?
   a) There is no difference
   b) Class variables are shared by all instances, instance variables are unique to each instance
   c) Instance variables are shared, class variables are unique
   d) Class variables are faster

**Answers: 1-b, 2-c, 3-b**

## Summary

In this lesson, you learned:
- How to create classes with the `class` keyword
- Understanding the `__init__` constructor method
- The importance of the `self` parameter
- Creating and using instance methods
- The difference between class and instance variables

Next, you'll learn about inheritance and more advanced OOP concepts!
""",
                    'topics': ['classes', 'objects', 'methods', 'self', 'constructor']
                }
            },
            'advanced': {
                'decorators_and_context_managers': {
                    'title': 'Decorators and Context Managers',
                    'estimated_time': '50 minutes',
                    'prerequisites': ['classes_and_objects', 'functions_basics'],
                    'content_template': """# Decorators and Context Managers in Python

## Introduction
Decorators and context managers are powerful Python features that help you write cleaner, more maintainable code. They provide elegant ways to modify function behavior and manage resources.

## What You'll Learn
- Understanding and creating decorators
- Function decorators and class decorators
- Context managers and the `with` statement
- Creating custom context managers

## Understanding Decorators

Decorators are functions that modify or enhance other functions:

```python
def my_decorator(func):
    def wrapper():
        print("Something before the function")
        func()
        print("Something after the function")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

# Equivalent to: say_hello = my_decorator(say_hello)
say_hello()
# Output:
# Something before the function
# Hello!
# Something after the function
```

## Decorators with Arguments

Handle functions that take parameters:

```python
def timing_decorator(func):
    import time
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

@timing_decorator
def slow_function(n):
    import time
    time.sleep(n)
    return f"Slept for {n} seconds"

result = slow_function(1)
print(result)
```

## Parameterized Decorators

Create decorators that accept their own arguments:

```python
def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")
# Output:
# Hello, Alice!
# Hello, Alice!
# Hello, Alice!
```

## Class Decorators

Decorators can also be applied to classes:

```python
def add_string_method(cls):
    def __str__(self):
        return f"{cls.__name__} instance with attributes: {self.__dict__}"
    cls.__str__ = __str__
    return cls

@add_string_method
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

person = Person("Bob", 30)
print(person)  # Person instance with attributes: {'name': 'Bob', 'age': 30}
```

## Context Managers

Context managers ensure proper resource management:

```python
# Built-in context manager for file handling
with open('example.txt', 'w') as file:
    file.write('Hello, World!')
# File is automatically closed when exiting the with block

# Multiple context managers
with open('input.txt', 'r') as infile, open('output.txt', 'w') as outfile:
    data = infile.read()
    outfile.write(data.upper())
```

## Creating Custom Context Managers

Using the `contextlib` module:

```python
from contextlib import contextmanager
import time

@contextmanager
def timer():
    start = time.time()
    print("Timer started")
    try:
        yield
    finally:
        end = time.time()
        print(f"Timer ended. Elapsed: {end - start:.4f} seconds")

# Usage
with timer():
    time.sleep(2)
    print("Doing some work...")
```

## Class-based Context Managers

Implement `__enter__` and `__exit__` methods:

```python
class DatabaseConnection:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None
    
    def __enter__(self):
        print(f"Connecting to {self.db_name}")
        self.connection = f"Connection to {self.db_name}"
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Closing connection to {self.db_name}")
        if exc_type:
            print(f"Exception occurred: {exc_val}")
        return False  # Don't suppress exceptions

# Usage
with DatabaseConnection("mydb") as conn:
    print(f"Using {conn}")
    # Simulate some database work
```

## Practical Example: Caching Decorator

```python
def memoize(func):
    cache = {}
    def wrapper(*args):
        if args in cache:
            print(f"Cache hit for {args}")
            return cache[args]
        print(f"Computing result for {args}")
        result = func(*args)
        cache[args] = result
        return result
    return wrapper

@memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))  # Computes and caches intermediate results
print(fibonacci(8))   # Uses cached results
```

## Quiz

1. What is the primary purpose of a decorator?
   a) To delete functions
   b) To modify or enhance function behavior
   c) To create new classes
   d) To handle exceptions

2. Which methods must a class implement to be used as a context manager?
   a) __start__ and __stop__
   b) __begin__ and __end__
   c) __enter__ and __exit__
   d) __open__ and __close__

3. What does the `yield` statement do in a context manager created with `@contextmanager`?
   a) Returns a value permanently
   b) Marks the point where the with block executes
   c) Ends the function
   d) Creates a generator

**Answers: 1-b, 2-c, 3-b**

## Summary

In this lesson, you learned:
- How to create and use function decorators
- Parameterized decorators for flexible behavior modification
- Class decorators for enhancing classes
- Context managers for resource management
- Creating custom context managers with classes and `@contextmanager`

These advanced features help you write more elegant and maintainable Python code!
""",
                    'topics': ['decorators', 'context_managers', 'resource_management', 'metaprogramming']
                }
            }
        },
        'javascript': {
            'beginner': {
                'variables_and_functions': {
                    'title': 'Variables and Functions in JavaScript',
                    'estimated_time': '35 minutes',
                    'prerequisites': [],
                    'content_template': """# Variables and Functions in JavaScript

## Introduction
JavaScript is a versatile programming language used for web development. Understanding variables and functions is fundamental to writing JavaScript code.

## What You'll Learn
- How to declare variables with var, let, and const
- Understanding function declarations and expressions
- Scope and hoisting concepts

## Variable Declarations

JavaScript has three ways to declare variables:

```javascript
// var - function-scoped, can be redeclared
var name = "John";
var name = "Jane"; // OK

// let - block-scoped, cannot be redeclared
let age = 25;
age = 26; // OK, can be reassigned
// let age = 27; // Error: Cannot redeclare

// const - block-scoped, cannot be reassigned
const PI = 3.14159;
// PI = 3.14; // Error: Cannot reassign
```

## Data Types

JavaScript has several primitive data types:

```javascript
// String
let firstName = "Alice";
let lastName = 'Smith';
let fullName = `${firstName} ${lastName}`; // Template literal

// Number
let integer = 42;
let decimal = 3.14;
let negative = -10;

// Boolean
let isActive = true;
let isComplete = false;

// Undefined and null
let undefinedVar;
console.log(undefinedVar); // undefined
let nullVar = null;
```

## Function Declarations

Create reusable blocks of code with functions:

```javascript
// Function declaration
function greet(name) {
    return `Hello, ${name}!`;
}

// Function call
console.log(greet("World")); // Hello, World!

// Function with multiple parameters
function add(a, b) {
    return a + b;
}

console.log(add(5, 3)); // 8
```

## Function Expressions

Functions can be assigned to variables:

```javascript
// Function expression
const multiply = function(x, y) {
    return x * y;
};

console.log(multiply(4, 7)); // 28

// Arrow function (ES6)
const divide = (a, b) => {
    return a / b;
};

// Shorter arrow function syntax
const square = x => x * x;
const sayHello = () => "Hello!";

console.log(divide(10, 2)); // 5
console.log(square(5));     // 25
console.log(sayHello());    // Hello!
```

## Scope

Variables have different scopes:

```javascript
// Global scope
let globalVar = "I'm global";

function myFunction() {
    // Function scope
    let functionVar = "I'm in the function";
    
    if (true) {
        // Block scope
        let blockVar = "I'm in the block";
        console.log(globalVar);    // Accessible
        console.log(functionVar);  // Accessible
        console.log(blockVar);     // Accessible
    }
    
    // console.log(blockVar); // Error: blockVar is not defined
}

myFunction();
```

## Practice Exercise

Create a simple calculator:

```javascript
function calculator(operation, num1, num2) {
    switch(operation) {
        case 'add':
            return num1 + num2;
        case 'subtract':
            return num1 - num2;
        case 'multiply':
            return num1 * num2;
        case 'divide':
            return num2 !== 0 ? num1 / num2 : 'Error: Division by zero';
        default:
            return 'Error: Invalid operation';
    }
}

// Test the calculator
console.log(calculator('add', 10, 5));      // 15
console.log(calculator('subtract', 10, 5)); // 5
console.log(calculator('multiply', 10, 5)); // 50
console.log(calculator('divide', 10, 5));   // 2
```

## Quiz

1. Which keyword creates a block-scoped variable that cannot be reassigned?
   a) var
   b) let
   c) const
   d) final

2. What is the difference between function declarations and function expressions?
   a) There is no difference
   b) Declarations are hoisted, expressions are not
   c) Expressions are faster
   d) Declarations cannot have parameters

3. What does this arrow function do: `const double = x => x * 2;`?
   a) Creates a variable called double
   b) Multiplies x by 2 and returns the result
   c) Both a and b
   d) Creates an error

**Answers: 1-c, 2-b, 3-c**

## Summary

In this lesson, you learned:
- The three ways to declare variables: var, let, and const
- JavaScript's primitive data types
- How to create and call functions
- Function expressions and arrow functions
- Understanding scope in JavaScript

Next, you'll learn about objects and arrays in JavaScript!
""",
                    'topics': ['variables', 'functions', 'scope', 'data_types']
                }
            },
            'intermediate': {
                'promises_and_async': {
                    'title': 'Promises and Async/Await in JavaScript',
                    'estimated_time': '45 minutes',
                    'prerequisites': ['variables_and_functions'],
                    'content_template': """# Promises and Async/Await in JavaScript

## Introduction
Asynchronous programming is crucial in JavaScript for handling operations like API calls, file reading, and timers without blocking the main thread.

## What You'll Learn
- Understanding asynchronous programming
- Working with Promises
- Using async/await syntax
- Error handling in asynchronous code

## Understanding Asynchronous Programming

JavaScript is single-threaded but can handle asynchronous operations:

```javascript
console.log("Start");

setTimeout(() => {
    console.log("This runs after 2 seconds");
}, 2000);

console.log("End");

// Output:
// Start
// End
// This runs after 2 seconds (after 2 seconds)
```

## Creating and Using Promises

Promises represent eventual completion of asynchronous operations:

```javascript
// Creating a Promise
const myPromise = new Promise((resolve, reject) => {
    const success = true;
    
    setTimeout(() => {
        if (success) {
            resolve("Operation successful!");
        } else {
            reject("Operation failed!");
        }
    }, 1000);
});

// Using the Promise
myPromise
    .then(result => {
        console.log(result); // "Operation successful!"
    })
    .catch(error => {
        console.error(error);
    });
```

## Promise Chaining

Chain multiple asynchronous operations:

```javascript
function fetchUser(id) {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({ id: id, name: `User ${id}` });
        }, 1000);
    });
}

function fetchUserPosts(userId) {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve([`Post 1 by User ${userId}`, `Post 2 by User ${userId}`]);
        }, 1000);
    });
}

// Promise chaining
fetchUser(1)
    .then(user => {
        console.log("User:", user);
        return fetchUserPosts(user.id);
    })
    .then(posts => {
        console.log("Posts:", posts);
    })
    .catch(error => {
        console.error("Error:", error);
    });
```

## Async/Await Syntax

A cleaner way to work with Promises:

```javascript
async function getUserData(id) {
    try {
        const user = await fetchUser(id);
        console.log("User:", user);
        
        const posts = await fetchUserPosts(user.id);
        console.log("Posts:", posts);
        
        return { user, posts };
    } catch (error) {
        console.error("Error:", error);
        throw error;
    }
}

// Using async function
getUserData(1)
    .then(data => {
        console.log("Complete data:", data);
    })
    .catch(error => {
        console.error("Failed to get user data:", error);
    });
```

## Promise.all and Promise.race

Handle multiple Promises:

```javascript
// Promise.all - wait for all promises to resolve
async function fetchMultipleUsers() {
    try {
        const promises = [
            fetchUser(1),
            fetchUser(2),
            fetchUser(3)
        ];
        
        const users = await Promise.all(promises);
        console.log("All users:", users);
    } catch (error) {
        console.error("One or more requests failed:", error);
    }
}

// Promise.race - resolve with the first completed promise
async function fetchFirstResponse() {
    try {
        const promises = [
            fetchUser(1),
            fetchUser(2),
            fetchUser(3)
        ];
        
        const firstUser = await Promise.race(promises);
        console.log("First user:", firstUser);
    } catch (error) {
        console.error("First request failed:", error);
    }
}
```

## Real-world Example: API Calls

```javascript
// Simulating API calls
async function fetchFromAPI(url) {
    return new Promise((resolve, reject) => {
        // Simulate network delay
        setTimeout(() => {
            if (url.includes('error')) {
                reject(new Error('API Error'));
            } else {
                resolve({
                    data: `Data from ${url}`,
                    status: 200
                });
            }
        }, Math.random() * 2000);
    });
}

async function loadPageData() {
    try {
        console.log("Loading page data...");
        
        // Load multiple resources in parallel
        const [userData, settingsData, notificationsData] = await Promise.all([
            fetchFromAPI('/api/user'),
            fetchFromAPI('/api/settings'),
            fetchFromAPI('/api/notifications')
        ]);
        
        console.log("User data:", userData);
        console.log("Settings:", settingsData);
        console.log("Notifications:", notificationsData);
        
        return {
            user: userData,
            settings: settingsData,
            notifications: notificationsData
        };
    } catch (error) {
        console.error("Failed to load page data:", error);
        throw error;
    }
}

// Usage
loadPageData()
    .then(pageData => {
        console.log("Page loaded successfully:", pageData);
    })
    .catch(error => {
        console.error("Page failed to load:", error);
    });
```

## Error Handling Best Practices

```javascript
async function robustAsyncFunction() {
    try {
        const result = await someAsyncOperation();
        return result;
    } catch (error) {
        // Log the error
        console.error("Operation failed:", error);
        
        // Decide whether to rethrow or handle
        if (error.code === 'NETWORK_ERROR') {
            // Retry logic could go here
            throw new Error('Network error - please try again');
        }
        
        // Return a default value or rethrow
        throw error;
    }
}
```

## Quiz

1. What does the `await` keyword do?
   a) Creates a new Promise
   b) Pauses execution until the Promise resolves
   c) Catches errors
   d) Makes code run faster

2. What happens if one Promise in `Promise.all()` rejects?
   a) The other Promises continue
   b) The entire Promise.all rejects immediately
   c) It returns partial results
   d) It ignores the rejected Promise

3. Which is true about async functions?
   a) They always return a Promise
   b) They run synchronously
   c) They cannot use try/catch
   d) They are faster than regular functions

**Answers: 1-b, 2-b, 3-a**

## Summary

In this lesson, you learned:
- The fundamentals of asynchronous programming in JavaScript
- How to create and use Promises
- The async/await syntax for cleaner asynchronous code
- Promise.all and Promise.race for handling multiple Promises
- Best practices for error handling in asynchronous code

Next, you'll learn about advanced JavaScript concepts like closures and prototypes!
""",
                    'topics': ['promises', 'async_await', 'asynchronous_programming', 'error_handling']
                }
            },
            'advanced': {
                'closures_and_prototypes': {
                    'title': 'Closures and Prototypes in JavaScript',
                    'estimated_time': '50 minutes',
                    'prerequisites': ['promises_and_async'],
                    'content_template': """# Closures and Prototypes in JavaScript

## Introduction
Closures and prototypes are advanced JavaScript concepts that enable powerful programming patterns. Understanding them is crucial for mastering JavaScript.

## What You'll Learn
- Understanding closures and lexical scope
- Practical applications of closures
- JavaScript's prototype-based inheritance
- Creating and manipulating prototypes

## Understanding Closures

A closure gives you access to an outer function's scope from an inner function:

```javascript
function outerFunction(x) {
    // Outer function's variable
    const outerVariable = x;
    
    function innerFunction(y) {
        // Inner function has access to outer function's variables
        console.log(outerVariable + y);
    }
    
    return innerFunction;
}

const myClosure = outerFunction(10);
myClosure(5); // 15

// The outer function has finished executing, but the inner function
// still has access to outerVariable through closure
```

## Practical Closure Examples

### 1. Data Privacy

```javascript
function createCounter() {
    let count = 0; // Private variable
    
    return {
        increment: function() {
            count++;
            return count;
        },
        decrement: function() {
            count--;
            return count;
        },
        getCount: function() {
            return count;
        }
    };
}

const counter = createCounter();
console.log(counter.increment()); // 1
console.log(counter.increment()); // 2
console.log(counter.getCount());  // 2
// console.log(counter.count); // undefined - count is private
```

### 2. Function Factories

```javascript
function createMultiplier(multiplier) {
    return function(x) {
        return x * multiplier;
    };
}

const double = createMultiplier(2);
const triple = createMultiplier(3);

console.log(double(5)); // 10
console.log(triple(5)); // 15
```

### 3. Module Pattern

```javascript
const myModule = (function() {
    let privateVariable = 0;
    
    function privateFunction() {
        console.log("This is private");
    }
    
    return {
        publicMethod: function() {
            privateVariable++;
            privateFunction();
            return privateVariable;
        },
        getPrivateVariable: function() {
            return privateVariable;
        }
    };
})();

console.log(myModule.publicMethod()); // "This is private", returns 1
console.log(myModule.getPrivateVariable()); // 1
```

## Understanding Prototypes

Every JavaScript object has a prototype, which is another object:

```javascript
// Constructor function
function Person(name, age) {
    this.name = name;
    this.age = age;
}

// Adding methods to the prototype
Person.prototype.greet = function() {
    return `Hello, I'm ${this.name} and I'm ${this.age} years old`;
};

Person.prototype.haveBirthday = function() {
    this.age++;
    return `Happy birthday! I'm now ${this.age}`;
};

// Creating instances
const person1 = new Person("Alice", 25);
const person2 = new Person("Bob", 30);

console.log(person1.greet()); // Hello, I'm Alice and I'm 25 years old
console.log(person2.haveBirthday()); // Happy birthday! I'm now 31
```

## Prototype Chain

Objects inherit from their prototype's prototype:

```javascript
// Base constructor
function Animal(name) {
    this.name = name;
}

Animal.prototype.speak = function() {
    return `${this.name} makes a sound`;
};

// Derived constructor
function Dog(name, breed) {
    Animal.call(this, name); // Call parent constructor
    this.breed = breed;
}

// Set up inheritance
Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;

// Add Dog-specific methods
Dog.prototype.bark = function() {
    return `${this.name} barks!`;
};

Dog.prototype.speak = function() {
    return `${this.name} barks loudly!`;
};

const myDog = new Dog("Buddy", "Golden Retriever");
console.log(myDog.speak()); // Buddy barks loudly!
console.log(myDog.bark());  // Buddy barks!
```

## Modern Class Syntax

ES6 classes provide syntactic sugar over prototypes:

```javascript
class Animal {
    constructor(name) {
        this.name = name;
    }
    
    speak() {
        return `${this.name} makes a sound`;
    }
}

class Dog extends Animal {
    constructor(name, breed) {
        super(name); // Call parent constructor
        this.breed = breed;
    }
    
    speak() {
        return `${this.name} barks loudly!`;
    }
    
    bark() {
        return `${this.name} barks!`;
    }
}

const myDog = new Dog("Max", "Labrador");
console.log(myDog.speak()); // Max barks loudly!
console.log(myDog instanceof Dog);    // true
console.log(myDog instanceof Animal); // true
```

## Advanced Closure Patterns

### Memoization

```javascript
function memoize(fn) {
    const cache = {};
    
    return function(...args) {
        const key = JSON.stringify(args);
        
        if (key in cache) {
            console.log('Cache hit');
            return cache[key];
        }
        
        console.log('Computing...');
        const result = fn.apply(this, args);
        cache[key] = result;
        return result;
    };
}

const expensiveFunction = memoize(function(n) {
    let result = 0;
    for (let i = 0; i < n * 1000000; i++) {
        result += i;
    }
    return result;
});

console.log(expensiveFunction(100)); // Computing... (takes time)
console.log(expensiveFunction(100)); // Cache hit (instant)
```

## Quiz

1. What is a closure in JavaScript?
   a) A way to close functions
   b) A function that has access to variables in its outer scope
   c) A type of loop
   d) A method to hide code

2. What is the prototype chain?
   a) A chain of functions
   b) The mechanism by which objects inherit properties and methods
   c) A way to connect databases
   d) A debugging tool

3. What does `Object.create()` do?
   a) Creates a new object with the specified prototype
   b) Copies an existing object
   c) Deletes an object
   d) Converts objects to strings

**Answers: 1-b, 2-b, 3-a**

## Summary

In this lesson, you learned:
- How closures work and their practical applications
- Using closures for data privacy and function factories
- Understanding JavaScript's prototype-based inheritance
- The prototype chain and how inheritance works
- Modern class syntax as syntactic sugar over prototypes
- Advanced patterns like memoization using closures

These concepts are fundamental to understanding how JavaScript works under the hood!
""",
                    'topics': ['closures', 'prototypes', 'inheritance', 'lexical_scope', 'design_patterns']
                }
            }
        }
    }
    
    @classmethod
    def generate_personalized_lessons(cls, user_id: str, subject: str) -> Dict[str, Any]:
        """
        Generate personalized lessons based on user's survey results
        
        Args:
            user_id: The user ID
            subject: The subject for lesson generation
            
        Returns:
            Dictionary containing lesson generation results
            
        Raises:
            ValueError: If subject is not supported or survey results not found
            FileNotFoundError: If survey results don't exist
        """
        logger.info(f"Generating personalized lessons for user {user_id}, subject {subject}")
        
        # Validate subject
        if subject not in cls.LESSON_TEMPLATES:
            raise ValueError(f"Subject '{subject}' is not supported for lesson generation")
        
        # Get survey analysis results
        survey_results = SurveyAnalysisService.get_survey_results(user_id, subject)
        if not survey_results:
            raise FileNotFoundError(f"Survey results not found for user {user_id}, subject {subject}")
        
        skill_level = survey_results['skill_level']
        topic_analysis = survey_results['topic_analysis']
        
        logger.info(f"User skill level: {skill_level}")
        logger.info(f"Strong topics: {topic_analysis.get('strengths', [])}")
        logger.info(f"Weak topics: {topic_analysis.get('weaknesses', [])}")
        
        # Generate lesson plan based on skill level and topic analysis
        lesson_plan = cls._create_lesson_plan(subject, skill_level, topic_analysis)
        
        # Generate individual lessons
        lessons = []
        for i, lesson_config in enumerate(lesson_plan, 1):
            lesson_content = cls._generate_lesson_content(
                lesson_config, 
                skill_level, 
                topic_analysis,
                lesson_number=i
            )
            lessons.append(lesson_content)
        
        # Create lesson metadata
        lesson_metadata = {
            'user_id': user_id,
            'subject': subject,
            'skill_level': skill_level,
            'total_lessons': len(lessons),
            'generated_at': datetime.utcnow().isoformat(),
            'topic_analysis': topic_analysis,
            'lesson_plan': lesson_plan,
            'lessons': [
                {
                    'lesson_number': lesson['lesson_number'],
                    'title': lesson['title'],
                    'estimated_time': lesson['estimated_time'],
                    'topics': lesson['topics'],
                    'difficulty': lesson['difficulty']
                }
                for lesson in lessons
            ]
        }
        
        return {
            'lessons': lessons,
            'metadata': lesson_metadata
        }
    
    @classmethod
    def _create_lesson_plan(cls, subject: str, skill_level: str, topic_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a personalized lesson plan based on skill level and topic analysis"""
        available_templates = cls.LESSON_TEMPLATES[subject]
        strengths = set(topic_analysis.get('strengths', []))
        weaknesses = set(topic_analysis.get('weaknesses', []))
        
        lesson_plan = []
        
        # Start with appropriate skill level lessons
        primary_templates = available_templates.get(skill_level, {})
        
        # Add lessons from current skill level
        for topic_key, template in primary_templates.items():
            lesson_config = template.copy()
            lesson_config['topic_key'] = topic_key
            lesson_config['difficulty'] = skill_level
            lesson_config['priority'] = cls._calculate_lesson_priority(template, strengths, weaknesses)
            lesson_plan.append(lesson_config)
        
        # Add lessons from other skill levels if needed to reach 5 lessons
        if len(lesson_plan) < 5:
            # Add from higher skill level if user is doing well
            if skill_level == 'beginner' and len(strengths) > len(weaknesses):
                intermediate_templates = available_templates.get('intermediate', {})
                for topic_key, template in intermediate_templates.items():
                    if len(lesson_plan) >= 10:
                        break
                    lesson_config = template.copy()
                    lesson_config['topic_key'] = topic_key
                    lesson_config['difficulty'] = 'intermediate'
                    lesson_config['priority'] = cls._calculate_lesson_priority(template, strengths, weaknesses)
                    lesson_plan.append(lesson_config)
            
            # Add from lower skill level if user has many weaknesses
            elif skill_level in ['intermediate', 'advanced'] and len(weaknesses) > len(strengths):
                beginner_templates = available_templates.get('beginner', {})
                for topic_key, template in beginner_templates.items():
                    if len(lesson_plan) >= 10:
                        break
                    lesson_config = template.copy()
                    lesson_config['topic_key'] = topic_key
                    lesson_config['difficulty'] = 'beginner'
                    lesson_config['priority'] = cls._calculate_lesson_priority(template, strengths, weaknesses)
                    lesson_plan.append(lesson_config)
        
        # Sort by priority (higher priority first) and limit to 5 lessons
        lesson_plan.sort(key=lambda x: x['priority'], reverse=True)
        return lesson_plan[:5]
    
    @classmethod
    def _calculate_lesson_priority(cls, template: Dict[str, Any], strengths: set, weaknesses: set) -> float:
        """Calculate priority score for a lesson based on user's strengths and weaknesses"""
        template_topics = set(template.get('topics', []))
        
        # Higher priority for lessons covering weak topics
        weakness_overlap = len(template_topics.intersection(weaknesses))
        strength_overlap = len(template_topics.intersection(strengths))
        
        # Base priority
        priority = 5.0
        
        # Boost priority for lessons covering weaknesses
        priority += weakness_overlap * 2.0
        
        # Slightly reduce priority for lessons covering only strengths
        if strength_overlap > 0 and weakness_overlap == 0:
            priority -= 1.0
        
        return priority
    
    @classmethod
    def _generate_lesson_content(cls, lesson_config: Dict[str, Any], skill_level: str, 
                               topic_analysis: Dict[str, Any], lesson_number: int) -> Dict[str, Any]:
        """Generate the actual lesson content based on configuration"""
        
        # Get base content from template
        base_content = lesson_config['content_template']
        
        # Customize content based on user's analysis
        customized_content = cls._customize_content_for_user(
            base_content, 
            skill_level, 
            topic_analysis,
            lesson_config
        )
        
        lesson = {
            'lesson_number': lesson_number,
            'title': lesson_config['title'],
            'estimated_time': lesson_config['estimated_time'],
            'difficulty': lesson_config['difficulty'],
            'topics': lesson_config['topics'],
            'prerequisites': lesson_config.get('prerequisites', []),
            'content': customized_content,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return lesson
    
    @classmethod
    def _customize_content_for_user(cls, base_content: str, skill_level: str, 
                                  topic_analysis: Dict[str, Any], lesson_config: Dict[str, Any]) -> str:
        """Customize lesson content based on user's skill level and topic analysis"""
        
        strengths = topic_analysis.get('strengths', [])
        weaknesses = topic_analysis.get('weaknesses', [])
        lesson_topics = lesson_config.get('topics', [])
        
        # Add personalized introduction
        personalized_intro = cls._generate_personalized_intro(skill_level, strengths, weaknesses, lesson_topics)
        
        # Add personalized conclusion
        personalized_conclusion = cls._generate_personalized_conclusion(skill_level, strengths, weaknesses, lesson_topics)
        
        # Insert personalized sections
        customized_content = base_content.replace(
            "## Introduction",
            f"## Introduction\n\n{personalized_intro}\n\n## Lesson Overview"
        )
        
        customized_content = customized_content.replace(
            "## Summary",
            f"{personalized_conclusion}\n\n## Summary"
        )
        
        return customized_content
    
    @classmethod
    def _generate_personalized_intro(cls, skill_level: str, strengths: List[str], 
                                   weaknesses: List[str], lesson_topics: List[str]) -> str:
        """Generate a personalized introduction based on user's profile"""
        
        intro_parts = []
        
        # Acknowledge skill level
        if skill_level == 'beginner':
            intro_parts.append("As someone new to programming, this lesson will build on fundamental concepts step by step.")
        elif skill_level == 'intermediate':
            intro_parts.append("Building on your existing programming knowledge, this lesson will deepen your understanding.")
        else:  # advanced
            intro_parts.append("As an advanced learner, this lesson will explore sophisticated concepts and best practices.")
        
        # Address strengths
        relevant_strengths = [s for s in strengths if s in lesson_topics]
        if relevant_strengths:
            intro_parts.append(f"I noticed you're already strong in {', '.join(relevant_strengths)}, so we'll build on that foundation.")
        
        # Address weaknesses
        relevant_weaknesses = [w for w in weaknesses if w in lesson_topics]
        if relevant_weaknesses:
            intro_parts.append(f"This lesson will help strengthen your understanding of {', '.join(relevant_weaknesses)}.")
        
        return " ".join(intro_parts)
    
    @classmethod
    def _generate_personalized_conclusion(cls, skill_level: str, strengths: List[str], 
                                        weaknesses: List[str], lesson_topics: List[str]) -> str:
        """Generate a personalized conclusion with next steps"""
        
        conclusion_parts = []
        
        # Acknowledge progress
        conclusion_parts.append("Great work completing this lesson!")
        
        # Provide skill-level appropriate encouragement
        if skill_level == 'beginner':
            conclusion_parts.append("You're building a solid foundation in programming concepts.")
        elif skill_level == 'intermediate':
            conclusion_parts.append("You're developing more sophisticated programming skills.")
        else:  # advanced
            conclusion_parts.append("You're mastering advanced programming concepts.")
        
        # Suggest practice based on weaknesses
        relevant_weaknesses = [w for w in weaknesses if w in lesson_topics]
        if relevant_weaknesses:
            conclusion_parts.append(f"Consider practicing more with {', '.join(relevant_weaknesses)} to reinforce your learning.")
        
        return " ".join(conclusion_parts)
    
    @classmethod
    def get_supported_subjects(cls) -> List[str]:
        """Get list of subjects supported for lesson generation"""
        return list(cls.LESSON_TEMPLATES.keys())
    
    @classmethod
    def validate_lesson_structure(cls, lesson: Dict[str, Any]) -> bool:
        """
        Validate that a lesson has the correct structure
        
        Args:
            lesson: Lesson dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'lesson_number', 'title', 'estimated_time', 'difficulty',
            'topics', 'content', 'generated_at'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in lesson:
                logger.error(f"Lesson missing required field: {field}")
                return False
        
        # Validate lesson number
        if not isinstance(lesson['lesson_number'], int) or lesson['lesson_number'] < 1:
            logger.error(f"Invalid lesson number: {lesson['lesson_number']}")
            return False
        
        # Validate difficulty
        if lesson['difficulty'] not in ['beginner', 'intermediate', 'advanced']:
            logger.error(f"Invalid difficulty level: {lesson['difficulty']}")
            return False
        
        # Validate content is not empty
        if not lesson['content'] or not isinstance(lesson['content'], str):
            logger.error("Lesson content must be a non-empty string")
            return False
        
        return True