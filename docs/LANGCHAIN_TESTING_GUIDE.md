# LangChain Testing Guide

## Overview

This guide covers the comprehensive testing suite implemented for the LangChain-powered personalized learning system. The testing framework ensures reliability, performance, and quality of the AI-driven content generation pipeline.

## Test Structure

### 1. Unit Tests (`test_langchain_chains_comprehensive.py`)

**Purpose**: Test individual LangChain chain components in isolation

**Coverage**:
- `BaseLangChainService` - Core functionality and retry logic
- `ContentGenerationChain` - RAG document loading and output validation
- `SurveyGenerationChain` - Survey question generation with difficulty distribution
- `CurriculumGeneratorChain` - Curriculum creation based on assessment results
- `LessonPlannerChain` - Detailed lesson plan generation
- `ContentGeneratorChain` - Comprehensive lesson content creation

**Key Features**:
- Mock LLM responses for consistent testing
- Validation of output structure and quality
- Error handling and retry mechanism testing
- RAG document integration testing

### 2. Integration Tests (`test_langchain_integration_comprehensive.py`)

**Purpose**: Test interaction between pipeline components

**Coverage**:
- Pipeline service initialization
- Stage-to-stage data flow
- Error propagation between stages
- RAG document integration across pipeline
- Connection testing with xAI API

**Key Features**:
- Full pipeline execution simulation
- Partial RAG document handling
- Error scenario testing
- Status reporting validation

### 3. xAI API Mock Tests (`test_xai_api_mocks.py`)

**Purpose**: Test xAI API interactions without external dependencies

**Coverage**:
- Successful API calls
- Rate limiting and retry logic
- Server error handling
- Client error responses
- Timeout and connection error recovery
- JSON response parsing
- Custom parameters and stop sequences

**Key Features**:
- Comprehensive error scenario coverage
- Response format validation
- Configuration testing
- Connection test mocking

### 4. Performance Tests (`test_langchain_performance.py`)

**Purpose**: Validate system performance and scalability

**Coverage**:
- Individual chain performance benchmarks
- Full pipeline execution timing
- Concurrent content generation
- Memory usage validation
- Error recovery performance
- Multi-user scalability testing

**Key Features**:
- Execution time assertions
- Throughput measurements
- Concurrent processing tests
- Performance regression detection

### 5. RAG Document Integration Tests (`test_rag_document_integration.py`)

**Purpose**: Test RAG document system integration

**Coverage**:
- Document loading and parsing
- Content quality with different RAG documents
- Document versioning and updates
- Format compliance validation
- Subject-specific document loading
- Fallback behavior when documents unavailable

**Key Features**:
- Document quality impact testing
- Version management validation
- Format compliance checking
- Subject-specific customization

### 6. End-to-End Tests (`test_langchain_end_to_end.py`)

**Purpose**: Test complete workflow from survey to lesson generation

**Coverage**:
- Survey-to-lessons pipeline
- Content quality and personalization
- Error handling and recovery
- Performance benchmarks
- Different skill level adaptation
- RAG document workflow integration

**Key Features**:
- Complete workflow validation
- Personalization verification
- Quality assurance checks
- Performance benchmarking
- Skill-level adaptation testing

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-mock

# Set up environment variables (for integration tests)
export XAI_API_KEY="test-key"
export GROK_API_URL="https://api.x.ai/v1"
```

### Running Individual Test Suites

```bash
# Unit tests
python -m pytest backend/tests/test_langchain_chains_comprehensive.py -v

# Integration tests
python -m pytest backend/tests/test_langchain_integration_comprehensive.py -v

# Performance tests
python -m pytest backend/tests/test_langchain_performance.py -v

# RAG document tests
python -m pytest backend/tests/test_rag_document_integration.py -v

# End-to-end tests
python -m pytest backend/tests/test_langchain_end_to_end.py -v
```

### Running All LangChain Tests

```bash
# Run all LangChain-related tests
python -m pytest backend/tests/test_langchain* -v

# Run with coverage report
python -m pytest backend/tests/test_langchain* --cov=app.services.langchain --cov-report=html
```

## Test Data and Fixtures

### Survey Data Fixtures

```python
@pytest.fixture
def complete_survey_data():
    return {
        'user_id': 'test-user',
        'subject': 'python',
        'skill_level': 'intermediate',
        'answers': [
            {'question_id': 1, 'topic': 'variables', 'correct': True},
            {'question_id': 2, 'topic': 'functions', 'correct': False},
            # ... more answers
        ]
    }
```

### RAG Document Fixtures

```python
@pytest.fixture
def mock_rag_documents():
    return {
        'survey': ['Generate 7-8 questions', 'Follow difficulty distribution'],
        'curriculum': ['Create comprehensive curriculum', 'Adapt to skill level'],
        'lesson_plans': ['Design 60-minute lessons', 'Include activities'],
        'content': ['Generate engaging content', 'Include code examples']
    }
```

## Mocking Strategy

### LLM Response Mocking

```python
@patch('app.services.langchain_chains.XAILLM')
def test_chain_functionality(mock_llm_class):
    mock_llm_class.return_value = Mock()
    
    mock_chain = Mock()
    mock_chain.run.return_value = expected_response
    
    with patch('app.services.langchain_chains.LLMChain', return_value=mock_chain):
        # Test implementation
```

### API Response Mocking

```python
@patch('app.services.langchain_base.requests.post')
def test_api_interaction(mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"message": {"content": "response"}}]}
    mock_post.return_value = mock_response
    
    # Test API interaction
```

## Quality Assurance

### Content Validation

Tests verify that generated content meets quality standards:

- **Structure**: Proper markdown formatting with headers, code blocks, lists
- **Completeness**: Required sections (objectives, examples, exercises, summary)
- **Code Examples**: At least 2 practical code examples per lesson
- **Exercises**: 3-5 hands-on exercises with varying difficulty
- **Length**: Substantial content (minimum character counts)

### Personalization Validation

Tests ensure content adapts to user needs:

- **Skill Level**: Content difficulty matches assessed skill level
- **Known Topics**: Topics already mastered are skipped or advanced
- **Weak Areas**: Focus on areas where user showed weakness
- **Learning Objectives**: Aligned with user's learning goals

### Performance Standards

Tests enforce performance requirements:

- **Response Time**: Individual chains complete within time limits
- **Pipeline Execution**: Full pipeline completes within acceptable timeframe
- **Throughput**: System can handle multiple concurrent requests
- **Memory Usage**: Memory consumption stays within bounds

## Continuous Integration

### GitHub Actions Integration

```yaml
name: LangChain Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run LangChain tests
        run: python -m pytest backend/tests/test_langchain* -v
```

### Test Coverage Requirements

- **Unit Tests**: Minimum 90% code coverage for chain components
- **Integration Tests**: All pipeline stages and error paths covered
- **End-to-End Tests**: Complete user workflows validated
- **Performance Tests**: All critical performance metrics monitored

## Troubleshooting

### Common Test Issues

1. **Mock Configuration**: Ensure all external dependencies are properly mocked
2. **Fixture Data**: Verify test data matches expected formats
3. **Async Operations**: Handle any asynchronous operations in tests
4. **Environment Variables**: Set required environment variables for tests

### Debug Mode

```bash
# Run tests with detailed output
python -m pytest backend/tests/test_langchain* -v -s --tb=long

# Run specific test with debugging
python -m pytest backend/tests/test_langchain_chains_comprehensive.py::TestSurveyGenerationChain::test_survey_generation -v -s
```

## Best Practices

### Test Organization

- **Descriptive Names**: Test method names clearly describe what is being tested
- **Single Responsibility**: Each test focuses on one specific aspect
- **Proper Setup**: Use fixtures for consistent test data setup
- **Clean Teardown**: Ensure tests don't affect each other

### Mock Usage

- **Minimal Mocking**: Mock only external dependencies, not internal logic
- **Realistic Data**: Use realistic mock data that matches production scenarios
- **Error Scenarios**: Include both success and failure scenarios
- **State Verification**: Verify both return values and side effects

### Performance Testing

- **Baseline Metrics**: Establish performance baselines for regression testing
- **Load Testing**: Test with realistic data volumes and concurrent users
- **Resource Monitoring**: Monitor memory, CPU, and network usage
- **Scalability Testing**: Verify system scales with increased load

This comprehensive testing suite ensures the LangChain system is robust, performant, and produces high-quality personalized learning content.