from typing import Any, Dict, List, Optional

from just_agents.base_agent import BaseAgent
from litellm import BaseModel

class Judgement(BaseModel):
    passed: bool
    reason: Optional[str] | List[str]
    raw_result: str

class JudgeAgent(BaseAgent):

    def evaluate(
        self,
        *,
        question: str,
        generated_answer: str,
        reference_answer: str,
        expected_tools: Optional[List[str]],
        expected_parameters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate a generated answer against a reference and expected MCP tool usage.

        Returns a dict: {"passed": bool, "reason": Optional[str], "raw_result": str}
        """
        prompt = f"""You are evaluating whether a generated answer correctly addresses a question and uses the expected MCP tools with proper parameters.

Question:
{question.strip()}

Generated Answer (with tool calls):
{str(generated_answer).strip()}

Reference Answer:
{str(reference_answer).strip()}

Expected MCP Tools:
{str(expected_tools)}

Expected Parameters:
{str(expected_parameters)}

Evaluate the generated answer and provide your judgment as a JSON object with the following structure:
- "passed": boolean indicating if the answer passes evaluation (true/false)
- "reason": string explaining your reasoning (optional, but recommended for failed cases)
- "raw_result": string containing the raw evaluation details

Consider these criteria:
1. Does the generated answer accurately address the question?
2. Are the expected MCP tools being used correctly?
3. Are the tool parameters used appropriately?
4. Is the answer factually consistent with the reference answer?

Respond only with a valid JSON object matching the required structure."""
        
        result = self.query_structural(prompt, parser=Judgement, enforce_validation=True)
        return {
            "passed": result.passed,
            "reason": result.reason,
            "raw_result": result.raw_result
        }
