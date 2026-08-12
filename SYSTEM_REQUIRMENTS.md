# System Requirements

## 1. Project Overview

**Project:** Natural Language → SQL Analytics Assistant

The system is an AI-powered analytics assistant that allows non-technical users to ask business questions using natural language. The system dynamically discovers database schema, generates SQL using an LLM, validates the generated SQL against security rules, executes approved queries using a read-only database connection, and presents understandable results.

The system must prioritize correctness, security, maintainability, and reproducibility over unnecessary feature complexity.

---

## 2. Core System Workflow

```text
User Question
      ↓
Schema Discovery
      ↓
Relevant Schema Context
      ↓
LLM SQL Generation
      ↓
SQL Validation & Guardrails
      ↓
Read-Only Query Execution
      ↓
Result Processing
      ↓
Natural Language Explanation
      ↓
User
```

---

## 3. Functional System Requirements

### 3.1 User Input

The system shall:

* Provide an interface for entering natural-language business questions.
* Accept questions related to the available database.
* Display query processing status.
* Handle empty or invalid user input gracefully.

### 3.2 Database

The system shall provide a realistic relational business database containing multiple related tables.

The database should contain:

* Customers
* Products
* Orders
* Order Items
* Appropriate relationships and foreign keys
* Realistic sample data

The database shall support analytical questions involving:

* Aggregation
* Filtering
* Sorting
* Grouping
* Joins
* Date-based analysis
* Ranking
* Basic comparisons

### 3.3 Schema Discovery

The system shall dynamically inspect the database schema.

Schema information should include:

* Table names
* Column names
* Data types
* Primary keys
* Foreign keys
* Table relationships

The system must not rely on hard-coded SQL answers for predefined questions.

### 3.4 Schema Context Selection

The system should identify the database tables and columns relevant to the user's question.

Only relevant schema information should be provided to the SQL-generation model where practical.

### 3.5 SQL Generation

The system shall use an LLM to convert the natural-language question into SQL.

Generated SQL must:

* Use only available tables and columns.
* Follow the configured database dialect.
* Prefer efficient queries.
* Be deterministic where possible.
* Contain only permitted operations.
* Not invent database structures.

### 3.6 SQL Validation

Every generated query shall pass through a validation layer before execution.

The validator shall check:

* SQL syntax
* Statement type
* Allowed operations
* Referenced tables
* Referenced columns where practical
* Multiple statements
* Destructive operations
* Query safety constraints

Only approved queries may reach the database.

### 3.7 Query Execution

Approved queries shall execute through a read-only database connection.

The system shall:

* Execute validated queries.
* Apply configurable query limits/timeouts where appropriate.
* Capture database errors.
* Prevent unauthorized write operations.
* Return structured results.

### 3.8 Result Display

The interface shall display:

* Generated SQL
* Query results
* Column names
* Number of returned records where appropriate
* Query execution status
* Relevant errors

### 3.9 Natural Language Explanation

The system shall convert query results into a concise natural-language explanation.

The explanation should:

* Directly answer the user's question.
* Use the returned data as its source.
* Avoid inventing facts.
* Mention important limitations where applicable.

### 3.10 Error Handling

The system shall handle:

* Invalid user questions
* Invalid SQL
* SQL validation failures
* Database execution errors
* LLM failures
* Timeouts
* Empty results

Errors must be presented in an understandable manner.

### 3.11 Query Logging

The system shall log relevant query activity, including where appropriate:

* User question
* Generated SQL
* Validation result
* Execution status
* Error information
* Timestamp
* Execution duration

Sensitive information must not be unnecessarily stored in logs.

---

## 4. Optional Functional Requirements

The following features are optional and should only be implemented after the MVP is stable:

* Query repair loop
* Chart generation
* Query explanation mode
* Saved questions
* Query history
* Role-based database permissions

---

## 5. Non-Functional Requirements

### 5.1 Security

The system must prevent destructive database operations and use a read-only database execution account.

### 5.2 Reliability

The core workflow should operate consistently across a defined test set of business questions.

### 5.3 Maintainability

The application should use modular components with clear separation between:

* API
* LLM integration
* Schema discovery
* SQL validation
* Database execution
* Result processing
* Logging
* Frontend

### 5.4 Performance

The system should avoid unnecessary database and LLM calls and should provide reasonable response times for normal analytical questions.

### 5.5 Reproducibility

The project shall provide:

* Dependency definitions
* Environment configuration
* Database initialization
* Seed data
* Setup instructions
* Example queries
* Test scenarios

### 5.6 Documentation

The repository shall contain documentation covering:

* Problem statement
* Architecture
* Technology stack
* Setup
* Usage
* Validation
* Testing
* Limitations
* Future improvements

---

## 6. Deployment Requirements

The application should be containerizable using Docker.

A recommended deployment structure is:

```text
Frontend
   ↓
Backend API
   ↓
LLM Provider
   ↓
SQL Validation Layer
   ↓
Read-Only Database
```

Environment-specific values such as API keys and database credentials must be supplied through environment variables.

---

## 7. Acceptance Requirements

The system shall demonstrate that it can:

1. Answer a defined set of business questions.
2. Dynamically use database schema information.
3. Generate valid SQL.
4. Reject unsafe SQL.
5. Execute approved queries using read-only access.
6. Handle invalid SQL and database errors.
7. Present understandable results.
8. Document known limitations.

---

## 8. MVP Boundary

The MVP is considered complete when the complete workflow operates reliably:

```text
Natural Language
      ↓
Schema Context
      ↓
SQL Generation
      ↓
SQL Validation
      ↓
Read-Only Execution
      ↓
Results
      ↓
Explanation
```

Stretch features must not delay completion of this core workflow.
