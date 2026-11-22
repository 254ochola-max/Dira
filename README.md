# Dira
Career Compass Agent is an AI-powered career assistant that recommends career paths, finds nearby internships, suggests course-related skills to improve, provides trusted learning platforms, and lists relevant job opportunities with estimated salaries to help students prepare for the job market.
# Career Compass Agent ("Dira")

A command-line AI agent that acts as a career guide for Kenyan students and recent graduates. Tell Dira your course and the town you live in, and she suggests:

- platforms to build your skills
- jobs and job destinations to aim for
- approximate salaries (KES per month)
- live job listings and the nearest real employers

Built with the Gemini API and plain Python functions as tools. The agent loop (think → act → observe) is written by hand in `agent.py`, so you can see exactly how an agent works.

## Example

```
You: I'm studying nursing in Nakuru. Where can I build my skills, what jobs can I get, what do they pay, and what is open near me?
```

Dira calls her tools, then replies with a plan: skills to build, jobs to aim for, where the jobs are, approximate pay, what is open nearby, and your next 3 steps.

## Requirements

- Python 3.10 or newer
- A free Gemini API key from <https://aistudio.google.com/apikey>
- Optional: a free Tavily key from <https://app.tavily.com> (turns on `web_search` and live Kenyan job-board results)

## Setup

**Windows (PowerShell)**

```powershell
git clone https://github.com/<your-username>/career-compass-agent.git
cd career-compass-agent\code

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

copy .env.example .env
```

**macOS / Linux**

```bash
git clone https://github.com/<your-username>/career-compass-agent.git
cd career-compass-agent/code

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

cp .env.example .env
```

Then open `.env` and paste your `GEMINI_API_KEY`. Never share or commit this file.

If PowerShell blocks the activate script, run this once in that terminal and try again:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

## Run

```bash
python check_setup.py     # confirms Python, packages, key and tools all work
python agent.py           # start chatting with Dira (type "quit" to exit)
```

## Configuration (`.env`)

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Powers the agent |
| `TAVILY_API_KEY` | No | Enables `web_search` and live Kenyan job-board results |
| `GEMINI_MODEL` | No | Switch model if you hit free-tier daily limits (default `gemini-3.5-flash`) |

## Project layout

```
code/
  step1_ask_llm.py        a plain LLM call: watch it guess about live jobs and pay
  step2_one_tool.py       one tool, one round trip done by hand
  tools.py                the tools and the tool menu given to the model
  agent.py                the full agent loop (think -> act -> observe)
  agent_sdk.py            the same agent, with the loop run by the Gemini SDK
  exercise_solutions.py   extra tools: country facts, save plan, skills gap
  check_setup.py          setup checker
  requirements.txt
  .env.example
```

Suggested order for learning: `step1_ask_llm.py` → `step2_one_tool.py` → `agent.py` → `agent_sdk.py`.

## The tools

| Tool | Source | What it does |
|---|---|---|
| `get_learning_platforms` | built-in list | where to build skills |
| `get_career_paths` | built-in list | jobs and job destinations |
| `get_salary_estimate` | built-in list | approximate pay (Kenya, KES) |
| `find_jobs` | Remotive + job-board links | current listings (Kenyan boards too, with Tavily) |
| `find_nearby_employers` | OpenStreetMap | closest real employers, nearest first |
| `web_search` | Tavily (optional) | verify pay, deadlines, news |

### Adding your own tool

1. Write the Python function in `tools.py`.
2. Add its description to `TOOL_DECLARATIONS`.
3. Add `"name": function` to `TOOL_FUNCTIONS`.

Nothing in `agent.py` needs to change. See `exercise_solutions.py` for examples.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'dotenv'`**: the packages are not installed in the Python you are running. Activate your virtual environment and run `python -m pip install -r requirements.txt`. In VS Code, pick the same environment with *Python: Select Interpreter*.
- **`KeyError: 'GEMINI_API_KEY'`**: `.env` is missing or empty. Copy `.env.example` to `.env` inside the `code` folder and add your key.
- **Rate limit / 429 errors**: you hit the free-tier limit. Wait a minute, or set a different `GEMINI_MODEL`.

## Honest limits

- Salary bands in `tools.py` are rough starter numbers, not official statistics. The agent is told to call them approximate. Replace them with data you trust.
- Platform links and job-board search URLs should be spot-checked before showing this to a class, because websites change.
- Nearby employers come from OpenStreetMap volunteers. They are places to approach, not confirmed vacancies.
- Remote jobs come from Remotive (please keep the link back to them).
- Live Kenyan job-board results need the free Tavily key. Without it the agent gives search links instead.

## License

Add a license of your choice (for example MIT) before making the repository public.
