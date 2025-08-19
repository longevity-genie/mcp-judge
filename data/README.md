# MCP Judge API Examples

This directory contains examples demonstrating how to use the new judge API based on just-agents BaseAgent.

## Core Concepts

The MCP Judge API is inspired by the judgement library and provides:

- **Structured Judgments**: All judgments use Pydantic models for type safety
- **BaseAgent Integration**: Built on just-agents for LLM interaction
- **Multiple Judge Types**: Boolean, numerical, and likert scale scoring
- **Jury Aggregation**: Combine multiple judges with various voting methods

## Quick Start

### Individual Judge

```python
from mcp_judge import BaseJudge, Judgment
from just_agents.llm_options import GEMINI_2_5_PRO

class MyJudge(BaseJudge):
    def judge(self, input_text: str, output: str = None, 
              expected: str = None, context: dict = None) -> Judgment:
        prompt = f"Evaluate: {input_text}\nResponse: {output}"
        return self._judge(prompt)

# Create judge using predefined LLMOptions (recommended)
judge = MyJudge.create_judge(
    model="gemini/gemini-2.5-pro",
    score_type="boolean",
    temperature=0.0
)

# Or use predefined options directly
judge = MyJudge(
    llm_options=GEMINI_2_5_PRO,
    score_type="boolean"
)

# Evaluate
result = judge.judge(
    input_text="What is 2+2?",
    output="2+2 equals 4",
    expected="4"
)

print(f"Score: {result.score}")
print(f"Reasoning: {result.reasoning}")
```

### MCP-Specific Judge

```python
from mcp_judge import MCPJudgeAgent
from just_agents.llm_options import GEMINI_2_5_PRO

# Create MCP judge
mcp_judge = MCPJudgeAgent.create_mcp_judge(
    model="gemini/gemini-2.5-pro",
    temperature=0.0
)

# Or use predefined options
mcp_judge = MCPJudgeAgent(
    llm_options=GEMINI_2_5_PRO,
    score_type="boolean"
)

# Evaluate tool usage
result = mcp_judge.judge(
    input_text="Search for Python docs",
    output="I used search_tool with query='Python documentation'",
    context={
        "expected_tools": ["search_tool"],
        "expected_parameters": {"query": "Python documentation"}
    }
)
```

### Jury System

```python
from mcp_judge import Jury, BaseJudge
from just_agents.llm_options import GEMINI_2_5_PRO, GEMINI_2_5_FLASH

# Create multiple judges using predefined options
judges = [
    ContentJudge(llm_options=GEMINI_2_5_PRO, score_type="boolean"),
    AccuracyJudge(llm_options=GEMINI_2_5_FLASH, score_type="numerical"),
    MCPJudgeAgent(llm_options=GEMINI_2_5_PRO, score_type="boolean")
]

# Create jury
jury = Jury(judges=judges, voting_method="majority")

# Get aggregated verdict
verdict = jury.vote(
    input_text="Question",
    output="Response",
    expected="Expected response"
)

print(f"Final score: {verdict.score}")
print(f"Individual judgments: {len(verdict.judgments)}")
```

## Available Voting Methods

- **majority**: Most common score wins
- **average**: Average of numerical scores
- **weighted_average**: Weighted average (requires weights parameter)
- **median**: Median of numerical scores

## Score Types

- **boolean**: True/False evaluations
- **numerical**: 0+ numerical scores
- **likert**: Categorical scores ("poor", "fair", "good", "excellent")

## Environment Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Set up API keys:
   ```bash
   # Copy the template file and edit with your actual keys
   cp .env.template .env
   
   # Or set environment variables directly
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   export GOOGLE_API_KEY="your-key"
   ```

3. Run examples:
   ```bash
   uv run python examples/judge_api_demo.py
   ```

## Migration from Legacy API

The new API is compatible with the existing MCP Judge functionality:

```python
# Legacy
from mcp_judge import JudgeAgent

# New API (recommended)
from mcp_judge import MCPJudgeAgent

# Both support similar interfaces
judge = MCPJudgeAgent.create_mcp_judge(model="gemini/gemini-2.5-pro")
result = judge.evaluate_legacy_format(
    question="...",
    generated_answer="...",
    reference_answer="...",
    expected_tools=["tool1"],
    expected_parameters={"param": "value"}
)
```

## Files

- `judge_api_demo.py`: Complete demonstration of all features
- `README.md`: This documentation

## Next Steps

- Explore the structured output capabilities
- Implement custom judges for specific evaluation needs
- Use jury systems for more robust evaluations
- Integrate with existing MCP testing workflows
