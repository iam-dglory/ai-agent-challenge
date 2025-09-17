# AI Agent Challenge

Develop a coding agent that generates custom parsers for bank statement PDFs.

## 5-Step Run Instructions

1. Fork and clone the repo: `git clone https://github.com/your-username/ai-agent-challenge.git` and cd into it.
2. Install dependencies: `pip install -r requirements.txt` (includes langgraph, langchain-groq, pymupdf, camelot-py, pandas, pytest, etc.).
3. Set API key in .env (GROQ_API_KEY or OPENAI_API_KEY).
4. Run the agent: `python agent.py --target icici` (generates custom_parsers/icici_parser.py and self-tests/fixes).
5. Verify with manual test: `pytest tests/test_icici.py` (should pass green).

## Agent Diagram

The agent is a LangGraph-based loop for autonomous code generation: It starts with a planning node that analyzes the sample PDF text and expected CSV to create a parsing strategy (e.g., using Camelot for table extraction). The code generation node uses an LLM to write the parser.py file based on the plan. The execution node runs pytest on the generated parser against the sample. The decision node checks results—if failed, it self-corrects by re-planning (up to 3 attempts); if passed or max attempts reached, it ends. This enables generating custom parsers for new banks without manual changes.
