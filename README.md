# MCP Judge

A UV-based CLI tool for benchmarking the performance of MCP (Model Context Protocol) servers using LLM-as-a-judge approach with real-world questions.

## Features

- **Multi-Model Testing**: Test multiple LLM models simultaneously
- **Judge-Based Evaluation**: Uses an LLM judge to evaluate tool usage and response quality
- **MCP Tools Integration**: Supports loading custom MCP tools or built-in pharmacology tools
- **Rich Output**: Beautiful terminal output with progress tracking and detailed results
- **Flexible Configuration**: Customizable system prompts, judge prompts, and model settings
- **Export Results**: Save detailed results to JSON for further analysis

## Installation

```bash
cd mcp-judge
uv sync
```

## Usage

### Basic Usage

```bash
# Test with default settings (uses Gemini 2.5 Pro)
uv run mcp-judge run examples/sample_questions.json

# Test multiple models
uv run mcp-judge run examples/sample_questions.json \
  --model gemini/gemini-2.5-pro \
  --model gemini/gemini-2.5-flash \
  --model claude-3-5-sonnet

# Use custom judge model
uv run mcp-judge run examples/sample_questions.json \
  --judge-model gemini/gemini-2.5-pro \
  --model gemini/gemini-2.5-flash
```

### MCP Server Integration

Use the `--mcp-config` option to provide a JSON file with the MCP server configuration. This allows you to connect to any MCP-compliant server and specify which tools to use.

**Example `mcp-config.json`:**
```json
{
  "mcp_endpoint": "python -m your_project.server",
  "only_include_tools": [
    "search_targets_to_file",
    "search_ligands_to_file"
  ],
  "exclude_tools": [],
  "raise_on_incorrect_names": true
}
```

**Usage:**
```bash
uv run mcp-judge run examples/sample_questions.json \
  --mcp-config /path/to/your/mcp-config.json
```

This configuration will load the `search_targets_to_file` and `search_ligands_to_file` tools from the specified MCP server.

### Advanced Options

```bash
# Verbose output with detailed responses
uv run mcp-judge run questions.json --verbose

# Save detailed results to file
uv run mcp-judge run questions.json \
  --output results.json

# Adjust model temperatures
uv run mcp-judge run questions.json \
  --temperature 0.2 \
  --judge-temperature 0.0
```

## Question File Format

Questions should be provided in a JSON file with the following structure:

```json
[
  {
    "question": "Find dopamine-related targets and save them to dopamine_targets.json",
    "expected_tools": ["search_targets_to_file"],
    "expected_parameters": {
      "name": "dopamine",
      "filename": "dopamine_targets.json"
    },
    "answer": "Reference answer describing expected tool usage and behavior"
  }
]
```

### Required Fields

- `question`: The question/task to be performed
- `expected_tools`: List of tool names that should be used
- `expected_parameters`: Dictionary of expected parameters for the tools
- `answer`: Reference answer for comparison

## Judge Evaluation

The judge evaluates responses based on:

1. **Correct Tool Usage**: Whether the right MCP tools were called
2. **Parameter Accuracy**: Whether tool parameters are appropriate and well-formed
3. **Logical Workflow**: Whether tools are used in a sensible sequence
4. **Information Retrieval**: Whether essential information was retrieved correctly

The judge returns either "PASS" or "FAIL [reason]".

## MCP Tools Integration

### Built-in Pharmacology Tools

Use `--pharmacology-tools` to load pharmacology MCP tools:
- `search_targets_to_file`
- `search_ligands_to_file`
- `get_target_interactions_to_file`
- `get_ligand_interactions_to_file`

### Custom Tools

Create a Python module with your MCP tools and use `--tools-module`:

```python
# my_tools.py
def my_search_tool(query: str, filename: str) -> str:
    """Search and save results to file."""
    # Implementation here
    return "Search completed and saved to " + filename

def my_analysis_tool(data_id: int) -> str:
    """Analyze data by ID."""
    # Implementation here
    return f"Analysis completed for ID {data_id}"
```

Then load specific tools:
```bash
uv run mcp-judge run questions.json \
  --tools-module my_tools.py \
  --tool-name my_search_tool \
  --tool-name my_analysis_tool
```

## Example Output

```
✅ Loaded 3 questions from examples/sample_questions.json
✅ Loaded 4 pharmacology tools
✅ Available tools: search_targets_to_file, search_ligands_to_file, get_target_interactions_to_file, get_ligand_interactions_to_file
✅ Generated default system prompt from available tools
✅ Initialized judge agent with model: openai/gpt-4o
✅ Initialized test runner

🔄 Testing model: openai/gpt-4o-mini
Testing openai/gpt-4o-mini ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 3/3
  📊 Results: 3/3 passed (100.0%)

📋 Overall Results:
                    Model Comparison                    
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Model                ┃ Passed ┃ Total ┃ Pass Rate ┃ Status       ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ openai/gpt-4o-mini   │      3 │     3 │    100.0% │ 🟢 Excellent │
└──────────────────────┴────────┴───────┴───────────┴──────────────┘

💾 Detailed results saved to results.json
```

## Environment Setup

Set up your API keys by copying the template file and filling in your actual keys:

```bash
# Copy the template file
cp .env.template .env

# Edit .env and add your actual API keys
# OPENAI_API_KEY=your-actual-openai-key
# ANTHROPIC_API_KEY=your-actual-anthropic-key
# GOOGLE_API_KEY=your-actual-google-key
```

Alternatively, you can set environment variables directly:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key" 
export GOOGLE_API_KEY="your-google-key"
```

## Dependencies

- `just-agents>=0.8.2` - LLM agent framework
- `typer>=0.16.0` - CLI framework
- `eliot>=1.17.5` - Structured logging
- `rich>=13.0.0` - Rich terminal output
- `pydantic>=2.11.7` - Data validation
- `python-dotenv>=1.1.1` - Environment configuration

## License

Licensed under the same terms as the project.