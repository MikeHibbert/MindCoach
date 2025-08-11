# MindCoach API Documentation

This document provides comprehensive documentation for the MindCoach REST API, including endpoint descriptions, request/response schemas, authentication requirements, and usage examples.

## Base URL

```
Development: http://localhost:5000/api
Production: https://api.mindcoach.com/api
```

## Authentication

MindCoach uses a user ID-based authentication system with plans to implement JWT tokens and OAuth2 in future versions.

### Authentication Methods

#### Current: User ID Authentication
```http
Content-Type: application/json
User-ID: <user_id>
```

#### Future: JWT Token Authentication (Planned)
```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

#### Future: OAuth2 Authentication (Planned)
```http
Content-Type: application/json
Authorization: Bearer <oauth_access_token>
```

### Authentication Requirements by Endpoint

| Endpoint Category | Authentication Required | Additional Requirements |
|------------------|------------------------|------------------------|
| User Management | User-ID header | User must exist in database |
| Subject Selection | User-ID header | Valid user account |
| Survey System | User-ID header | Subject selection required |
| Content Generation | User-ID header | Active subscription required |
| Lesson Access | User-ID header | Active subscription required |
| Subscription Management | User-ID header | User ownership verification |

### Authentication Error Responses

#### Missing Authentication
```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "User-ID header is required",
    "details": {
      "required_headers": ["User-ID"],
      "documentation": "/docs/api#authentication"
    }
  }
}
```

#### Invalid User ID
```json
{
  "success": false,
  "error": {
    "code": "INVALID_USER_ID",
    "message": "User ID not found or invalid",
    "details": {
      "user_id": "provided_user_id",
      "suggestion": "Create user account first"
    }
  }
}
```

#### Insufficient Permissions
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "User does not have permission to access this resource",
    "details": {
      "required_permission": "subscription_access",
      "user_permissions": ["basic_access"]
    }
  }
}
```

### Security Considerations

#### API Key Management (Future)
- API keys will be environment-specific (development, staging, production)
- Keys will have configurable expiration times
- Rate limiting will be applied per API key
- Key rotation will be supported for security

#### Request Signing (Future)
- HMAC-SHA256 request signing for sensitive operations
- Timestamp validation to prevent replay attacks
- Nonce validation for additional security
- Signature verification on server side

#### IP Whitelisting (Enterprise)
- Restrict API access to specific IP addresses
- Support for IP ranges and CIDR notation
- Configurable per user or organization
- Audit logging for access attempts

## Response Format

All API responses follow a consistent JSON format:

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error details
    }
  }
}
```

## HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for processing |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation errors |
| 500 | Internal Server Error | Server error |

## API Endpoints

### User Management

#### Create User
Creates a new user account in the system.

```http
POST /api/users
```

**Request Body:**
```json
{
  "user_id": "john_doe_123",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": "john_doe_123",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "message": "User created successfully"
}
```

**Error Responses:**
- `409 Conflict`: User ID already exists
- `422 Unprocessable Entity`: Invalid email format

#### Get User Profile
Retrieves user profile information.

```http
GET /api/users/{user_id}
```

**Path Parameters:**
- `user_id` (string): Unique user identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": "john_doe_123",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "subscriptions": [
      {
        "subject": "python",
        "status": "active",
        "expires_at": "2024-02-15T10:30:00Z"
      }
    ]
  }
}
```

#### Update User Profile
Updates user profile information.

```http
PUT /api/users/{user_id}
```

**Request Body:**
```json
{
  "email": "newemail@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": "john_doe_123",
    "email": "newemail@example.com",
    "updated_at": "2024-01-15T11:00:00Z"
  },
  "message": "User updated successfully"
}
```

### Subject Management

#### List Available Subjects
Retrieves all available programming subjects.

```http
GET /api/subjects
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subjects": [
      {
        "id": "python",
        "name": "Python Programming",
        "description": "Learn Python from basics to advanced concepts",
        "difficulty_levels": ["beginner", "intermediate", "advanced"],
        "estimated_duration": "40 hours",
        "prerequisites": [],
        "price": 29.99
      },
      {
        "id": "javascript",
        "name": "JavaScript Development",
        "description": "Modern JavaScript for web development",
        "difficulty_levels": ["beginner", "intermediate", "advanced"],
        "estimated_duration": "35 hours",
        "prerequisites": ["html", "css"],
        "price": 29.99
      }
    ]
  }
}
```

#### Select Subject
Records user's subject selection.

```http
POST /api/users/{user_id}/subjects/{subject}/select
```

**Path Parameters:**
- `user_id` (string): Unique user identifier
- `subject` (string): Subject identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "selected_subject": "python",
    "selected_at": "2024-01-15T10:35:00Z",
    "subscription_required": false
  },
  "message": "Subject selected successfully"
}
```

#### Check Subject Access Status
Verifies if user has access to a specific subject.

```http
GET /api/users/{user_id}/subjects/{subject}/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subject": "python",
    "has_access": true,
    "subscription_status": "active",
    "expires_at": "2024-02-15T10:30:00Z"
  }
}
```

### Survey System

#### Generate Survey
Creates an AI-generated assessment survey for a specific subject.

```http
POST /api/users/{user_id}/subjects/{subject}/survey/generate
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "survey_gen_12345",
    "status": "started",
    "estimated_completion": "30 seconds"
  },
  "message": "Survey generation started"
}
```

#### Get Survey Status
Checks the status of survey generation.

```http
GET /api/users/{user_id}/subjects/{subject}/survey/status/{task_id}
```

**Response (In Progress):**
```json
{
  "success": true,
  "data": {
    "task_id": "survey_gen_12345",
    "status": "in_progress",
    "progress": 75,
    "stage": "question_generation"
  }
}
```

**Response (Completed):**
```json
{
  "success": true,
  "data": {
    "task_id": "survey_gen_12345",
    "status": "completed",
    "survey_id": "survey_67890"
  }
}
```

#### Get Survey Questions
Retrieves generated survey questions.

```http
GET /api/users/{user_id}/subjects/{subject}/survey
```

**Response:**
```json
{
  "success": true,
  "data": {
    "survey_id": "survey_67890",
    "subject": "python",
    "questions": [
      {
        "id": 1,
        "question": "What is the correct way to define a function in Python?",
        "type": "multiple_choice",
        "options": [
          "function myFunc():",
          "def myFunc():",
          "func myFunc():",
          "define myFunc():"
        ],
        "difficulty": "beginner"
      },
      {
        "id": 2,
        "question": "Which data structure is ordered and mutable in Python?",
        "type": "multiple_choice",
        "options": [
          "tuple",
          "set",
          "list",
          "dictionary"
        ],
        "difficulty": "beginner"
      }
    ],
    "total_questions": 8,
    "estimated_time": "10 minutes"
  }
}
```

#### Submit Survey Answers
Submits user's survey responses for analysis.

```http
POST /api/users/{user_id}/subjects/{subject}/survey/submit
```

**Request Body:**
```json
{
  "survey_id": "survey_67890",
  "answers": [
    {
      "question_id": 1,
      "answer": "def myFunc():"
    },
    {
      "question_id": 2,
      "answer": "list"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "submission_id": "sub_98765",
    "total_questions": 8,
    "answered_questions": 8,
    "processing_status": "analyzing"
  },
  "message": "Survey submitted successfully"
}
```

#### Get Survey Results
Retrieves analyzed survey results and skill level assessment.

```http
GET /api/users/{user_id}/subjects/{subject}/survey/results
```

**Response:**
```json
{
  "success": true,
  "data": {
    "survey_id": "survey_67890",
    "submission_id": "sub_98765",
    "skill_level": "intermediate",
    "score": 75,
    "analysis": {
      "strengths": [
        "Basic syntax and functions",
        "Data structures understanding"
      ],
      "areas_for_improvement": [
        "Object-oriented programming",
        "Error handling"
      ],
      "recommended_topics": [
        "Classes and objects",
        "Exception handling",
        "File operations"
      ]
    },
    "completed_at": "2024-01-15T10:45:00Z"
  }
}
```

### Content Generation Pipeline

#### Start Content Generation
Initiates the three-stage LangChain pipeline for personalized content creation.

```http
POST /api/users/{user_id}/subjects/{subject}/content/generate
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "content_gen_54321",
    "pipeline_stages": [
      "curriculum_generation",
      "lesson_planning", 
      "content_generation"
    ],
    "estimated_completion": "3-5 minutes"
  },
  "message": "Content generation pipeline started"
}
```

#### Get Content Generation Status
Monitors the progress of the content generation pipeline.

```http
GET /api/users/{user_id}/subjects/{subject}/content/status/{task_id}
```

**Response (Stage 1 - Curriculum Generation):**
```json
{
  "success": true,
  "data": {
    "task_id": "content_gen_54321",
    "overall_status": "in_progress",
    "current_stage": "curriculum_generation",
    "stage_progress": 100,
    "overall_progress": 33,
    "stages": {
      "curriculum_generation": {
        "status": "completed",
        "completed_at": "2024-01-15T11:00:00Z"
      },
      "lesson_planning": {
        "status": "in_progress",
        "progress": 0
      },
      "content_generation": {
        "status": "pending"
      }
    }
  }
}
```

**Response (Stage 3 - Content Generation):**
```json
{
  "success": true,
  "data": {
    "task_id": "content_gen_54321",
    "overall_status": "in_progress",
    "current_stage": "content_generation",
    "stage_progress": 60,
    "overall_progress": 87,
    "stages": {
      "curriculum_generation": {
        "status": "completed",
        "completed_at": "2024-01-15T11:00:00Z"
      },
      "lesson_planning": {
        "status": "completed",
        "completed_at": "2024-01-15T11:02:00Z"
      },
      "content_generation": {
        "status": "in_progress",
        "lessons_completed": 6,
        "total_lessons": 10,
        "current_lesson": "Object-Oriented Programming Basics"
      }
    }
  }
}
```

**Response (Completed):**
```json
{
  "success": true,
  "data": {
    "task_id": "content_gen_54321",
    "overall_status": "completed",
    "completed_at": "2024-01-15T11:05:00Z",
    "results": {
      "curriculum_id": "curr_11111",
      "lesson_plan_id": "plan_22222",
      "total_lessons": 10,
      "estimated_duration": "25 hours"
    }
  }
}
```

### Curriculum Management

#### Get Curriculum Scheme
Retrieves the generated learning curriculum for a subject.

```http
GET /api/users/{user_id}/subjects/{subject}/curriculum
```

**Response:**
```json
{
  "success": true,
  "data": {
    "curriculum_id": "curr_11111",
    "subject": "python",
    "skill_level": "intermediate",
    "total_lessons": 10,
    "estimated_duration": "25 hours",
    "learning_objectives": [
      "Master Python fundamentals and syntax",
      "Understand object-oriented programming concepts",
      "Build practical applications with Python"
    ],
    "topics": [
      {
        "lesson_id": 1,
        "title": "Advanced Variables and Data Types",
        "topics": ["dictionaries", "sets", "type_hints"],
        "prerequisites": [],
        "difficulty": "intermediate",
        "estimated_time": "2.5 hours"
      },
      {
        "lesson_id": 2,
        "title": "Functions and Scope",
        "topics": ["function_parameters", "lambda_functions", "decorators"],
        "prerequisites": [1],
        "difficulty": "intermediate",
        "estimated_time": "3 hours"
      }
    ],
    "generated_at": "2024-01-15T11:00:00Z"
  }
}
```

#### Get Lesson Plans
Retrieves detailed lesson plans for the curriculum.

```http
GET /api/users/{user_id}/subjects/{subject}/lesson-plans
```

**Response:**
```json
{
  "success": true,
  "data": {
    "lesson_plan_id": "plan_22222",
    "curriculum_id": "curr_11111",
    "lesson_plans": [
      {
        "lesson_id": 1,
        "title": "Advanced Variables and Data Types",
        "learning_objectives": [
          "Understand complex data structures in Python",
          "Apply type hints for better code documentation",
          "Master dictionary and set operations"
        ],
        "structure": {
          "introduction": "5 minutes",
          "main_content": "20 minutes",
          "examples": "10 minutes",
          "exercises": "15 minutes",
          "summary": "5 minutes"
        },
        "activities": [
          "Interactive dictionary manipulation exercises",
          "Type hint implementation practice",
          "Set operations and use cases"
        ],
        "assessment": {
          "type": "practical_exercises",
          "count": 3,
          "difficulty": "intermediate"
        }
      }
    ],
    "generated_at": "2024-01-15T11:02:00Z"
  }
}
```

### Lesson Management

#### List User Lessons
Retrieves all generated lessons for a user's subject.

```http
GET /api/users/{user_id}/subjects/{subject}/lessons
```

**Query Parameters:**
- `page` (integer, optional): Page number for pagination (default: 1)
- `limit` (integer, optional): Number of lessons per page (default: 10)
- `status` (string, optional): Filter by completion status (`completed`, `in_progress`, `not_started`)

**Response:**
```json
{
  "success": true,
  "data": {
    "lessons": [
      {
        "lesson_id": 1,
        "title": "Advanced Variables and Data Types",
        "status": "completed",
        "progress": 100,
        "difficulty": "intermediate",
        "estimated_time": "2.5 hours",
        "completed_at": "2024-01-15T12:00:00Z"
      },
      {
        "lesson_id": 2,
        "title": "Functions and Scope",
        "status": "in_progress",
        "progress": 60,
        "difficulty": "intermediate",
        "estimated_time": "3 hours",
        "started_at": "2024-01-15T13:00:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_lessons": 10,
      "lessons_per_page": 10
    },
    "summary": {
      "completed": 1,
      "in_progress": 1,
      "not_started": 8,
      "total_progress": 16
    }
  }
}
```

#### Get Individual Lesson
Retrieves complete content for a specific lesson.

```http
GET /api/users/{user_id}/subjects/{subject}/lessons/{lesson_id}
```

**Path Parameters:**
- `lesson_id` (integer): Lesson identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "lesson_id": 1,
    "title": "Advanced Variables and Data Types",
    "content": "# Advanced Variables and Data Types\n\n## Learning Objectives\n...",
    "content_type": "markdown",
    "metadata": {
      "difficulty": "intermediate",
      "estimated_time": "2.5 hours",
      "prerequisites": [],
      "learning_objectives": [
        "Understand complex data structures in Python",
        "Apply type hints for better code documentation"
      ]
    },
    "progress": {
      "status": "completed",
      "completion_percentage": 100,
      "time_spent": "2.3 hours",
      "exercises_completed": 3,
      "total_exercises": 3
    },
    "navigation": {
      "previous_lesson": null,
      "next_lesson": {
        "lesson_id": 2,
        "title": "Functions and Scope"
      }
    }
  }
}
```

#### Update Lesson Progress
Records user progress on a specific lesson.

```http
PUT /api/users/{user_id}/subjects/{subject}/lessons/{lesson_id}/progress
```

**Request Body:**
```json
{
  "completion_percentage": 75,
  "time_spent": 90,
  "exercises_completed": 2,
  "status": "in_progress"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "lesson_id": 1,
    "progress": {
      "status": "in_progress",
      "completion_percentage": 75,
      "time_spent": "1.5 hours",
      "exercises_completed": 2,
      "total_exercises": 3,
      "updated_at": "2024-01-15T14:30:00Z"
    }
  },
  "message": "Progress updated successfully"
}
```

### LangChain-Powered Content Generation

The MindCoach platform now includes advanced AI-powered content generation using LangChain and xAI's Grok-3 Mini model. This provides personalized, high-quality educational content through a sophisticated three-stage pipeline.

#### Generate Lessons with LangChain Pipeline
Starts the AI-powered lesson generation pipeline that creates personalized curriculum, lesson plans, and content.

```http
POST /api/users/{user_id}/subjects/{subject}/lessons/generate-langchain
```

**Prerequisites:**
- User must have completed the subject survey
- Active subscription required for the subject

**Response:**
```json
{
  "success": true,
  "pipeline_id": "user123_python_1705320000",
  "message": "LangChain lesson generation started for python",
  "generation_method": "langchain",
  "status": "started",
  "details": {
    "user_id": "user123",
    "subject": "python",
    "skill_level": "intermediate",
    "total_stages": 3
  }
}
```

**Status Code:** `202 Accepted` - Pipeline started successfully

#### Get Pipeline Status
Monitors the progress of the LangChain content generation pipeline.

```http
GET /api/users/{user_id}/subjects/{subject}/lessons/pipeline-status/{pipeline_id}
```

**Path Parameters:**
- `pipeline_id` (string): Pipeline identifier returned from generation request

**Response:**
```json
{
  "success": true,
  "pipeline_id": "user123_python_1705320000",
  "pipeline_status": {
    "user_id": "user123",
    "subject": "python",
    "current_stage": "content_generation",
    "status": "in_progress",
    "progress_percentage": 75.0,
    "stages_completed": 2,
    "total_stages": 3,
    "current_step": "Generating lesson 3 content (3/10)",
    "started_at": "2024-01-15T10:00:00Z",
    "estimated_completion": "2024-01-15T10:15:00Z"
  }
}
```

**Pipeline Stages:**
1. `curriculum_generation` - Creates personalized curriculum scheme
2. `lesson_planning` - Develops detailed lesson plans
3. `content_generation` - Generates complete lesson content

**Pipeline Status Values:**
- `in_progress` - Pipeline is actively running
- `completed` - All stages completed successfully
- `failed` - Pipeline encountered an error
- `cancelled` - Pipeline was cancelled by user

#### Cancel Pipeline
Cancels a running LangChain content generation pipeline.

```http
POST /api/users/{user_id}/subjects/{subject}/lessons/pipeline-cancel/{pipeline_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Pipeline cancelled successfully",
  "pipeline_id": "user123_python_1705320000",
  "status": "cancelled"
}
```

#### Get Curriculum Scheme
Retrieves the AI-generated curriculum scheme created by the LangChain pipeline.

```http
GET /api/users/{user_id}/subjects/{subject}/curriculum
```

**Response:**
```json
{
  "success": true,
  "curriculum": {
    "curriculum": {
      "subject": "python",
      "skill_level": "intermediate",
      "total_lessons": 10,
      "learning_objectives": [
        "Master intermediate Python programming concepts",
        "Build practical applications using Python",
        "Understand object-oriented programming principles"
      ],
      "topics": [
        {
          "lesson_id": 1,
          "title": "Advanced Data Structures",
          "topics": ["dictionaries", "sets", "comprehensions"],
          "prerequisites": ["basic_python"],
          "difficulty": "intermediate",
          "estimated_duration": "60 minutes"
        },
        {
          "lesson_id": 2,
          "title": "Object-Oriented Programming",
          "topics": ["classes", "inheritance", "polymorphism"],
          "prerequisites": ["functions", "data_structures"],
          "difficulty": "intermediate",
          "estimated_duration": "75 minutes"
        }
      ]
    },
    "generated_at": "2024-01-15T10:01:00Z",
    "generation_stage": "curriculum_complete"
  },
  "message": "Curriculum scheme retrieved successfully"
}
```

#### Get Lesson Plans
Retrieves the detailed lesson plans generated by the LangChain pipeline.

```http
GET /api/users/{user_id}/subjects/{subject}/lesson-plans
```

**Response:**
```json
{
  "success": true,
  "lesson_plans": {
    "lesson_plans": [
      {
        "lesson_id": 1,
        "title": "Advanced Data Structures",
        "learning_objectives": [
          "Understand and use Python dictionaries effectively",
          "Master set operations and use cases",
          "Create and optimize list/dict comprehensions"
        ],
        "structure": {
          "introduction": "5 minutes",
          "main_content": "25 minutes",
          "examples": "15 minutes",
          "exercises": "15 minutes",
          "summary": "5 minutes"
        },
        "activities": [
          "Interactive demonstration of dictionary methods",
          "Guided practice with set operations",
          "Independent coding challenges with comprehensions"
        ],
        "assessment": "Coding exercises and practical application tasks",
        "materials_needed": [
          "Python interpreter or IDE",
          "Code examples repository",
          "Practice dataset"
        ],
        "key_concepts": [
          "dictionary_methods",
          "set_operations",
          "comprehensions"
        ]
      }
    ],
    "generated_at": "2024-01-15T10:02:00Z",
    "generation_stage": "lesson_plans_complete"
  },
  "message": "Lesson plans retrieved successfully"
}
```

#### Get LangChain-Generated Lesson
Retrieves individual lesson content generated by the LangChain pipeline.

```http
GET /api/users/{user_id}/subjects/{subject}/lessons/{lesson_id}/langchain
```

**Path Parameters:**
- `lesson_id` (integer): Lesson identifier

**Response:**
```json
{
  "success": true,
  "lesson": {
    "lesson_id": 1,
    "user_id": "user123",
    "subject": "python",
    "content": "# Advanced Data Structures\n\n## Introduction\n\nWelcome to our lesson on advanced Python data structures...\n\n## Key Concepts\n\n### Dictionaries\n\nDictionaries are mutable, unordered collections...\n\n```python\n# Example: Creating and using dictionaries\nstudent = {\n    'name': 'Alice',\n    'age': 22,\n    'courses': ['Python', 'Data Science']\n}\n```\n\n## Hands-on Exercises\n\n### Exercise 1: Dictionary Operations\n\nCreate a program that manages a simple inventory system...",
    "metadata": {
      "user_id": "user123",
      "subject": "python",
      "lesson_id": "1",
      "generated_at": "2024-01-15T10:03:00Z",
      "generation_method": "langchain"
    },
    "generation_method": "langchain",
    "retrieved_at": "2024-01-15T10:03:00Z"
  }
}
```

### Subscription Management

#### List User Subscriptions
Retrieves all subscriptions for a user.

```http
GET /api/users/{user_id}/subscriptions
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subscriptions": [
      {
        "id": 1,
        "subject": "python",
        "status": "active",
        "purchased_at": "2024-01-15T10:30:00Z",
        "expires_at": "2024-02-15T10:30:00Z",
        "price_paid": 29.99,
        "currency": "USD"
      },
      {
        "id": 2,
        "subject": "javascript",
        "status": "expired",
        "purchased_at": "2023-12-01T10:30:00Z",
        "expires_at": "2024-01-01T10:30:00Z",
        "price_paid": 29.99,
        "currency": "USD"
      }
    ],
    "summary": {
      "active_subscriptions": 1,
      "expired_subscriptions": 1,
      "total_spent": 59.98
    }
  }
}
```

#### Purchase Subject Subscription
Creates a new subscription for a specific subject.

```http
POST /api/users/{user_id}/subscriptions/{subject}
```

**Request Body:**
```json
{
  "payment_method": "credit_card",
  "payment_token": "tok_1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subscription_id": 3,
    "subject": "react",
    "status": "active",
    "purchased_at": "2024-01-15T15:00:00Z",
    "expires_at": "2024-02-15T15:00:00Z",
    "price_paid": 29.99,
    "currency": "USD",
    "payment_confirmation": "pay_abcdef123456"
  },
  "message": "Subscription purchased successfully"
}
```

#### Cancel Subscription
Cancels an active subscription.

```http
DELETE /api/users/{user_id}/subscriptions/{subject}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subscription_id": 1,
    "subject": "python",
    "status": "cancelled",
    "cancelled_at": "2024-01-15T16:00:00Z",
    "refund_amount": 15.00,
    "refund_status": "processing"
  },
  "message": "Subscription cancelled successfully"
}
```

## Error Handling

### Common Error Responses

#### Validation Errors
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field_errors": {
        "email": ["Invalid email format"],
        "user_id": ["User ID must be between 3 and 50 characters"]
      }
    }
  }
}
```

#### Resource Not Found
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": {
      "resource_type": "user",
      "resource_id": "nonexistent_user"
    }
  }
}
```

#### Subscription Required
```json
{
  "success": false,
  "error": {
    "code": "SUBSCRIPTION_REQUIRED",
    "message": "Active subscription required to access this subject",
    "details": {
      "subject": "python",
      "subscription_url": "/api/users/john_doe/subscriptions/python"
    }
  }
}
```

#### Rate Limiting
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 60,
      "limit": 100,
      "window": "1 hour"
    }
  }
}
```

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| User Management | 100 requests | 1 hour |
| Survey Generation | 10 requests | 1 hour |
| Content Generation | 5 requests | 1 hour |
| Lesson Access | 1000 requests | 1 hour |
| General API | 500 requests | 1 hour |

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642262400
```

### RAG Document Management

The RAG (Retrieval-Augmented Generation) document management system provides administrative control over the documents that guide the LangChain content generation pipeline. These endpoints are designed for administrators to manage content guidelines, templates, and versioning.

#### List Available RAG Documents
Retrieves all available RAG documents in the system.

```http
GET /api/rag-docs
```

**Response:**
```json
{
  "status": "success",
  "available_documents": {
    "general": [
      "content_guidelines",
      "survey_guidelines", 
      "curriculum_guidelines",
      "lesson_plan_guidelines"
    ],
    "subjects": [
      "python",
      "javascript",
      "react"
    ]
  },
  "statistics": {
    "total_general_docs": 4,
    "total_subject_docs": 3,
    "cached_documents": 2,
    "available_subjects": ["python", "javascript", "react"],
    "rag_docs_path": "/app/rag_docs",
    "path_exists": true
  }
}
```

#### Get RAG Document
Retrieves the content of a specific RAG document.

```http
GET /api/rag-docs/{doc_type}
```

**Path Parameters:**
- `doc_type` (string): Document type (e.g., "content_guidelines", "survey_guidelines")

**Query Parameters:**
- `subject` (string, optional): Subject name for subject-specific templates

**Response:**
```json
{
  "status": "success",
  "document_type": "content_guidelines",
  "subject": null,
  "content": "# Content Guidelines for Lesson Generation\n\n## Lesson Structure Template\n\nEvery lesson should follow this structure...",
  "content_length": 2847
}
```

#### Validate RAG Document
Validates the structure and format of a RAG document.

```http
POST /api/rag-docs/{doc_type}/validate
```

**Request Body:**
```json
{
  "content": "# Content Guidelines\n\n## Lesson Structure Template\n\n```python\ncode example\n```",
  "subject": "python"
}
```

**Response:**
```json
{
  "status": "success",
  "document_type": "content_guidelines",
  "validation_results": {
    "has_content": true,
    "has_headers": true,
    "has_examples": true,
    "has_lesson_structure": true,
    "has_exercise_format": false,
    "proper_format": true,
    "is_valid": true
  },
  "is_valid": true
}
```

#### Get Documents for Pipeline Stage
Retrieves all RAG documents relevant to a specific pipeline stage.

```http
GET /api/rag-docs/stage/{stage}
```

**Path Parameters:**
- `stage` (string): Pipeline stage ("survey", "curriculum", "lesson_plans", "content")

**Query Parameters:**
- `subject` (string, optional): Subject name for subject-specific templates

**Response:**
```json
{
  "status": "success",
  "stage": "content",
  "subject": "python",
  "document_count": 2,
  "documents": [
    "# Content Guidelines for Lesson Generation...",
    "# Python Templates\n\n## Python-specific content..."
  ]
}
```

#### Get Document Version History
Retrieves the version history for a RAG document.

```http
GET /api/rag-docs/{doc_type}/versions
```

**Query Parameters:**
- `subject` (string, optional): Subject name for subject-specific documents

**Response:**
```json
{
  "status": "success",
  "document_type": "content_guidelines",
  "subject": null,
  "current_version": "1.2",
  "total_versions": 3,
  "versions": {
    "1.0": {
      "created_at": "2024-01-15T10:00:00Z",
      "description": "Initial version",
      "author": "system",
      "content_length": 2500
    },
    "1.1": {
      "created_at": "2024-01-15T11:00:00Z", 
      "description": "Added exercise guidelines",
      "author": "admin",
      "content_length": 2700
    },
    "1.2": {
      "created_at": "2024-01-15T12:00:00Z",
      "description": "Updated formatting standards",
      "author": "admin",
      "content_length": 2847
    }
  }
}
```

#### Get Specific Document Version
Retrieves a specific version of a RAG document.

```http
GET /api/rag-docs/{doc_type}/versions/{version}
```

**Path Parameters:**
- `version` (string): Version number (e.g., "1.0", "1.1")

**Query Parameters:**
- `subject` (string, optional): Subject name for subject-specific documents

**Response:**
```json
{
  "status": "success",
  "document_type": "content_guidelines",
  "subject": null,
  "version": "1.0",
  "content": "# Content Guidelines for Lesson Generation (Version 1.0)...",
  "content_length": 2500
}
```

#### Create New Document Version
Creates a new version of a RAG document.

```http
POST /api/rag-docs/{doc_type}/versions
```

**Request Body:**
```json
{
  "content": "# Updated Content Guidelines\n\n## New Section\n\nThis is the updated content...",
  "description": "Added new formatting guidelines",
  "author": "admin_user",
  "subject": null
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Created new version 1.3",
  "document_type": "content_guidelines",
  "subject": null,
  "new_version": "1.3",
  "description": "Added new formatting guidelines",
  "author": "admin_user"
}
```

**Status Code:** `201 Created`

#### Rollback Document Version
Rolls back a document to a previous version.

```http
POST /api/rag-docs/{doc_type}/rollback
```

**Request Body:**
```json
{
  "target_version": "1.1",
  "subject": null
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully rolled back to version 1.1",
  "document_type": "content_guidelines",
  "subject": null,
  "target_version": "1.1"
}
```

#### Compare Document Versions
Compares two versions of a RAG document.

```http
POST /api/rag-docs/{doc_type}/versions/compare
```

**Request Body:**
```json
{
  "version1": "1.1",
  "version2": "1.2",
  "subject": null
}
```

**Response:**
```json
{
  "status": "success",
  "comparison": {
    "document_type": "content_guidelines",
    "subject": null,
    "version1": "1.1",
    "version2": "1.2",
    "version1_length": 2700,
    "version2_length": 2847,
    "version1_lines": 95,
    "version2_lines": 98,
    "length_difference": 147,
    "lines_difference": 3,
    "identical": false
  }
}
```

#### Delete Document Version
Deletes a specific version of a RAG document (cannot delete current version).

```http
DELETE /api/rag-docs/{doc_type}/versions/{version}
```

**Request Body:**
```json
{
  "subject": null
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully deleted version 1.0",
  "document_type": "content_guidelines",
  "subject": null,
  "deleted_version": "1.0"
}
```

#### Clear Document Cache
Clears the RAG document cache to force reload from disk.

```http
POST /api/rag-docs/cache/clear
```

**Response:**
```json
{
  "status": "success",
  "message": "Document cache cleared successfully"
}
```

#### Reload Document
Reloads a specific RAG document from disk, bypassing cache.

```http
POST /api/rag-docs/{doc_type}/reload
```

**Request Body:**
```json
{
  "subject": null
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Document reloaded successfully: content_guidelines",
  "content_length": 2847
}
```

#### Get Document Statistics
Retrieves detailed statistics about RAG documents and validation status.

```http
GET /api/rag-docs/stats
```

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "total_general_docs": 4,
    "total_subject_docs": 3,
    "cached_documents": 5,
    "available_subjects": ["python", "javascript", "react"],
    "rag_docs_path": "/app/rag_docs",
    "path_exists": true,
    "versions_path": "/app/rag_docs/versions",
    "metadata_path": "/app/rag_docs/metadata"
  },
  "validation_summary": {
    "content_guidelines": true,
    "survey_guidelines": true,
    "curriculum_guidelines": false,
    "lesson_plan_guidelines": true
  },
  "total_valid_documents": 3,
  "total_invalid_documents": 1
}
```

### RAG Document Error Responses

#### Document Not Found
```json
{
  "status": "error",
  "message": "Document not found: nonexistent_doc"
}
```

#### Version Not Found
```json
{
  "status": "error", 
  "message": "Version 2.0 not found for document content_guidelines"
}
```

#### Validation Failed
```json
{
  "status": "error",
  "message": "Document content validation failed",
  "validation_results": {
    "has_content": true,
    "has_headers": false,
    "has_examples": false,
    "is_valid": false
  }
}
```

#### Cannot Delete Current Version
```json
{
  "status": "error",
  "message": "Failed to delete version 1.2. It may be the current version or not exist."
}
```

## Webhooks

MindCoach supports webhooks for real-time notifications of important events.

### Webhook Events

| Event | Description |
|-------|-------------|
| `user.created` | New user account created |
| `subscription.purchased` | Subject subscription purchased |
| `subscription.expired` | Subscription expired |
| `survey.completed` | User completed assessment survey |
| `content.generated` | Lesson content generation completed |
| `lesson.completed` | User completed a lesson |

### Webhook Payload Example
```json
{
  "event": "content.generated",
  "timestamp": "2024-01-15T11:05:00Z",
  "data": {
    "user_id": "john_doe_123",
    "subject": "python",
    "task_id": "content_gen_54321",
    "lessons_generated": 10,
    "generation_time": "4.5 minutes"
  }
}
```

### Webhook Configuration

#### Setting Up Webhooks
```http
POST /api/webhooks
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks/mindcoach",
  "events": ["content.generated", "subscription.purchased"],
  "secret": "your_webhook_secret",
  "active": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "webhook_id": "wh_12345",
    "url": "https://your-app.com/webhooks/mindcoach",
    "events": ["content.generated", "subscription.purchased"],
    "created_at": "2024-01-15T10:00:00Z",
    "active": true
  }
}
```

#### Webhook Security

All webhook payloads include a signature header for verification:

```http
X-MindCoach-Signature: sha256=<signature>
X-MindCoach-Timestamp: 1642262400
```

**Signature Verification (Node.js):**
```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  
  return `sha256=${expectedSignature}` === signature;
}
```

**Signature Verification (Python):**
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={expected_signature}" == signature
```

## Advanced API Features

### Batch Operations

#### Batch User Creation
```http
POST /api/users/batch
```

**Request Body:**
```json
{
  "users": [
    {
      "user_id": "user1",
      "email": "user1@example.com"
    },
    {
      "user_id": "user2", 
      "email": "user2@example.com"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "created": 2,
    "failed": 0,
    "results": [
      {
        "user_id": "user1",
        "status": "created",
        "id": 1
      },
      {
        "user_id": "user2",
        "status": "created", 
        "id": 2
      }
    ]
  }
}
```

#### Batch Lesson Progress Update
```http
PUT /api/users/{user_id}/subjects/{subject}/lessons/batch-progress
```

**Request Body:**
```json
{
  "updates": [
    {
      "lesson_id": 1,
      "completion_percentage": 100,
      "status": "completed"
    },
    {
      "lesson_id": 2,
      "completion_percentage": 50,
      "status": "in_progress"
    }
  ]
}
```

### Filtering and Sorting

#### Advanced Lesson Filtering
```http
GET /api/users/{user_id}/subjects/{subject}/lessons?status=completed&difficulty=intermediate&sort=completion_date&order=desc&limit=5
```

**Query Parameters:**
- `status`: Filter by completion status (`completed`, `in_progress`, `not_started`)
- `difficulty`: Filter by difficulty level (`beginner`, `intermediate`, `advanced`)
- `sort`: Sort field (`title`, `difficulty`, `completion_date`, `estimated_time`)
- `order`: Sort order (`asc`, `desc`)
- `limit`: Number of results per page (1-100)
- `offset`: Number of results to skip for pagination

#### Search Functionality
```http
GET /api/users/{user_id}/subjects/{subject}/lessons/search?q=functions&fields=title,content
```

**Query Parameters:**
- `q`: Search query string
- `fields`: Fields to search in (`title`, `content`, `objectives`)
- `fuzzy`: Enable fuzzy matching (`true`, `false`)

### Data Export and Import

#### Export User Data
```http
GET /api/users/{user_id}/export
```

**Response:**
```json
{
  "success": true,
  "data": {
    "export_id": "exp_12345",
    "download_url": "https://api.mindcoach.com/exports/exp_12345.zip",
    "expires_at": "2024-01-16T10:00:00Z",
    "includes": [
      "user_profile",
      "subscriptions", 
      "survey_results",
      "lesson_progress",
      "generated_content"
    ]
  }
}
```

#### Import User Data
```http
POST /api/users/{user_id}/import
```

**Request Body (multipart/form-data):**
```
file: <exported_data.zip>
options: {
  "overwrite_existing": false,
  "validate_data": true
}
```

### Analytics and Reporting

#### User Progress Analytics
```http
GET /api/users/{user_id}/analytics
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_subjects": 3,
      "active_subscriptions": 2,
      "lessons_completed": 25,
      "total_study_time": "45.5 hours",
      "average_session_length": "1.2 hours"
    },
    "progress_by_subject": [
      {
        "subject": "python",
        "completion_percentage": 80,
        "lessons_completed": 8,
        "total_lessons": 10,
        "time_spent": "20 hours"
      }
    ],
    "learning_streak": {
      "current_streak": 7,
      "longest_streak": 15,
      "last_activity": "2024-01-15T14:30:00Z"
    }
  }
}
```

#### System-Wide Analytics (Admin Only)
```http
GET /api/admin/analytics
```

**Response:**
```json
{
  "success": true,
  "data": {
    "users": {
      "total_users": 10000,
      "active_users_30d": 7500,
      "new_users_30d": 1200
    },
    "subscriptions": {
      "total_subscriptions": 15000,
      "active_subscriptions": 12000,
      "revenue_30d": 360000
    },
    "content_generation": {
      "surveys_generated_30d": 5000,
      "lessons_generated_30d": 50000,
      "average_generation_time": "3.2 minutes"
    }
  }
}
```

## Request/Response Schema Validation

### JSON Schema Definitions

#### User Creation Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["user_id", "email"],
  "properties": {
    "user_id": {
      "type": "string",
      "minLength": 3,
      "maxLength": 50,
      "pattern": "^[a-zA-Z0-9_-]+$"
    },
    "email": {
      "type": "string",
      "format": "email",
      "maxLength": 100
    }
  },
  "additionalProperties": false
}
```

#### Survey Submission Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["survey_id", "answers"],
  "properties": {
    "survey_id": {
      "type": "string",
      "pattern": "^survey_[a-zA-Z0-9]+$"
    },
    "answers": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["question_id", "answer"],
        "properties": {
          "question_id": {
            "type": "integer",
            "minimum": 1
          },
          "answer": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  }
}
```

#### Lesson Progress Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "completion_percentage": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100
    },
    "time_spent": {
      "type": "integer",
      "minimum": 0,
      "description": "Time spent in minutes"
    },
    "exercises_completed": {
      "type": "integer",
      "minimum": 0
    },
    "status": {
      "type": "string",
      "enum": ["not_started", "in_progress", "completed"]
    }
  },
  "additionalProperties": false
}
```

### Response Schema Validation

All API responses follow these schema patterns:

#### Success Response Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["success", "data"],
  "properties": {
    "success": {
      "type": "boolean",
      "const": true
    },
    "data": {
      "type": "object"
    },
    "message": {
      "type": "string"
    }
  }
}
```

#### Error Response Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["success", "error"],
  "properties": {
    "success": {
      "type": "boolean",
      "const": false
    },
    "error": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": {
          "type": "string",
          "pattern": "^[A-Z_]+$"
        },
        "message": {
          "type": "string"
        },
        "details": {
          "type": "object"
        }
      }
    }
  }
}
```

## SDK and Client Libraries

Official client libraries are available for popular programming languages:

### JavaScript/Node.js
```bash
npm install @mindcoach/api-client
```

```javascript
import MindCoachAPI from '@mindcoach/api-client';

const client = new MindCoachAPI({
  baseURL: 'https://api.mindcoach.com',
  userId: 'john_doe_123'
});

// Generate survey
const survey = await client.surveys.generate('python');
```

### Python
```bash
pip install mindcoach-api
```

#### Basic Usage
```python
from mindcoach_api import MindCoachClient
from mindcoach_api.exceptions import MindCoachAPIError

# Initialize client
client = MindCoachClient(
    base_url='https://api.mindcoach.com',
    user_id='john_doe_123',
    timeout=30
)

# Create user
try:
    user = client.users.create(
        user_id='new_user_123',
        email='newuser@example.com'
    )
    print(f"User created: {user.user_id}")
except MindCoachAPIError as e:
    print(f"Error: {e.message}")

# Select subject and generate survey
subject = client.subjects.select('python')
survey_task = client.surveys.generate('python')

# Wait for survey completion
survey = client.surveys.wait_for_completion(survey_task.task_id)

# Submit survey answers
answers = [
    {'question_id': 1, 'answer': 'def myFunc():'},
    {'question_id': 2, 'answer': 'list'}
]
submission = client.surveys.submit('python', survey.survey_id, answers)

# Start content generation
content_task = client.content.generate('python')

# Monitor progress with callback
def progress_callback(status):
    print(f"Stage: {status.current_stage}, Progress: {status.overall_progress}%")

result = client.content.wait_for_completion(
    content_task.task_id,
    callback=progress_callback
)

# Access generated lessons
lessons = client.lessons.list('python')
for lesson in lessons:
    print(f"Lesson {lesson.lesson_id}: {lesson.title}")
    
# Get specific lesson content
lesson_content = client.lessons.get('python', 1)
print(lesson_content.content)
```

#### Advanced Features
```python
# Batch operations
users_data = [
    {'user_id': 'user1', 'email': 'user1@example.com'},
    {'user_id': 'user2', 'email': 'user2@example.com'}
]
batch_result = client.users.create_batch(users_data)

# Analytics
analytics = client.analytics.get_user_analytics()
print(f"Total study time: {analytics.total_study_time}")

# Subscription management
subscription = client.subscriptions.purchase('python', payment_token='tok_123')
subscriptions = client.subscriptions.list()

# Export user data
export_task = client.users.export_data()
export_url = client.users.wait_for_export(export_task.export_id)
```

#### Error Handling
```python
from mindcoach_api.exceptions import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
    SubscriptionRequiredError
)

try:
    lessons = client.lessons.list('premium_subject')
except SubscriptionRequiredError as e:
    print(f"Subscription required: {e.subscription_url}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
except ValidationError as e:
    print(f"Validation errors: {e.field_errors}")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
```

#### Async Support
```python
import asyncio
from mindcoach_api import AsyncMindCoachClient

async def main():
    client = AsyncMindCoachClient(
        base_url='https://api.mindcoach.com',
        user_id='john_doe_123'
    )
    
    # Async operations
    user = await client.users.create('async_user', 'async@example.com')
    subjects = await client.subjects.list()
    
    # Concurrent operations
    tasks = [
        client.surveys.generate('python'),
        client.surveys.generate('javascript'),
        client.surveys.generate('react')
    ]
    results = await asyncio.gather(*tasks)
    
    await client.close()

asyncio.run(main())
```

### Go
```bash
go get github.com/mindcoach/mindcoach-go
```

#### Basic Usage
```go
package main

import (
    "context"
    "fmt"
    "log"
    
    "github.com/mindcoach/mindcoach-go"
)

func main() {
    client := mindcoach.NewClient(&mindcoach.Config{
        BaseURL: "https://api.mindcoach.com",
        UserID:  "john_doe_123",
        Timeout: 30 * time.Second,
    })
    
    ctx := context.Background()
    
    // Create user
    user, err := client.Users.Create(ctx, &mindcoach.CreateUserRequest{
        UserID: "go_user_123",
        Email:  "gouser@example.com",
    })
    if err != nil {
        log.Fatal(err)
    }
    
    // Generate survey
    surveyTask, err := client.Surveys.Generate(ctx, "python")
    if err != nil {
        log.Fatal(err)
    }
    
    // Wait for completion
    survey, err := client.Surveys.WaitForCompletion(ctx, surveyTask.TaskID)
    if err != nil {
        log.Fatal(err)
    }
    
    // Submit answers
    answers := []mindcoach.SurveyAnswer{
        {QuestionID: 1, Answer: "def myFunc():"},
        {QuestionID: 2, Answer: "list"},
    }
    
    submission, err := client.Surveys.Submit(ctx, "python", survey.SurveyID, answers)
    if err != nil {
        log.Fatal(err)
    }
    
    // Generate content
    contentTask, err := client.Content.Generate(ctx, "python")
    if err != nil {
        log.Fatal(err)
    }
    
    // Monitor progress
    progressChan := make(chan *mindcoach.ContentGenerationStatus)
    go func() {
        for status := range progressChan {
            fmt.Printf("Stage: %s, Progress: %d%%\n", 
                status.CurrentStage, status.OverallProgress)
        }
    }()
    
    result, err := client.Content.WaitForCompletion(ctx, contentTask.TaskID, progressChan)
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("Content generation completed: %d lessons\n", result.TotalLessons)
}
```

### PHP
```bash
composer require mindcoach/mindcoach-php
```

#### Basic Usage
```php
<?php
require_once 'vendor/autoload.php';

use MindCoach\Client;
use MindCoach\Exceptions\MindCoachException;

$client = new Client([
    'base_url' => 'https://api.mindcoach.com',
    'user_id' => 'john_doe_123',
    'timeout' => 30
]);

try {
    // Create user
    $user = $client->users()->create([
        'user_id' => 'php_user_123',
        'email' => 'phpuser@example.com'
    ]);
    
    // Select subject
    $client->subjects()->select('python');
    
    // Generate and submit survey
    $surveyTask = $client->surveys()->generate('python');
    $survey = $client->surveys()->waitForCompletion($surveyTask['task_id']);
    
    $answers = [
        ['question_id' => 1, 'answer' => 'def myFunc():'],
        ['question_id' => 2, 'answer' => 'list']
    ];
    
    $submission = $client->surveys()->submit('python', $survey['survey_id'], $answers);
    
    // Generate content with progress tracking
    $contentTask = $client->content()->generate('python');
    
    $client->content()->waitForCompletion($contentTask['task_id'], function($status) {
        echo "Stage: {$status['current_stage']}, Progress: {$status['overall_progress']}%\n";
    });
    
    // Get lessons
    $lessons = $client->lessons()->list('python');
    foreach ($lessons['lessons'] as $lesson) {
        echo "Lesson {$lesson['lesson_id']}: {$lesson['title']}\n";
    }
    
} catch (MindCoachException $e) {
    echo "Error: " . $e->getMessage() . "\n";
    echo "Code: " . $e->getErrorCode() . "\n";
}
?>
```

### Ruby
```bash
gem install mindcoach-api
```

#### Basic Usage
```ruby
require 'mindcoach'

client = MindCoach::Client.new(
  base_url: 'https://api.mindcoach.com',
  user_id: 'john_doe_123',
  timeout: 30
)

begin
  # Create user
  user = client.users.create(
    user_id: 'ruby_user_123',
    email: 'rubyuser@example.com'
  )
  
  # Generate survey
  survey_task = client.surveys.generate('python')
  survey = client.surveys.wait_for_completion(survey_task.task_id)
  
  # Submit answers
  answers = [
    { question_id: 1, answer: 'def myFunc():' },
    { question_id: 2, answer: 'list' }
  ]
  
  submission = client.surveys.submit('python', survey.survey_id, answers)
  
  # Generate content
  content_task = client.content.generate('python')
  
  # Monitor progress
  result = client.content.wait_for_completion(content_task.task_id) do |status|
    puts "Stage: #{status.current_stage}, Progress: #{status.overall_progress}%"
  end
  
  # Access lessons
  lessons = client.lessons.list('python')
  lessons.each do |lesson|
    puts "Lesson #{lesson.lesson_id}: #{lesson.title}"
  end
  
rescue MindCoach::AuthenticationError => e
  puts "Authentication failed: #{e.message}"
rescue MindCoach::RateLimitError => e
  puts "Rate limited. Retry after: #{e.retry_after} seconds"
rescue MindCoach::ValidationError => e
  puts "Validation errors: #{e.field_errors}"
rescue MindCoach::APIError => e
  puts "API error: #{e.message}"
end
```

## Testing the API

### Using cURL

#### Create a user
```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "email": "test@example.com"
  }'
```

#### Generate survey
```bash
curl -X POST http://localhost:5000/api/users/test_user_123/subjects/python/survey/generate \
  -H "Content-Type: application/json" \
  -H "User-ID: test_user_123"
```

#### Get survey questions
```bash
curl -X GET http://localhost:5000/api/users/test_user_123/subjects/python/survey \
  -H "User-ID: test_user_123"
```

### Using Postman

A comprehensive Postman collection is available for testing all API endpoints:

#### Collection Setup
1. **Import Collection**: `docs/postman/MindCoach_API.postman_collection.json`
2. **Import Environment**: `docs/postman/MindCoach_Environment.postman_environment.json`
3. **Set Environment Variables**:
   ```json
   {
     "base_url": "http://localhost:5000/api",
     "user_id": "test_user_123",
     "subject": "python",
     "auth_token": "{{user_id}}"
   }
   ```

#### Collection Structure
- **User Management**: Create, read, update user profiles
- **Subject Operations**: List subjects, select subjects, check access
- **Survey Workflow**: Generate, retrieve, submit surveys
- **Content Generation**: Start pipeline, monitor progress, retrieve content
- **Lesson Management**: List lessons, get content, update progress
- **Subscription Management**: Purchase, cancel, manage subscriptions
- **Analytics**: User analytics, progress tracking
- **Admin Operations**: System analytics, user management

#### Running Tests
1. **Individual Requests**: Run single endpoints for testing
2. **Collection Runner**: Execute entire test suite
3. **Environment Testing**: Switch between dev/staging/production
4. **Automated Testing**: Set up Newman for CI/CD integration

```bash
# Install Newman for command-line testing
npm install -g newman

# Run collection
newman run MindCoach_API.postman_collection.json \
  -e MindCoach_Environment.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

### Integration Testing Examples

#### Complete User Journey Test
```javascript
// Test complete user workflow
describe('Complete User Journey', () => {
  let userId = 'test_user_' + Date.now();
  let taskId;
  
  test('1. Create User', async () => {
    const response = await fetch(`${baseUrl}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        email: `${userId}@example.com`
      })
    });
    
    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data.user_id).toBe(userId);
  });
  
  test('2. Select Subject', async () => {
    const response = await fetch(`${baseUrl}/users/${userId}/subjects/python/select`, {
      method: 'POST',
      headers: { 'User-ID': userId }
    });
    
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
  });
  
  test('3. Generate Survey', async () => {
    const response = await fetch(`${baseUrl}/users/${userId}/subjects/python/survey/generate`, {
      method: 'POST',
      headers: { 'User-ID': userId }
    });
    
    expect(response.status).toBe(202);
    const data = await response.json();
    expect(data.data.task_id).toBeDefined();
  });
  
  test('4. Submit Survey', async () => {
    // Wait for survey generation to complete
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const surveyResponse = await fetch(`${baseUrl}/users/${userId}/subjects/python/survey`, {
      headers: { 'User-ID': userId }
    });
    const surveyData = await surveyResponse.json();
    
    const answers = surveyData.data.questions.map(q => ({
      question_id: q.id,
      answer: q.options[0] // Select first option for testing
    }));
    
    const submitResponse = await fetch(`${baseUrl}/users/${userId}/subjects/python/survey/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-ID': userId
      },
      body: JSON.stringify({
        survey_id: surveyData.data.survey_id,
        answers: answers
      })
    });
    
    expect(submitResponse.status).toBe(200);
  });
  
  test('5. Start Content Generation', async () => {
    const response = await fetch(`${baseUrl}/users/${userId}/subjects/python/content/generate`, {
      method: 'POST',
      headers: { 'User-ID': userId }
    });
    
    expect(response.status).toBe(202);
    const data = await response.json();
    taskId = data.data.task_id;
    expect(taskId).toBeDefined();
  });
  
  test('6. Monitor Content Generation', async () => {
    let completed = false;
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes max
    
    while (!completed && attempts < maxAttempts) {
      const response = await fetch(`${baseUrl}/users/${userId}/subjects/python/content/status/${taskId}`, {
        headers: { 'User-ID': userId }
      });
      
      const data = await response.json();
      
      if (data.data.overall_status === 'completed') {
        completed = true;
        expect(data.data.results.total_lessons).toBe(10);
      } else if (data.data.overall_status === 'failed') {
        throw new Error('Content generation failed');
      }
      
      await new Promise(resolve => setTimeout(resolve, 5000));
      attempts++;
    }
    
    expect(completed).toBe(true);
  });
  
  test('7. Access Generated Lessons', async () => {
    const response = await fetch(`${baseUrl}/users/${userId}/subjects/python/lessons`, {
      headers: { 'User-ID': userId }
    });
    
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.data.lessons).toHaveLength(10);
    expect(data.data.summary.total_progress).toBeGreaterThan(0);
  });
});
```

#### Performance Testing
```javascript
// Load testing example
describe('API Performance Tests', () => {
  test('Concurrent User Creation', async () => {
    const promises = [];
    const userCount = 50;
    
    for (let i = 0; i < userCount; i++) {
      promises.push(
        fetch(`${baseUrl}/users`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: `load_test_user_${i}`,
            email: `loadtest${i}@example.com`
          })
        })
      );
    }
    
    const startTime = Date.now();
    const responses = await Promise.all(promises);
    const endTime = Date.now();
    
    const successCount = responses.filter(r => r.status === 201).length;
    const avgResponseTime = (endTime - startTime) / userCount;
    
    expect(successCount).toBe(userCount);
    expect(avgResponseTime).toBeLessThan(1000); // Less than 1 second average
  });
  
  test('API Rate Limiting', async () => {
    const promises = [];
    const requestCount = 150; // Exceed rate limit of 100/hour
    
    for (let i = 0; i < requestCount; i++) {
      promises.push(
        fetch(`${baseUrl}/subjects`, {
          headers: { 'User-ID': 'rate_limit_test_user' }
        })
      );
    }
    
    const responses = await Promise.all(promises);
    const rateLimitedCount = responses.filter(r => r.status === 429).length;
    
    expect(rateLimitedCount).toBeGreaterThan(0);
  });
});
```

## API Versioning

The API uses URL-based versioning:

- **Current Version**: v1 (default, no version prefix required)
- **Future Versions**: `/api/v2/`, `/api/v3/`, etc.

Version-specific documentation will be maintained for each API version.

## Support and Feedback

For API support, questions, or feedback:

- **Documentation Issues**: Create an issue in the GitHub repository
- **API Bugs**: Report via the bug tracking system
- **Feature Requests**: Submit via the feature request portal
- **General Support**: Contact the API support team

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- User management endpoints
- Subject selection and subscription management
- AI-powered survey generation
- Three-stage content generation pipeline
- Lesson management and progress tracking