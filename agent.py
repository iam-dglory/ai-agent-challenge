import os
import subprocess
import operator
import pandas as pd
import fitz  # PyMuPDF
import sys
from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from dotenv import load_dotenv
import argparse

load_dotenv()

# LLM setup (uses Groq or OpenAI)
if os.getenv("GROQ_API_KEY"):
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama3-70b-8192", temperature=0.0)
elif os.getenv("OPENAI_API_KEY"):
    from langchain_openai import ChatOpenAI
    llm = ChatGroq(model="llama3-70b-8192", temperature=0.0)
else:
    raise ValueError("No API key found. Please set GROQ_API_KEY or OPENAI_API_KEY in .env.")

# State definition
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, ToolMessage]], operator.add]
    code: str
    target: str
    attempts: int
    decision: str

# Tool to run tests
def run_tests(target: str) -> str:
    """
    Runs pytest for the specified bank parser.
    """
    try:
        command = ["pytest", f"tests/test_{target}.py", "-v"]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return "Test Passed"
        else:
            return f"Test Failed. Output:\n{result.stdout}\nError:\n{result.stderr}"
    except Exception as e:
        return f"Test Failed with exception: {str(e)}"

# Nodes
def plan_generator(state: AgentState) -> dict:
    print("---PLANNING---")
    plan_prompt = f"""
    You are an expert coding agent for writing bank statement parsers.
    Analyze the sample PDF text and expected CSV to plan how to parse the PDF into the exact DF.
    Focus on handling table structure, empty fields, data types, and matching the schema.
    If previous attempts failed, use the last test output to plan fixes (e.g., change Camelot flavor, clean rows, handle NaNs).
    Previous attempts: {state['attempts']}
    Last test output: {state['messages'][-1].content if state['attempts'] > 0 else 'None'}
    Provide a concise, actionable plan for generating the code (e.g., 'Use Camelot with lattice flavor, concat tables, set columns, convert types, handle NaNs').
    """
    response = llm.invoke(state['messages'] + [HumanMessage(content=plan_prompt)])
    return {"messages": [response]}

def code_generator(state: AgentState) -> dict:
    print("---GENERATING CODE---")
    code_prompt = f"""
    You are an expert Python coder.
    Follow this plan exactly: {state['messages'][-1].content}
    Write the full code for custom_parsers/{state['target']}_parser.py.
    It must define def parse(pdf_path: str) -> pd.DataFrame:
    - Import necessary libs (pandas, camelot, os, fitz if needed).
    - Handle file not found.
    - Extract tables from PDF.
    - Clean DF to match schema: Date (datetime), Description (str), Debit Amt (float or NaN), Credit Amt (float or NaN), Balance (float).
    - Ensure NaN for empty Debit/Credit.
    - Do not add extra rows/columns.
    Output only the Python code, no explanations.
    """
    response = llm.invoke(state['messages'] + [HumanMessage(content=code_prompt)])
    code = response.content.strip()
    file_path = f"custom_parsers/{state['target']}_parser.py"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(code)
    return {"messages": [AIMessage(content="Code generated.")], "code": code}

def execute_and_test(state: AgentState) -> dict:
    print("---EXECUTING TESTS---")
    test_result = run_tests(state['target'])
    print(f"Test output:\n{test_result}")
    return {"messages": [ToolMessage(content=test_result, tool_call_id="run_tests")]}

def decision_maker(state: AgentState) -> dict:
    print("---MAKING DECISION---")
    test_output = state['messages'][-1].content
    if "Test Passed" in test_output:
        print("Test passed! Finalizing solution.")
        return {"decision": "finish"}
    state['attempts'] += 1
    if state['attempts'] >= 3:
        print("Maximum attempts reached. Exiting.")
        return {"decision": "fail"}
    print("Test failed. Retrying with self-correction...")
    return {"decision": "self-correct"}

# Graph setup
workflow = StateGraph(AgentState)
workflow.add_node("plan", plan_generator)
workflow.add_node("generate_code", code_generator)
workflow.add_node("execute_tests", execute_and_test)
workflow.add_node("decide", decision_maker)
workflow.set_entry_point("plan")
workflow.add_edge("plan", "generate_code")
workflow.add_edge("generate_code", "execute_tests")
workflow.add_edge("execute_tests", "decide")
workflow.add_conditional_edges(
    "decide",
    lambda state: state['decision'],
    {"self-correct": "plan", "finish": END, "fail": END}
)
app = workflow.compile()

# CLI entry
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Agent Challenge CLI")
    parser.add_argument("--target", required=True, help="Target bank (e.g., icici)")
    args = parser.parse_args()

    # Load sample data for prompt
    pdf_path = os.path.join("data", args.target, f"{args.target}_sample.pdf")
    csv_path = os.path.join("data", args.target, f"{args.target}_sample.csv")
    pdf_text = ""
    if os.path.exists(pdf_path):
        with fitz.open(pdf_path) as doc:
            for page in doc:
                pdf_text += page.get_text() + "\n"
    csv_text = ""
    if os.path.exists(csv_path):
        expected_df = pd.read_csv(csv_path)
        csv_text = expected_df.to_string(index=False)

    # Initial state
    initial_message = HumanMessage(content=f"Write a custom parser for {args.target} bank statement.\nSample PDF extracted text:\n{pdf_text}\n\nExpected output DataFrame (as string):\n{csv_text}")
    initial_state = {
        "messages": [initial_message],
        "code": "",
        "target": args.target,
        "attempts": 0,
        "decision": ""
    }

    # Run the graph
    for step in app.stream(initial_state):
        pass
