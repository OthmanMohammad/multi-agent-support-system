# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-13

### Added

- Create exception utilities package
- Add exception enrichment with context
- Add decorators for exception handling
- Add context extraction utilities
- Enhance error handlers with exception enrichment
- Add correlation ID and logging middleware
- Integrate middleware and structured logging
- Add structured logging to conversation endpoints
- Add structured logging to customer endpoints
- Add structured logging to analytics endpoints
- Add structured logging to health check endpoints
- Migrate notification service to structured logging
- Migrate customer infrastructure service to structured logging
- Migrate analytics service to structured logging
- Migrate knowledge base service to structured logging
- Migrate conversation application service to structured logging
- Migrate customer application service to structured logging
- Migrate workflow engine to structured logging
- Migrate LangGraph to structured logging
- Migrate router agent to structured logging
- Migrate billing agent to structured logging
- Migrate technical agent to structured logging
- Migrate escalation agent to structured logging
- Migrate usage agent to structured logging
- Migrate API agent to structured logging
- Migrate connection module to structured logging
- Migrate result handler to structured logging
- Migrate state manager to structured logging
- Migrate base service to structured logging
- Migrate event bus to structured logging
- Migrate enrichment utilities to structured logging
- Add Sentry Discord integration for real-time alerts
- Add performance testing utilities for Sentry
- Add centralized configuration management with Pydantic Settings
- Add startup configuration validation with fail-fast

### Build

- Add pydantic-settings for configuration management

### Documentation

- Generate initial changelog with git-cliff
- Enhance exception docstrings for Phase 4
- Add comprehensive Discord integration documentation
- Update environment template with security requirements
- Add comprehensive Doppler secrets management documentation

### Fixed

- Add missing EnrichedExceptionMixin class to enrichment.py
- Remove hardcoded database credentials from version control
- Convert async database URL to sync for Alembic compatibility
- Ensure Alembic uses sync database URL

### Miscellaneous

- Add git-cliff configuration for automated changelog
- Add git-cliff configuration for automated changelog
- Ignore local release guide
- Explicitly ignore environment files to prevent secret leaks
- Add Doppler config and .env files to .gitignore

### Refactored

- Standardize imports with explicit src package prefix
- Update .env.example for staging/production only and fix CORS format
- Integrate centralized configuration management
- Use centralized configuration for database connections
- Use centralized configuration for Sentry
- Export configuration management functions
- Use centralized config for Anthropic API
- Use centralized config for Qdrant
- Use centralized config in simple agent
- Use centralized config and remove development environment

## [1.0.0] - 2025-11-12

### Added

- Initialize project directory structure with modular architecture
- Implement basic chat function with Claude API
- Add conversation history for multi-turn context
- Add conversation history limit to prevent token overflow
- Add conversation statistics tracking and display
- Add knowledge base with 10 sample support articles
- Implement keyword-based article search with scoring
- Integrate knowledge base search into agent responses
- Add source citations display for knowledge base articles
- Save conversations to JSON file on exit
- Add conversation manager to list and load saved chats
- Add project dependencies
- Add Qdrant vector store client with search and upsert
- Add Qdrant Cloud client with sentence-transformers
- Add embedding generation for KB articles
- Add KB loader for Qdrant Cloud
- Upgrade to vector search with keyword fallback
- Integrate vector search for semantic KB retrieval
- Add AgentState definition for LangGraph
- Add BaseAgent abstract class
- Add Router agent with intent classification
- Add Billing specialist agent
- Add LangGraph orchestration for multi-agent system
- Add interactive multi-agent demo
- Add Technical, Usage, and Escalation agents
- Add all 5 agents to LangGraph orchestration
- Add Pydantic models for REST API
- Add in-memory conversation storage
- Add FastAPI REST API with streaming support
- Add 15 API documentation articles
- Implement APIAgent for developer support
- Integrate APIAgent into full 6-agent system
- Add SQLAlchemy ORM models for all tables
- Add async connection manager with pooling
- Setup Alembic migrations and create initial schema
- Add base repository with common CRUD operations
- Add customer repository with email lookup
- Add conversation repository with status management
- Add message repository for conversation messages
- Export all repositories from package
- Add database repository dependencies for dependency injection
- Integrate database persistence replacing in-memory storage
- Add base model with timestamp mixin and common methods
- Add customer model with relationships and constraints
- Add conversation model with performance indexes
- Add message model with conversation relationship
- Add agent performance model with success rate calculation
- Add models package exports
- Add conversation schemas with statistics model
- Add customer Pydantic schemas with validation
- Add message schemas with sentiment distribution
- Add agent performance schemas with computed success rate
- Add schemas package exports with all DTOs
- Enhance base repository with bulk operations and advanced queries
- Enhance customer repository with plan management and search
- Enhance conversation repository with statistics and advanced queries
- Enhance message repository with sentiment and token tracking
- Add agent performance repository with analytics methods
- Export all repositories including agent performance
- Enhance connection manager with health checks and pool monitoring
- Add agent performance repository to dependencies
- Add performance indexes for optimized queries
- Update database package exports with new structure
- Add database health check utility script
- Add audit trail and soft delete support to base model
- Implement Unit of Work pattern for transaction management
- Enhance base repository with soft delete and audit support
- Add Unit of Work dependency injection
- Export Unit of Work in package init
- Export Unit of Work in package
- Complete database schema with Unit of Work and Audit Trail
- Implement Result pattern for railway-oriented programming
- Update exports to include events and specifications
- Add structured error types with factory functions
- Add domain events infrastructure with EventBus
- Add specification pattern for composable business rules
- Add base service package structure
- Add BaseService with result-based error handling
- Add services package root with documentation
- Add test suite package with structure documentation
- Add pytest configuration with shared fixtures and path setup
- Add comprehensive unit tests for core patterns (Result, Events, Specifications)
- Add domain services package structure
- Wire up domain services package exports
- Add conversation domain validators
- Add conversation domain event definitions
- Add conversation business rule specifications
- Implement conversation domain service with pure business logic
- Add customer domain validators
- Add customer domain event definitions
- Add customer business rule specifications
- Implement customer domain service with pure business logic
- Add workflow package initialization
- Add comprehensive exception hierarchy
- Implement state lifecycle manager
- Implement agent result parser and validator
- Implement main Agent Workflow Engine
- Add infrastructure services package initialization
- Implement CustomerInfrastructureService
- Implement KnowledgeBaseService
- Implement AnalyticsService
- Implement NotificationService
- Implement CachingService
- Update services package exports
- Add application services package initialization
- Add ConversationApplicationService for orchestration
- Add CustomerApplicationService for customer operations
- Add error handlers for Result to HTTP mapping
- Add application service dependencies
- Add routes package with domain separation
- Add conversation routes with thin controllers
- Add customer routes with thin controllers
- Add analytics routes for system metrics
- Add health check routes for monitoring
- Initialize utils package for shared utilities
- Add logging package with public API
- Implement structured logging setup with structlog
- Add async-safe context management with contextvars
- Implement PII masking for GDPR compliance
- Add custom formatters for JSON and console output
- Add logging decorators for common patterns
- Integrate structured logging in FastAPI startup
- Add Sentry SDK integration with PII filtering
- Initialize Sentry monitoring on application startup
- Capture internal errors in Sentry

### Build

- Add anthropic and dotenv dependencies

### Documentation

- Add comprehensive API documentation
- Add Sentry configuration to environment template
- Add changelog for version tracking

### Fixed

- Fix circular imports and add multi-file support
- Change document IDs to integer index for Qdrant
- Add category field index for Qdrant filtering
- Standardize all agents to claude-3-haiku-20240307
- Add load_dotenv() to read .env file
- Rename metadata to extra_metadata to avoid SQLAlchemy reserved keyword
- Resolve circular import in customer schema using TYPE_CHECKING
- Resolve circular import in conversation schema using TYPE_CHECKING
- Correct Message model relationship to reference Conversation
- Correct import path in test script
- Properly handle NULL values in update operations
- Correct type annotation for Unit of Work context manager
- Add async/await support to BaseService for database operations
- Export handle_exceptions decorator from base package
- Update ValueError regex pattern to match actual error message
- Rename TestEntity to Entity to avoid pytest collection warning
- Use kw_only for test event dataclasses to fix field order
- Update error details assertions to handle None values
- Add default values to domain event fields to fix dataclass inheritance
- Restore sentinel pattern in Result class to handle None values correctly
- Add missing timestamp field to conversation response dicts
- Resolve Pydantic validation errors in list_conversations and customers endpoints
- Remove plan_benefits calculation causing JSON infinity error

### Miscellaneous

- Configure comprehensive gitignore for Python and project artifacts
- Ignore saved conversations and preserve directory structure
- Exclude embedded articles from version control
- Add LangGraph and LangChain for multi-agent system
- Add FastAPI and streaming dependencies for production API
- Add database dependencies (SQLAlchemy, asyncpg, Alembic)
- Apply database migration for performance indexes
- Configure pytest for async test support
- Add sentry-sdk for error tracking
- Set version to 1.0.0 for initial release

### Refactored

- Update models.py to import from modular structure
- Migrate chat endpoint to Unit of Work pattern
- Move state definitions to workflow package
- Move LangGraph to workflow package
- Update base agent imports for workflow package
- Update router agent imports for workflow package
- Update billing agent imports for workflow package
- Update technical agent imports for workflow package
- Update usage agent imports for workflow package
- Update API agent imports for workflow package
- Update escalation agent imports for workflow package
- Update demo to use workflow package
- Update API server to use workflow package
- Remove deprecated state.py
- Remove deprecated graph.py
- Transform main.py into thin HTTP layer

### Testing

- Add pytest conftest for proper imports
- Add comparison test for keyword vs vector search
- Add API test client
- Add comprehensive Unit of Work tests
- Add comprehensive tests for conversation validators
- Add comprehensive tests for conversation specifications
- Add comprehensive tests for conversation domain service
- Add comprehensive tests for customer validators
- Add comprehensive tests for customer specifications
- Add comprehensive tests for customer domain service
- Add domain test package structure and shared fixtures
- Add pytest configuration for domain tests
- Add comprehensive unit tests for infrastructure services
- Add integration tests for infrastructure services
- Add Services unit tests package

### Config

- Add environment template for API key
- Add logging environment variables to .env.example

### Deps

- Add structlog dependencies for structured logging

### Migration

- Add audit trail and soft delete fields to all tables
- Complete schema with audit trail and optimized indexes

[1.1.0]: https://github.com/othmanmohammad/multi-agent-support-system/compare/v1.0.0...v1.1.0

