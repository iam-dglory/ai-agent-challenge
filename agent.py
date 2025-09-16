import os
import shutil
import subprocess
import operator
import pandas as pd
import re
import fitz # PyMuPDF
from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for both Groq and OpenAI API keys to provide flexibility
if os.getenv("GROQ_API_KEY"):
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0.0)
elif os.getenv("OPENAI_API_KEY"):
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
else:
    raise ValueError("No API key found. Please set either GROQ_API_KEY or OPENAI_API_KEY in your .env file.")

# Define the graph state with a correct reducer for messages
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, ToolMessage]], operator.add]
    code: str
    target: str
    attempts: int

# Define the agent's tools
def run_tests(target: str) -> str:
    """Runs the test script for the specified bank parser."""
    try:
        result = subprocess.run(
            ["python", f"tests/test_{target}.py"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr

# Define the nodes of the graph
def plan_generator(state: AgentState) -> dict:
    """
    Generates a plan for the coding agent.
    """
    print("---PLANNING---")
    plan_prompt = f"""
    You are an expert coding agent tasked with writing a Python parser for a bank statement.
    The goal is to create a function `parse(pdf_path)` inside `custom_parsers/{state['target']}_parser.py`
    that takes a PDF file path and returns a pandas DataFrame with the same schema as
    `data/{state['target']}/{state['target']}_sample.csv`.
    The agent must:
    1. Read the PDF content.
    2. Use regular expressions or other methods to extract transaction data.
    3. Construct a pandas DataFrame from the extracted data.
    4. Return the DataFrame.

    Based on the previous attempts (if any) and the error message provided, create a plan
    to generate the correct code.
    Previous attempts: {state['attempts']}
    Last error: {state['messages'][-1].content if state['attempts'] > 0 else "None"}

    Your plan should be concise and actionable for the code generator.
    """
    
    response = llm.invoke([HumanMessage(content=plan_prompt)])
    return {"messages": [response]}

def code_generator(state: AgentState) -> dict:
    """
    Generates the Python code for the parser based on the plan.
    """
    print("---GENERATING CODE---")
    plan = state['messages'][-1].content
    code_prompt = f"""
    You are an expert Python programmer. Your task is to write the code for a bank statement parser
    based on the following plan and context.

    Context:
    - The parser must be in a file named `custom_parsers/{state['target']}_parser.py`.
    - The main function must be `parse(pdf_path: str) -> pd.DataFrame`.
    - The output DataFrame must match the schema of the CSV file in `data/{state['target']}/`.
    - You can use libraries like pandas, re, and PyMuPDF (fitz).
    - You should handle potential errors with a try-except block.

    Plan:
    {plan}

    Write the complete and correct Python code.
    """
    
    response = llm.invoke([HumanMessage(content=code_prompt)])
    code = response.content
    
    # Save the generated code to the file
    file_path = f"custom_parsers/{state['target']}_parser.py"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(code)
    
    return {"messages": [response], "code": code}

def execute_and_test(state: AgentState) -> dict:
    """
    Executes the generated code and runs the test script.
    """
    print("---EXECUTING TESTS---")
    test_result = run_tests(state['target'])
    print(f"Test output:\n{test_result}")
    
    return {"messages": [ToolMessage(content=test_result, tool_call_id="run_tests")]}

def decision_maker(state: AgentState) -> str:
    """
    Decides whether to retry, self-correct, or finish.
    """
    print("---MAKING DECISION---")
    test_output = state['messages'][-1].content
    if "Test Passed" in test_output:
        print("Test passed! Finalizing solution.")
        return "finish"
    
    state['attempts'] += 1
    if state['attempts'] >= 3:
        print("Maximum correction attempts reached. Exiting.")
        return "fail"
    
    print("Test failed. Retrying with self-correction...")
    return "self-correct"

# Build the graph
workflow = StateGraph(AgentState)

workflow.add_node("plan", plan_generator)
workflow.add_node("generate_code", code_generator)
workflow.add_node("execute_tests", execute_and_test)
workflow.add_node("decide", decision_maker)

# Set up the entry point
workflow.set_entry_point("plan")

# Add edges and conditional edges
workflow.add_edge("plan", "generate_code")
workflow.add_edge("generate_code", "execute_tests")
workflow.add_edge("execute_tests", "decide")
workflow.add_conditional_edges(
    "decide",
    decision_maker,
    {
        "self-correct": "plan",
        "finish": END,
        "fail": END
    }
)

app = workflow.compile()

# Main CLI entry point
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent-as-Coder Challenge CLI")
    parser.add_argument("--target", required=True, help="The target bank for the parser (e.g., icici)")
    args = parser.parse_args()

    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=f"Write a parser for the '{args.target}' bank.")],
        "code": "",
        "target": args.target,
        "attempts": 0
    }

    # Run the agent
    for step in app.stream(initial_state):
        pass
