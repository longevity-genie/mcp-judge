"""CLI tool for evaluating MCP server performance using LLM as a judge approach."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import track
from eliot import start_action

from mcp_judge.judge import JudgeAgent


app = typer.Typer(help="MCP Judge - CLI tool for evaluating MCP server performance")
console = Console()


def load_questions_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load questions from a JSON file."""
    with start_action(action_type="load_questions", file_path=str(file_path)):
        try:
            with open(file_path, 'r') as f:
                questions = json.load(f)
            console.print(f"✅ Loaded {len(questions)} questions from {file_path}")
            return questions
        except Exception as e:
            console.print(f"❌ Error loading questions from {file_path}: {e}")
            raise typer.Exit(1)


def create_judge(profiles_file: Path, judge_name: str = "GeminiJudgeAgent") -> JudgeAgent:
    """Create and load a judge agent from profiles."""
    with start_action(action_type="create_judge", profiles_file=str(profiles_file), judge_name=judge_name):
        try:
            judge: JudgeAgent = JudgeAgent.auto_load(
                section_name=judge_name,
                file_path=profiles_file,
                parent_section="agent_profiles"
            )
            console.print(f"✅ Loaded judge: {judge.shortname}")
            console.print(f"Model: {judge.llm_options.get('model', 'N/A')}")
            return judge
        except Exception as e:
            console.print(f"❌ Error loading judge: {e}")
            raise typer.Exit(1)


@app.command()
def evaluate(
    questions_file: str = typer.Argument(..., help="Path to the questions JSON file"),
    judge_name: str = typer.Option("GeminiJudgeAgent", "--judge", "-j", help="Name of the judge agent to use"),
    profiles_file: Optional[str] = typer.Option(None, "--profiles", "-p", help="Path to agent profiles YAML file"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Path to save evaluation results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """Evaluate questions using the specified judge agent."""
    
    # Set up paths
    questions_path = Path(questions_file)
    if not questions_path.exists():
        console.print(f"❌ Questions file not found: {questions_path}")
        raise typer.Exit(1)
    
    if profiles_file:
        profiles_path = Path(profiles_file)
    else:
        # Default to agent_profiles.yaml in the same directory as this script
        profiles_path = Path(__file__).parent / "agent_profiles.yaml"
    
    if not profiles_path.exists():
        console.print(f"❌ Profiles file not found: {profiles_path}")
        raise typer.Exit(1)
    
    # Load questions and create judge
    questions = load_questions_from_file(questions_path)
    judge = create_judge(profiles_path, judge_name)
    
    # Perform evaluations
    results = []
    passed_count = 0
    
    console.print(f"\n🧪 Evaluating {len(questions)} questions...")
    
    for i, question_data in enumerate(track(questions, description="Evaluating questions...")):
        with start_action(action_type="evaluate_question", question_index=i):
            question = question_data.get("question", "")
            generated_answer = question_data.get("answer", "")
            reference_answer = question_data.get("reference_answer", generated_answer)
            expected_tools = question_data.get("expected_tools", [])
            expected_parameters = question_data.get("expected_parameters", {})
            
            try:
                result = judge.evaluate(
                    question=question,
                    generated_answer=generated_answer,
                    reference_answer=reference_answer,
                    expected_tools=expected_tools,
                    expected_parameters=expected_parameters
                )
                
                result["question_index"] = i
                result["question"] = question
                result["generated_answer"] = generated_answer
                result["expected_tools"] = expected_tools
                result["expected_parameters"] = expected_parameters
                
                results.append(result)
                
                if result["passed"]:
                    passed_count += 1
                
                if verbose:
                    status = "✅ PASSED" if result["passed"] else "❌ FAILED"
                    console.print(f"Question {i+1}: {status}")
                    if not result["passed"] and result["reason"]:
                        console.print(f"  Reason: {result['reason']}")
                        
            except Exception as e:
                console.print(f"❌ Error evaluating question {i+1}: {e}")
                results.append({
                    "question_index": i,
                    "question": question,
                    "passed": False,
                    "reason": f"Evaluation error: {str(e)}",
                    "raw_result": "",
                    "error": True
                })
    
    # Display summary
    console.print(f"\n📊 Evaluation Summary:")
    console.print(f"Total questions: {len(questions)}")
    console.print(f"Passed: {passed_count}")
    console.print(f"Failed: {len(questions) - passed_count}")
    console.print(f"Success rate: {passed_count / len(questions) * 100:.1f}%")
    
    # Create detailed results table
    table = Table(title="Evaluation Results")
    table.add_column("Question #", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Question", style="dim", max_width=50)
    table.add_column("Reason", style="dim", max_width=40)
    
    for result in results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        question_preview = result["question"][:47] + "..." if len(result["question"]) > 50 else result["question"]
        reason = result.get("reason", "")[:37] + "..." if result.get("reason") and len(result.get("reason", "")) > 40 else result.get("reason", "")
        
        table.add_row(
            str(result["question_index"] + 1),
            status,
            question_preview,
            reason
        )
    
    console.print(table)
    
    # Save results if output file specified
    if output_file:
        output_path = Path(output_file)
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            console.print(f"\n💾 Results saved to: {output_path}")
        except Exception as e:
            console.print(f"❌ Error saving results: {e}")


@app.command()
def test():
    """Run a simple test evaluation to verify the judge is working."""
    
    # Path to agent profiles YAML
    profiles_file = Path(__file__).parent / "agent_profiles.yaml"
    
    console.print(f"Loading judge from: {profiles_file}")
    
    # Load judge from profiles using inherited auto_load
    judge = create_judge(profiles_file)
    
    # Test evaluation
    console.print("\n🧪 Testing evaluation...")
    
    question = "How do I list files in a directory?"
    generated_answer = "You can use the `ls` command to list files in a directory."
    reference_answer = "Use the `ls` command or the file browser tool to list directory contents."
    expected_tools = ["file_browser"]
    expected_parameters = {"path": "/some/directory"}
    
    result = judge.evaluate(
        question=question,
        generated_answer=generated_answer,
        reference_answer=reference_answer,
        expected_tools=expected_tools,
        expected_parameters=expected_parameters
    )
    
    console.print(f"\n📊 Test Result:")
    status = "✅ PASSED" if result['passed'] else "❌ FAILED"
    console.print(f"Status: {status}")
    console.print(f"Raw result: {result['raw_result']}")
    if result['reason']:
        console.print(f"Reason: {result['reason']}")


def main():
    """Main entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
