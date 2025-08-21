# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Judge is a UV-based CLI tool for benchmarking MCP (Model Context Protocol) servers using an LLM-as-a-judge approach. It evaluates how well AI agents use MCP tools by comparing generated responses against expected tool usage patterns.

## Common Commands

### Installation and Setup
```bash
# Install dependencies
uv sync

# Set up environment variables (copy .env.template to .env first)
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key" 
export GOOGLE_API_KEY="your-key"
```

### Running the Tool
```bash
# Basic evaluation with default settings (Gemini 2.5 Pro)
uv run mcp-judge evaluate data/sample_questions.json

# Test multiple models
uv run mcp-judge run data/sample_questions.json \
  --model gemini/gemini-2.5-pro \
  --model gemini/gemini-2.5-flash \
  --model claude-3-5-sonnet

# With custom judge and output
uv run mcp-judge evaluate data/sample_questions.json \
  --judge GeminiJudgeAgent \
  --output results.json \
  --verbose

# Test the judge setup
uv run mcp-judge test
```

### MCP Server Integration
```bash
# Use custom MCP server configuration
uv run mcp-judge run data/sample_questions.json \
  --mcp-config /path/to/mcp-config.json

# Load built-in pharmacology tools
uv run mcp-judge run data/sample_questions.json --pharmacology-tools

# Load custom tools module
uv run mcp-judge run data/sample_questions.json \
  --tools-module my_tools.py \
  --tool-name my_search_tool
```

## Architecture

### Core Components

- **`src/mcp_judge/judge.py`**: Contains the `JudgeAgent` class that inherits from `BaseAgent` (just-agents). Implements structured evaluation using Pydantic models for JSON validation.

- **`src/mcp_judge/run.py`**: CLI application built with Typer. Handles command-line interface, question loading, judge initialization, and result presentation with Rich formatting.

- **`src/mcp_judge/agent_profiles.yaml`**: Configuration for judge agents including model settings, system prompts, and LLM options. Currently defines `GeminiJudgeAgent` with Gemini 2.5 Flash model.

### Evaluation Flow

1. **Question Loading**: JSON files with question/expected_tools/expected_parameters/answer structure
2. **Judge Creation**: Loads judge agent from YAML profiles using `BaseAgent.auto_load()`
3. **Evaluation**: Judge compares generated answers against expected MCP tool usage
4. **Structured Output**: Returns JSON with `passed`, `reason`, and `raw_result` fields
5. **Results Display**: Rich terminal tables and optional JSON export

### Key Dependencies

- **just-agents**: Base agent framework for LLM interactions
- **litellm**: Multi-model LLM interface with structured output support
- **typer**: CLI framework with type hints
- **rich**: Terminal output formatting and progress tracking
- **pydantic**: Data validation and JSON parsing
- **eliot**: Structured logging with action context

### Question Format

Questions in `data/` directory follow this structure:
```json
{
  "question": "Task description",
  "expected_tools": ["tool_name"],
  "expected_parameters": {"param": "value"},
  "answer": "Reference response with expected tool usage"
}
```

### Judge Evaluation Criteria

The judge evaluates based on:
1. **Correct Tool Usage**: Right MCP tools for the task
2. **Parameter Accuracy**: Appropriate and well-formed parameters  
3. **Logical Workflow**: Sensible tool usage sequence
4. **Information Retrieval**: Essential data retrieved correctly

Returns structured judgment with pass/fail status, reasoning, and detailed evaluation.