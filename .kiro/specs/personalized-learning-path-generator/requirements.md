# Requirements Document

## Introduction
The Personalized Learning Path Generator is a web application, branded as MindCoach, that provides customized learning experiences for users across various programming subjects. The system assesses user knowledge through AI-generated surveys and creates comprehensive learning content using a LangChain-orchestrated pipeline with Grok-3 Mini via xAI's API. The application implements a pay-per-subject monetization model with responsive design supporting desktop, tablet, and mobile devices. Content generation follows a three-stage LangChain pipeline: curriculum planning, lesson plan creation, and content generation, all guided by RAG documents for consistent quality and structure.

## Requirements

### Requirement 1
**User Story:** As a learner, I want to select a programming subject from available options, so that I can begin a personalized learning journey in my area of interest.
#### Acceptance Criteria
1. WHEN a user accesses the application THEN the system SHALL display available subjects in a dropdown or card grid format.
2. WHEN a user selects a subject THEN the system SHALL save the selection as `users/<user_id>/selection.json`.
3. WHEN the interface is viewed on desktop (min-width: 1024px) THEN the system SHALL display the full layout with sidebar navigation.
4. WHEN the interface is viewed on tablet (min-width: 768px) THEN the system SHALL display a stacked layout with larger touch targets.
5. WHEN the interface is viewed on mobile (max-width: 767px) THEN the system SHALL display a single-column, touch-friendly design.

### Requirement 2
**User Story:** As a learner, I want to take an AI-generated knowledge assessment survey for my selected subject, so that the system can understand my current skill level and customize my learning path accordingly.
#### Acceptance Criteria
1. WHEN a user selects a subject THEN the system SHALL use Grok-3 Mini via xAI API to generate 5-10 assessment questions specific to that subject.
2. WHEN generating survey questions THEN the system SHALL use LangChain to orchestrate the AI call with appropriate prompting and validation.
3. WHEN creating questions THEN the system SHALL follow RAG document guidelines to ensure consistent question quality and format.
4. WHEN the survey is generated THEN the system SHALL save it as `users/<user_id>/<subject>/survey.json`.
5. WHEN a user submits survey answers THEN the system SHALL save responses as `users/<user_id>/<subject>/survey_answers.json`.
6. WHEN survey answers are processed THEN the system SHALL analyze responses to determine skill level (beginner, intermediate, advanced).
7. WHEN the survey is displayed THEN the system SHALL ensure responsive design across all device types.

### Requirement 3
**User Story:** As a learner, I want to receive personalized lesson content generated through a sophisticated AI pipeline, so that I can access high-quality, tailored learning materials that match my skill level and learning needs.
#### Acceptance Criteria
1. WHEN survey processing is complete THEN the system SHALL initiate a three-stage LangChain pipeline for content generation.
2. WHEN Stage 1 executes THEN the system SHALL use Grok-3 Mini to generate a comprehensive learning scheme/curriculum based on survey results.
3. WHEN Stage 2 executes THEN the system SHALL use Grok-3 Mini to create detailed lesson plans for each topic in the curriculum.
4. WHEN Stage 3 executes THEN the system SHALL use Grok-3 Mini to generate complete lesson content documents with explanations, examples, and exercises.
5. WHEN each stage executes THEN the system SHALL use RAG documents to guide content structure, quality, and consistency.
6. WHEN lessons are generated THEN the system SHALL store them in `users/<user_id>/<subject>/` directory as `lesson_1.md` through `lesson_10.md`.
7. WHEN creating lessons THEN the system SHALL skip topics the user demonstrated knowledge of in the survey.
8. WHEN lessons are generated THEN the system SHALL display a progress indicator showing current pipeline stage and completion status.
9. WHEN lessons are viewed THEN the system SHALL render markdown content as HTML for proper display.
10. WHEN lessons are accessed THEN the system SHALL ensure responsive viewing across desktop, tablet, and mobile devices.

### Requirement 4
**User Story:** As a business owner, I want to implement a pay-per-subject model, so that users must purchase access to each subject before receiving personalized lessons.
#### Acceptance Criteria
1. WHEN a user attempts to access a subject THEN the system SHALL check for an active subscription in the SQLite database.
2. WHEN a user has an active subscription for a subject THEN the system SHALL allow lesson generation and access.
3. WHEN a user lacks a subscription for a subject THEN the system SHALL prevent lesson generation and display the subject as locked.
4. WHEN displaying subjects THEN the system SHALL clearly indicate which subjects are available and which are locked.
5. WHEN subscription status changes THEN the system SHALL update the SQLite database accordingly.

### Requirement 5
**User Story:** As a user with accessibility needs, I want the application to be fully accessible, so that I can navigate and use all features regardless of my abilities.
#### Acceptance Criteria
1. WHEN the application loads THEN the system SHALL use readable fonts with high-contrast colors.
2. WHEN a user navigates using keyboard only THEN the system SHALL provide full keyboard navigation support.
3. WHEN screen readers are used THEN the system SHALL provide appropriate ARIA labels and semantic HTML.
4. WHEN content is displayed THEN the system SHALL maintain accessibility standards across all responsive breakpoints.
5. WHEN interactive elements are present THEN the system SHALL provide adequate touch targets for mobile and tablet users.

### Requirement 6
**User Story:** As a system administrator, I want user data to be properly organized and stored, so that the system can efficiently manage user progress and content delivery.
#### Acceptance Criteria
1. WHEN a new user is created THEN the system SHALL create a `users/<user_id>` directory structure.
2. WHEN a user selects a subject THEN the system SHALL create a `users/<user_id>/<subject>/` subdirectory.
3. WHEN user data needs to be stored THEN the system SHALL use SQLite database for user profiles, subscriptions, and survey results.
4. WHEN lesson files are created THEN the system SHALL store them as markdown files in the appropriate user/subject directory.
5. WHEN data integrity is required THEN the system SHALL maintain consistent file naming conventions and directory structures.

### Requirement 7
**User Story:** As a developer, I want the application to use modern web technologies with a clear separation of concerns, so that the system is maintainable and scalable.
#### Acceptance Criteria
1. WHEN implementing the frontend THEN the system SHALL use React with Tailwind CSS for responsive UI components.
2. WHEN implementing the backend THEN the system SHALL use Flask (Python) with SQLite for data management.
3. WHEN styling the application THEN the system SHALL use Tailwind CSS classes for responsive design implementation.
4. WHEN handling data persistence THEN the system SHALL separate file-based lesson storage from database-stored user metadata.
5. WHEN structuring the codebase THEN the system SHALL maintain clear separation between frontend and backend components.

### Requirement 8
**User Story:** As a system administrator, I want the content generation pipeline to use RAG documents for guidance, so that all generated content follows consistent structure and quality standards.
#### Acceptance Criteria
1. WHEN the system initializes THEN it SHALL load RAG documents that define lesson structure, content guidelines, and quality standards.
2. WHEN generating surveys THEN the system SHALL reference RAG documents to ensure question format and assessment criteria consistency.
3. WHEN creating curriculum schemes THEN the system SHALL use RAG documents to guide learning progression and topic organization.
4. WHEN generating lesson plans THEN the system SHALL follow RAG document templates for lesson structure and learning objectives.
5. WHEN creating lesson content THEN the system SHALL use RAG documents to ensure consistent formatting, example quality, and exercise design.
6. WHEN RAG documents are updated THEN the system SHALL use the latest versions for all subsequent content generation.

### Requirement 9
**User Story:** As a developer, I want the system to use LangChain for AI orchestration instead of direct API calls, so that the content generation pipeline is more robust, maintainable, and extensible.
#### Acceptance Criteria
1. WHEN the system needs to generate content THEN it SHALL use LangChain to orchestrate all AI interactions with Grok-3 Mini.
2. WHEN using LangChain THEN the system SHALL implement proper error handling, retry logic, and response validation.
3. WHEN processing AI responses THEN the system SHALL use LangChain's parsing capabilities to ensure structured output.
4. WHEN managing AI prompts THEN the system SHALL use LangChain's prompt templates for consistency and maintainability.
5. WHEN scaling content generation THEN the system SHALL leverage LangChain's chain composition for complex multi-stage workflows.
6. WHEN integrating with xAI API THEN the system SHALL use LangChain's API integration patterns for reliable communication.

### Requirement 10
**User Story:** As a DevOps engineer, I want the application to be containerized with Docker, so that deployment is consistent, scalable, and environment-independent.
#### Acceptance Criteria
1. WHEN deploying the application THEN the system SHALL use Docker containers for frontend, backend, and supporting services.
2. WHEN building containers THEN the system SHALL use multi-stage builds to optimize image sizes and security.
3. WHEN running in production THEN the system SHALL use Docker Compose to orchestrate all services with proper networking and volumes.
4. WHEN scaling the application THEN the system SHALL support horizontal scaling through container replication.
5. WHEN managing data persistence THEN the system SHALL use Docker volumes for database, user data, and RAG documents.
6. WHEN monitoring system health THEN the system SHALL implement container health checks and logging.
7. WHEN developing locally THEN the system SHALL provide a development Docker configuration with hot reloading and debugging support.

## Design Overview
- **Responsive UI**: Use Tailwind CSS for desktop (min-width: 1024px), tablet (min-width: 768px), and mobile (max-width: 767px) layouts.
- **File Structure**: Store data in `users/<user_id>/<subject>` with `selection.json`, `survey.json`, `survey_answers.json`, `curriculum_scheme.json`, `lesson_plans.json`, and `lesson_1.md` to `lesson_10.md`.
- **LangChain Pipeline**: Three-stage content generation pipeline using LangChain with Grok-3 Mini via xAI API.
- **RAG Integration**: Use structured RAG documents to guide content generation quality and consistency.
- **Asynchronous Processing**: Use background task processing for the multi-stage content generation pipeline with real-time progress updates.
- **Containerized Deployment**: Docker-based deployment with separate containers for frontend, backend, Redis, and Nginx reverse proxy.