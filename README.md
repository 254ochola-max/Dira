# Dira: Career Compass Agent

Dira is an AI-powered career guide for students and recent graduates in Kenya. A student says **what course they are doing** and **which town they live in**, and Dira replies with a practical plan:

- Platforms to build relevant skills
- Jobs they can aim for, and where those jobs are
- Approximate salaries (KES per month)
- Live job listings and the nearest real employers to approach for internships or attachments

Dira is a tool-using agent. The LLM never makes up jobs or pay on its own. It asks our Python code to call tools, reads the results, and then writes the final plan.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| LLM | Google Gemini (default `gemini-3.5-flash`, configurable) |
| LLM SDK | `google-genai` (function calling / tool use) |
| HTTP | `requests` |
| Config | `python-dotenv` (`.env` file) |
| Remote jobs | [Remotive API](https://remotive.com/api/remote-jobs) |
| Kenyan job boards and web verification (optional) | [Tavily Search API](https://tavily.com) |
| Nearby employers | [OpenStreetMap](https://www.openstreetmap.org) via the Overpass API |
| Geocoding | Open-Meteo Geocoding API |
| Extra exercise tool | REST Countries API |

### Agent architecture

Dira uses the classic **think → act → observe** loop:

1. The student asks a question.
2. Gemini decides which tool(s) to call.
3. Our code runs the matching Python function and returns the result.
4. Gemini reads the results and either calls more tools or writes the final answer.
5. A safety limit (`MAX_STEPS = 8`) stops runaway loops.

---

## Features and Tools

| Tool | Data source | Purpose |
|---|---|---|
| `get_learning_platforms` | Built-in knowledge base | Where to build skills for a course |
| `get_career_paths` | Built-in knowledge base | Jobs and job destinations |
| `get_salary_estimate` | Built-in knowledge base | Approximate monthly pay (Kenya, KES) |
| `find_jobs` | Remotive + job-board links (+ Tavily for Kenyan boards) | Current job listings |
| `find_nearby_employers` | OpenStreetMap (Overpass) | Closest real employers, nearest first |
| `web_search` | Tavily (optional) | Verify pay, deadlines and news |

The built-in knowledge base covers career fields such as software/IT, data and AI, cybersecurity, business and marketing, accounting and finance, and engineering. Courses are matched to a field by keyword.

---

## Project Structure

```
.
├── agent.py               # Full agent loop (think -> act -> observe)
├── agent_sdk.py           # Same agent, with the loop handled by the Gemini SDK
├── tools.py               # The tools, knowledge base and tool declarations
├── step1_ask_llm.py       # Demo: a plain LLM guessing about jobs and pay
├── step2_one_tool.py      # Demo: one tool, one round trip done by hand
├── exercise_solutions.py  # Extra tools: country facts, save plan, skills gap
├── check_setup.py         # Verifies your environment and API keys
├── requirements.txt       # Python dependencies
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python 3.10 or newer
- A free [Gemini API key](https://aistudio.google.com/apikey)
- *(Optional)* A free [Tavily API key](https://app.tavily.com) for `web_search` and live Kenyan job-board results

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/254ochola-max/Dira.git
cd Dira

# 2. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a file named `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_key_here

# Optional: enables web_search and live Kenyan job-board results
TAVILY_API_KEY=

# Optional: switch model if you hit free-tier daily limits
GEMINI_MODEL=gemini-3.5-flash
```

> **Never commit your `.env` file.** It is already listed in `.gitignore`.

### Verify your setup

```bash
python check_setup.py
```

### Run the agent

```bash
python agent.py
```

Or run the version where the Gemini SDK manages the tool loop:

```bash
python agent_sdk.py
```

### Example prompt

```
I'm studying nursing in Nakuru. Where can I build my skills, what jobs can I get,
what do they pay, and what is open near me?
```

Dira answers with these sections: **Skills to build, Jobs you can aim for, Where the jobs are, Approximate pay, Open now and nearby, Your next 3 steps.**

---

## Learning Path

The repo doubles as a small tutorial on building agents:

1. `step1_ask_llm.py`: see how a plain LLM guesses about live jobs and pay.
2. `step2_one_tool.py`: give the LLM one tool and run one round trip by hand.
3. `agent.py`: the complete multi-tool agent loop.
4. `agent_sdk.py`: the same agent using the SDK's built-in loop.
5. `exercise_solutions.py`: extra tools to extend the agent.

---

## Limitations

- **Salary bands are rough starter numbers**, not official statistics. Replace them with data you trust.
- **Platform links and job-board URLs can change.** Spot-check them before sharing.
- **Nearby employers come from OpenStreetMap volunteers.** They are places to approach, not confirmed vacancies.
- **Remote jobs come from Remotive**; please keep the link back to them.
- **Live Kenyan job-board results need a Tavily key.** Without it, the agent gives search links instead.

---

## Contributing

Contributions are welcome. A great place to start is adding a new career field to the `FIELDS` knowledge base in `tools.py`, which upgrades the whole agent at once.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/new-field`)
3. Commit your changes
4. Open a pull request

---

## Acknowledgements

- [Google Gemini](https://ai.google.dev) for the LLM
- [Remotive](https://remotive.com) for remote job listings
- [OpenStreetMap](https://www.openstreetmap.org) contributors for employer data
- [Tavily](https://tavily.com) for web search
- [Open-Meteo](https://open-meteo.com) for geocoding
