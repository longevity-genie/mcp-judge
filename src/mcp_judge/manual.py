import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import typer
from dotenv import load_dotenv
from just_agents.just_tool import JustToolFactory, JustMCPServerParameters
from just_agents.data_classes import MCPServerConfig
from just_agents.base_agent import BaseAgent
from just_agents import llm_options
from just_agents.just_tool import JustMCPTool
from mcp_judge.judge import JudgeAgent

app = typer.Typer(help="MCP Judge - A tool for querying biological data using MCP agents")

def get_project_paths() -> tuple[Path, Path]:
    """Get project root and data directory paths."""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # Go up from src/mcp_judge/ to project root
    data_dir = project_root / "data"
    return project_root, data_dir

def load_environment(env_file: Optional[Path] = None) -> None:
    """Load environment variables from .env file."""
    if env_file and env_file.exists():
        # Load from user-specified .env file
        load_dotenv(env_file)
        typer.echo(f"Loaded environment from {env_file}")
    else:
        # Try to load from project root .env file
        project_root, _ = get_project_paths()
        default_env_file = project_root / ".env"
        if default_env_file.exists():
            load_dotenv(default_env_file)
            typer.echo(f"Loaded environment from {default_env_file}")
        else:
            # Load from current directory or system env
            load_dotenv()

def resolve_path(path_input: Optional[str], default_filename: str, data_dir: Path) -> Path:
    """Resolve path input to actual Path, using project defaults if not specified."""
    if path_input:
        # User provided a path - use it as is (absolute) or relative to data_dir
        user_path = Path(path_input)
        if user_path.is_absolute():
            return user_path
        else:
            return data_dir / user_path
    else:
        # Use default path relative to data directory
        return data_dir / default_filename

@app.command()
def judge(
    question_indices: Optional[str] = typer.Option(
        "all",
        "--questions",
        "-q",
        help="Question indices to ask (e.g., '1,3,5' or 'all'). Default: 'all'. Use --list to see available questions."
    ),
    config_file: Optional[str] = typer.Option(
        None, 
        "--config", 
        "-c", 
        help="Path to MCP config file (relative to data dir or absolute). Default: opengenes-mcp-config-stdio.json"
    ),
    questions_file: Optional[str] = typer.Option(
        None,
        "--questions-file",
        "-f", 
        help="Path to questions file (relative to data dir or absolute). Default: open-genes-questions.json"
    ),
    env_file: Optional[str] = typer.Option(
        None,
        "--env",
        "-e",
        help="Path to .env file (relative to data dir or absolute). Default: project root .env"
    ),
    agent_profiles_file: Optional[str] = typer.Option(
        None,
        "--agent-profiles",
        "-p",
        help="Path to agent profiles file (relative to data dir or absolute). Default: data/agent_profiles.yaml"
    ),
    agent_profile_section: Optional[str] = typer.Option(
        "GeminiJudgeAgent",
        "--agent-profile",
        "-a",
        help="Section name in agent profiles file. Default: GeminiJudgeAgent"
    )
) -> None:
    """Judge MCP agent responses using predefined biological questions from open-genes dataset. By default, asks all questions."""
    
    # Establish relative paths based on current file location
    project_root, data_dir = get_project_paths()
    
    # Load environment variables
    env_path = resolve_path(env_file, ".env", project_root) if env_file else None
    load_environment(env_path)
    
    # Resolve file paths using helper function
    config_path = resolve_path(config_file, "opengenes-mcp-config-stdio.json", data_dir)
    questions_path = resolve_path(questions_file, "open-genes-questions.json", data_dir)
    profiles_path = resolve_path(agent_profiles_file, "agent_profiles.yaml", data_dir)
    


    # Load MCP configuration
    if not config_path.exists():
        typer.echo(f"Error: Config file not found at {config_path}", err=True)
        raise typer.Exit(1)
    
    mcp_config = config_path.read_text(encoding="utf-8")
    typer.echo(f"Loaded MCP config from {config_path}")
    
    # Load open-genes questions - required for this tool
    if not questions_path.exists():
        typer.echo(f"Error: Questions file not found at {questions_path}", err=True)
        raise typer.Exit(1)
    
    with open(questions_path, 'r', encoding='utf-8') as f:
        open_genes_questions: List[Dict[str, Any]] = json.load(f)
    typer.echo(f"Loaded {len(open_genes_questions)} questions from {questions_path}")

    # Check agent profiles file exists
    if not profiles_path.exists():
        typer.echo(f"Error: Agent profiles file not found at {profiles_path}", err=True)
        raise typer.Exit(1)

    # Validate agent profile section exists
    with open(profiles_path, 'r', encoding='utf-8') as f:
        profiles_data = yaml.safe_load(f)

    if 'agent_profiles' not in profiles_data:
        typer.echo(f"Error: Invalid agent profiles file format - missing 'agent_profiles' section", err=True)
        raise typer.Exit(1)

    if agent_profile_section not in profiles_data['agent_profiles']:
        available_sections = list(profiles_data['agent_profiles'].keys())
        typer.echo(f"Error: Agent profile section '{agent_profile_section}' not found in {profiles_path}", err=True)
        typer.echo(f"Available sections: {', '.join(available_sections)}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Using agent profile section: {agent_profile_section}")
    
    
    # Parse question indices (defaults to "all" if not specified)
    if not question_indices:
        question_indices = "all"
    
    # Determine which questions to ask
    questions_to_ask: List[Dict[str, Any]] = []
    if question_indices.lower() == "all":
        questions_to_ask = open_genes_questions
    else:
        try:
            indices = [int(idx.strip()) for idx in question_indices.split(",")]
            for idx in indices:
                if 1 <= idx <= len(open_genes_questions):
                    questions_to_ask.append(open_genes_questions[idx - 1])
                else:
                    typer.echo(f"Warning: Question index {idx} is out of range (1-{len(open_genes_questions)})", err=True)
        except ValueError:
            typer.echo("Error: Invalid question indices format. Use comma-separated numbers (e.g., '1,3,5') or 'all'.", err=True)
            raise typer.Exit(1)
    
    if not questions_to_ask:
        typer.echo("Error: No valid questions selected.", err=True)
        raise typer.Exit(1)
    
    # Create tools from the MCP configurationprf
    
    if not profiles_path.exists():
        typer.echo(f"Error: Agent profiles file not found at {profiles_path}", err=True)
        raise typer.Exit(1)

    # TODO: For NW1: clean tool Factory to have a single public method to have tools outside agents
    # TODO: For NW2: tools_list = agent.list_tools() - listing now needs agent, must be bound to tools
    # TODO: For NW3: convoluted jsons config handling, fewer options - more clarity\
    # TODO: For NW4: Add asterisk yaml support
    # TODO: For NW5: Clearly analyze teo usecases: yaml and code, what;s needed strip everything else or it becomes Java
    
    mcp_config = JustMCPServerParameters( 
        mcp_client_config=mcp_config,
    )
    # tool_dict: Dict[str, JustMCPTool] = JustToolFactory.create_tools_dict(tools=[mcp_config])
    tool_dict: Dict[str, JustMCPTool] = JustToolFactory.create_tools_from_mcp(config=mcp_config)
    
    tools = list(tool_dict.values())

    # Create agent
    # profiles_path is already resolved above and checked for existence
    # Execute questions
    typer.echo(f"\nAsking {len(questions_to_ask)} question(s):")
    typer.echo("=" * 60)

    for i, question_data in enumerate(questions_to_ask[:1]):
        agent = BaseAgent(tools=tools, llm_options=llm_options.GEMINI_2_5_PRO)
        question = question_data.get('question', 'No question text')
        expected_answer = question_data.get('answer', 'No expected answer')
        
        typer.echo(f"\nQuestion {i}: {question}")
        typer.echo("-" * 40)
        
        result = agent.query(question)
        agent.memory.pretty_print_all_messages()
        #typer.echo(f"Agent Response:\n{result}")
        
        #typer.echo(f"\nExpected Answer:\n{expected_answer}")
        typer.echo("=" * 60)
        typer.echo(f"Judging...")

        judge_agent: JudgeAgent = JudgeAgent.from_yaml(section_name=agent_profile_section, parent_section='agent_profiles', file_path=profiles_path)
   
        if judge_agent is None:
            typer.echo(f"Error: Failed to load judge agent from {profiles_path}", err=True)
            raise typer.Exit(1)
        else:
            typer.echo(f"Loaded judge agent from {profiles_path}")
            
        #judge_agent.evaluate(
        #    question=question,
        #    generated_answer=result,
        #    reference_answer=expected_answer
        #)
    
    from just_agents.mcp_client import MCPClientLocator
    all_clients = MCPClientLocator().get_all_clients()
    typer.echo(f"There are {len(all_clients)} clients")
    typer.echo(f"All clients: {all_clients}")






if __name__ == '__main__':
    app()
