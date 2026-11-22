"""
exercise_solutions.py - answers for the "Your turn" exercises.
Try them yourself first!

How to plug a new tool into the agent (same 3 moves every time):
  1. Write the Python function           (in tools.py)
  2. Add its description to TOOL_DECLARATIONS
  3. Add  "name": function  to TOOL_FUNCTIONS
Nothing in agent.py needs to change. The loop already handles any tool.
"""

import json
from datetime import datetime

import requests

HEADERS = {"User-Agent": "CareerCompassWorkshop/1.0 (student learning project)"}


# ---------------------------------------------------------------------------
# Exercise 1: add another country's salaries
# Idea: SALARY_KES in tools.py is just a dictionary. Copy it, change the
# numbers for Uganda (UGX) or Tanzania (TZS), and give get_salary_estimate a
# `country` parameter that picks the right table. The agent adapts by itself.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Exercise 2: country facts  (REST Countries - free, no key)
# Useful when a student asks about working abroad.
# ---------------------------------------------------------------------------

def get_country_info(country: str) -> dict:
    """Capital, population, currencies, languages and time zones of a country."""
    data = requests.get(
        f"https://restcountries.com/v3.1/name/{country}",
        params={"fields": "name,capital,population,currencies,languages,timezones"},
        headers=HEADERS, timeout=10,
    ).json()
    if not isinstance(data, list) or not data:
        return {"error": f"No country found called '{country}'."}
    c = data[0]
    return {
        "name": c["name"]["common"],
        "capital": c.get("capital", []),
        "population": c.get("population"),
        "currencies": list(c.get("currencies", {}).keys()),
        "languages": list(c.get("languages", {}).values()),
        "timezones": c.get("timezones", []),
    }


COUNTRY_DECLARATION = {
    "name": "get_country_info",
    "description": "Get basic facts about a country: capital, population, currencies, languages, time zones.",
    "parameters_json_schema": {
        "type": "object",
        "properties": {"country": {"type": "string", "description": "e.g. 'Rwanda'"}},
        "required": ["country"],
    },
}


# ---------------------------------------------------------------------------
# Exercise 3: a tool that DOES something - save the career plan to a file
# A human approves first ("human in the loop"), because this tool changes things.
# ---------------------------------------------------------------------------

def save_career_plan(title: str, plan: str) -> dict:
    """Save a career plan to a text file, after the student says yes."""
    answer = input(f"\n  Agent wants to save '{title}' to a file. Allow? (y/n) ").strip().lower()
    if answer != "y":
        return {"saved": False, "reason": "The user said no."}
    filename = f"career_plan_{datetime.now():%Y%m%d_%H%M%S}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{title}\n{'=' * len(title)}\n\n{plan}\n")
    return {"saved": True, "file": filename}


SAVE_DECLARATION = {
    "name": "save_career_plan",
    "description": "Save the final career plan to a text file. Only use when the student asks to save.",
    "parameters_json_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "plan": {"type": "string", "description": "The full plan text"},
        },
        "required": ["title", "plan"],
    },
}


# ---------------------------------------------------------------------------
# Exercise 4: a skills-gap checker (no internet, pure Python)
# The student lists skills they already have; the tool compares them with a
# short "must have" list for the field and returns what is still missing.
# ---------------------------------------------------------------------------

CORE_SKILLS = {
    "software_it": ["Python or JavaScript", "Git and GitHub", "SQL", "A deployed portfolio project"],
    "data_ai": ["SQL", "Python (pandas)", "Excel or Power BI", "A published analysis project"],
    "accounting_finance": ["Excel", "A bookkeeping package", "Financial statements", "CPA or ACCA progress"],
    "health": ["Clinical placement hours", "Professional council registration", "Basic life support", "Communication"],
    "business_marketing": ["Digital marketing basics", "Excel", "Presentation skills", "A real campaign or project"],
}


def check_skills_gap(field: str, skills_i_have: str) -> dict:
    """Compare the student's skills with the core skills for a field."""
    from tools import _match_field
    matched = _match_field(field)
    wanted = CORE_SKILLS.get(matched)
    if not wanted:
        return {"error": f"No skills list for '{matched}' yet. Add one to CORE_SKILLS."}
    have = skills_i_have.lower()
    missing = [s for s in wanted if not any(word in have for word in s.lower().split()[:1])]
    return {"field": matched, "core_skills": wanted, "probably_missing": missing}


GAP_DECLARATION = {
    "name": "check_skills_gap",
    "description": "Compare the skills a student already has with the core skills for their field.",
    "parameters_json_schema": {
        "type": "object",
        "properties": {
            "field": {"type": "string", "description": "The student's course, e.g. 'Computer Science'"},
            "skills_i_have": {"type": "string", "description": "Skills the student listed, comma separated"},
        },
        "required": ["field", "skills_i_have"],
    },
}


# To use them, add these lines at the bottom of tools.py:
#
#   from exercise_solutions import (get_country_info, COUNTRY_DECLARATION,
#                                   save_career_plan, SAVE_DECLARATION,
#                                   check_skills_gap, GAP_DECLARATION)
#   TOOL_DECLARATIONS += [COUNTRY_DECLARATION, SAVE_DECLARATION, GAP_DECLARATION]
#   TOOL_FUNCTIONS["get_country_info"] = get_country_info
#   TOOL_FUNCTIONS["save_career_plan"] = save_career_plan
#   TOOL_FUNCTIONS["check_skills_gap"] = check_skills_gap

if __name__ == "__main__":
    print(json.dumps(get_country_info("Kenya"), indent=2))
    print(json.dumps(check_skills_gap("Computer Science", "Python, SQL"), indent=2))
