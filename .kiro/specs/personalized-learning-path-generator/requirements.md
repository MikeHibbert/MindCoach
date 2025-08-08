# Requirements Document

## Introduction

The Personalized Learning Path Generator is a web application that provides customized learning experiences for users across various programming subjects. The system assesses user knowledge through surveys and generates tailored lesson content, implementing a pay-per-subject monetization model. The application features a responsive design supporting desktop, tablet, and mobile devices, with lessons stored as markdown files in a structured file system.

## Requirements

### Requirement 1

**User Story:** As a learner, I want to select a programming subject from available options, so that I can begin a personalized learning journey in my area of interest.

#### Acceptance Criteria

1. WHEN a user accesses the application THEN the system SHALL display available subjects in a dropdown or card grid format
2. WHEN a user selects a subject THEN the system SHALL save the selection as `users/<user_id>/selection.json`
3. WHEN the interface is viewed on desktop (min-width: 1024px) THEN the system SHALL display the full layout with sidebar navigation
4. WHEN the interface is viewed on tablet (min-width: 768px) THEN the system SHALL display a stacked layout with larger touch targets
5. WHEN the interface is viewed on mobile (max-width: 767px) THEN the system SHALL display a single-column, touch-friendly design

### Requirement 2

**User Story:** As a learner, I want to take a knowledge assessment survey for my selected subject, so that the system can understand my current skill level and customize my learning path accordingly.

#### Acceptance Criteria

1. WHEN a user selects a subject THEN the system SHALL generate a survey with 5-10 questions specific to that subject
2. WHEN the survey is generated THEN the system SHALL save it as `users/<user_id>/<subject>/survey.json`
3. WHEN a user submits survey answers THEN the system SHALL save responses as `users/<user_id>/<subject>/survey_answers.json`
4. WHEN survey answers are processed THEN the system SHALL analyze responses to determine skill level (beginner, intermediate, advanced)
5. WHEN the survey is displayed THEN the system SHALL ensure responsive design across all device types

### Requirement 3

**User Story:** As a learner, I want to receive personalized lesson content based on my assessment results, so that I can focus on topics I need to learn while skipping content I already know.

#### Acceptance Criteria

1. WHEN survey processing is complete THEN the system SHALL generate exactly 10 markdown lesson files tailored to the user's skill level
2. WHEN lessons are generated THEN the system SHALL store them in `users/<user_id>/<subject>/` directory as `lesson_1.md` through `lesson_10.md`
3. WHEN creating lessons THEN the system SHALL skip topics the user demonstrated knowledge of in the survey
4. WHEN displaying lessons THEN each lesson SHALL include explanations, code examples, and a quiz
5. WHEN lessons are viewed THEN the system SHALL render markdown content as HTML for proper display
6. WHEN lessons are accessed THEN the system SHALL ensure responsive viewing across desktop, tablet, and mobile devices

### Requirement 4

**User Story:** As a business owner, I want to implement a pay-per-subject model, so that users must purchase access to each subject before receiving personalized lessons.

#### Acceptance Criteria

1. WHEN a user attempts to access a subject THEN the system SHALL check for an active subscription in the SQLite database
2. WHEN a user has an active subscription for a subject THEN the system SHALL allow lesson generation and access
3. WHEN a user lacks a subscription for a subject THEN the system SHALL prevent lesson generation and display the subject as locked
4. WHEN displaying subjects THEN the system SHALL clearly indicate which subjects are available and which are locked
5. WHEN subscription status changes THEN the system SHALL update the SQLite database accordingly

### Requirement 5

**User Story:** As a user with accessibility needs, I want the application to be fully accessible, so that I can navigate and use all features regardless of my abilities.

#### Acceptance Criteria

1. WHEN the application loads THEN the system SHALL use readable fonts with high-contrast colors
2. WHEN a user navigates using keyboard only THEN the system SHALL provide full keyboard navigation support
3. WHEN screen readers are used THEN the system SHALL provide appropriate ARIA labels and semantic HTML
4. WHEN content is displayed THEN the system SHALL maintain accessibility standards across all responsive breakpoints
5. WHEN interactive elements are present THEN the system SHALL provide adequate touch targets for mobile and tablet users

### Requirement 6

**User Story:** As a system administrator, I want user data to be properly organized and stored, so that the system can efficiently manage user progress and content delivery.

#### Acceptance Criteria

1. WHEN a new user is created THEN the system SHALL create a `users/<user_id>` directory structure
2. WHEN a user selects a subject THEN the system SHALL create a `users/<user_id>/<subject>/` subdirectory
3. WHEN user data needs to be stored THEN the system SHALL use SQLite database for user profiles, subscriptions, and survey results
4. WHEN lesson files are created THEN the system SHALL store them as markdown files in the appropriate user/subject directory
5. WHEN data integrity is required THEN the system SHALL maintain consistent file naming conventions and directory structures

### Requirement 7

**User Story:** As a developer, I want the application to use modern web technologies with a clear separation of concerns, so that the system is maintainable and scalable.

#### Acceptance Criteria

1. WHEN implementing the frontend THEN the system SHALL use React with Tailwind CSS for responsive UI components
2. WHEN implementing the backend THEN the system SHALL use Flask (Python) with SQLite for data management
3. WHEN styling the application THEN the system SHALL use Tailwind CSS classes for responsive design implementation
4. WHEN handling data persistence THEN the system SHALL separate file-based lesson storage from database-stored user metadata
5. WHEN structuring the codebase THEN the system SHALL maintain clear separation between frontend and backend components