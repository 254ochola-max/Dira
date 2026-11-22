"""
agent.py - the complete Career Compass agent.

  LLM (brain)  +  tools (hands)  +  instructions  +  memory  +  THE LOOP

Run:  python agent.py
Then say things like:
  I'm studying nursing in Nakuru. Where can I build my skills, what jobs
  can I get, what do they pay, and what is open near me?
"""

import os
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
MAX_STEPS = 8  # safety limit: the agent may loop at most this many times

# ---------------------------------------------------------------------------
# Instructions (the "system prompt"): who the agent is and how it behaves
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""You are Dira, a friendly career guide for students and recent graduates.
Today's date is {date.today():%A %d %B %Y}.
Rules:
- You need two things: the student's COURSE and the TOWN they live in. If either is
  missing, ask for it in one short question before using tools.
- Use your tools for learning platforms, jobs, salaries and listings. Never guess those.
- You may call several tools before answering.
- Salaries are always APPROXIMATE. Say so, give the range in KES per month, and
  mention that pay varies by employer and experience.
- Never invent a job listing, company or link. Only share what a tool returned.
- Nearby employers are places to approach (walk-in, internship, attachment), not
  confirmed vacancies. Say that clearly.
- If a tool returns an error, say so honestly instead of making things up.
- Finish with a short, clear plan using these headings: Skills to build, Jobs you
  can aim for, Where the jobs are, Approximate pay, Open now and nearby,
  Your next 3 steps.

Formatting rules
- do not use markdown formatting, give reply in plain text"""

config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
)

# Small helper for coloured terminal output, so students can SEE each step
BLUE, YELLOW, GREEN, GREY, RESET = "\033[94m", "\033[93m", "\033[92m", "\033[90m", "\033[0m"


def run_tool(name: str, args: dict, step: int) -> dict:
    """Run the Python function the model asked for. Never crash the agent."""
    print(f"{BLUE}  step {step} | calling {name}({args}){RESET}")
    if name not in TOOL_FUNCTIONS:
        output = {"error": f"Unknown tool '{name}'"}
    else:
        try:
            output = TOOL_FUNCTIONS[name](**args)
        except Exception as e:  # network down, bad arguments, ...
            output = {"error": str(e)}
    print(f"{GREY}           -> {str(output)[:110]}{RESET}")
    return output


def run_agent(question: str, messages: list) -> str:
    """THE AGENT LOOP: think -> act -> observe, until the model answers."""
    messages.append(types.Content(role="user",
                                  parts=[types.Part(text=question)]))

    for step in range(1, MAX_STEPS + 1):
        # THINK: send the whole conversation so far to the LLM
        response = client.models.generate_content(
            model=MODEL, contents=messages, config=config)
        messages.append(response.candidates[0].content)   # remember its reply

        # No tool requests? Then the model has its final answer. Done!
        if not response.function_calls:
            return response.text

        # ACT + OBSERVE: run every tool it asked for, collect the results
        results = []
        for call in response.function_calls:
            output = run_tool(call.name, dict(call.args), step)
            results.append(types.Part(function_response=types.FunctionResponse(
                id=call.id, name=call.name, response={"result": output})))

        # Hand the results back; the loop goes round again
        messages.append(types.Content(role="user", parts=results))

    return "Sorry, I hit my step limit before finishing. Try a simpler question."


def main():
    print(f"{GREEN}Dira career agent ready ({MODEL}).{RESET}")
    print(f"{GREY}Tools: {', '.join(TOOL_FUNCTIONS)}. Type 'quit' to exit.{RESET}\n")
    messages = []  # MEMORY: the conversation history, kept between questions
    while True:
        question = input(f"{YELLOW}You: {RESET}").strip()
        if question.lower() in {"quit", "exit", "q"}:
            break
        if not question:
            continue
        checkpoint = len(messages)
        try:
            answer = run_agent(question, messages)
        except Exception as e:
            del messages[checkpoint:]  # forget the half-finished turn
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                answer = "Rate limit reached on the free tier. Wait a minute and try again."
            else:
                answer = f"Something went wrong: {e}"
        print(f"\n{GREEN}Dira:{RESET} {answer}\n")


if __name__ == "__main__":
    main()
