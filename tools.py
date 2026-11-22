"""
tools.py - the agent's "hands".

Each tool is just a normal Python function. The LLM never runs these itself.
It only ASKS us to run them, and our code (agent.py) does the actual calling.

  get_learning_platforms  built-in list   where to build skills for a course
  get_career_paths        built-in list   jobs + job destinations for a course
  get_salary_estimate     built-in list   APPROXIMATE monthly pay (Kenya, KES)
  find_jobs               Remotive + Tavily + job-board links (live listings)
  find_nearby_employers   OpenStreetMap   real organisations closest to the student
  web_search              Tavily          optional, needs TAVILY_API_KEY

IMPORTANT: the salary bands and platform lists below are starter data written
for this workshop. They are rough guides, not official statistics. The agent
is told to say "approximate" and to verify with web_search when it can.
"""

import math
import os
import re
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv

load_dotenv()
TIMEOUT = 20  # seconds - never let one slow API freeze the whole agent
HEADERS = {"User-Agent": "CareerCompassWorkshop/1.0 (student learning project)"}
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


# ---------------------------------------------------------------------------
# The knowledge base: one entry per career FIELD.
# Tools 1-3 all read from it, so adding a field here upgrades the whole agent.
# ---------------------------------------------------------------------------

def _p(name, good_for, cost, url=""):
    return {"name": name, "good_for": good_for, "cost": cost, "url": url}


FIELDS = {
    "software_it": {
        "keywords": ["computer", "software", "information technology", " it ",
                     "informatics", "programming", "web", "mobile app", "bsc cs"],
        "platforms": [
            _p("freeCodeCamp", "Web dev, Python, data - full free curriculum", "free", "https://www.freecodecamp.org"),
            _p("Microsoft Learn", "Azure, .NET, Power Platform, free certifications paths", "free", "https://learn.microsoft.com"),
            _p("Coursera / edX", "University-level courses, audit free", "free to audit", "https://www.coursera.org"),
            _p("GitHub", "Build a public portfolio of real projects", "free", "https://github.com"),
            _p("HackerRank / LeetCode", "Interview practice and coding challenges", "free", "https://www.hackerrank.com"),
            _p("ALX Africa", "Structured software engineering programme", "check site", "https://www.alxafrica.com"),
            _p("Moringa School", "Bootcamps (Nairobi)", "paid", "https://moringaschool.com"),
        ],
        "jobs": ["Software developer", "Web developer", "Mobile app developer",
                 "QA / test engineer", "IT support officer", "DevOps / cloud engineer",
                 "Systems administrator"],
        "destinations": {
            "local": ["Nairobi (biggest tech hub)", "Mombasa", "Kisumu", "Nakuru"],
            "sectors": ["Telecoms and mobile money", "Banks and fintech", "Software houses and startups",
                        "Government ICT (ICTA, county governments)", "NGOs and universities"],
            "remote_or_abroad": "Remote work for global companies is common for developers",
        },
        "employer_types": ["it_company", "bank"],
    },
    "data_ai": {
        "keywords": ["data", "statistics", "actuarial", "analytics", "machine learning",
                     "artificial intelligence", " ai ", "mathematics", "econometrics"],
        "platforms": [
            _p("Kaggle Learn", "Short free courses in Python, SQL, ML + datasets", "free", "https://www.kaggle.com/learn"),
            _p("IBM SkillsBuild", "Free data and AI learning paths with credentials", "free", "https://skillsbuild.org"),
            _p("Coursera / edX", "Data science specialisations", "free to audit", "https://www.coursera.org"),
            _p("Microsoft Learn", "Power BI, Azure data and AI paths", "free", "https://learn.microsoft.com"),
            _p("GitHub / Kaggle notebooks", "Publish analysis projects as your portfolio", "free", "https://github.com"),
        ],
        "jobs": ["Data analyst", "Business intelligence analyst", "Data scientist",
                 "Machine learning engineer", "Statistician", "Research analyst (M&E)"],
        "destinations": {
            "local": ["Nairobi", "Mombasa"],
            "sectors": ["Banks and insurance", "Telecoms", "Research institutes and NGOs (monitoring and evaluation)",
                        "Government statistics bodies", "Consulting firms"],
            "remote_or_abroad": "Remote analytics roles are available; strong SQL + Python helps most",
        },
        "employer_types": ["bank", "ngo", "it_company"],
    },
    "cybersecurity": {
        "keywords": ["cyber", "security", "network", "forensic", "telecommunication"],
        "platforms": [
            _p("TryHackMe", "Beginner-friendly hands-on security labs", "free tier", "https://tryhackme.com"),
            _p("Cisco Networking Academy", "Networking and security fundamentals", "free courses", "https://www.netacad.com"),
            _p("ISC2 / CompTIA", "Entry certifications (CC, Security+)", "check site", "https://www.isc2.org"),
            _p("Coursera / edX", "Security and risk courses", "free to audit", "https://www.coursera.org"),
        ],
        "jobs": ["Security analyst (SOC)", "Network administrator", "Penetration tester",
                 "IT auditor", "Digital forensics analyst"],
        "destinations": {
            "local": ["Nairobi", "Mombasa"],
            "sectors": ["Banks and mobile money", "Telecoms", "Government agencies", "Audit and consulting firms"],
            "remote_or_abroad": "Remote and bug-bounty work exist but need proven skills",
        },
        "employer_types": ["bank", "it_company", "government_office"],
    },
    "business_marketing": {
        "keywords": ["business", "commerce", "marketing", "management", "entrepreneur",
                     "human resource", "supply chain", "procurement", "sales", "bcom", "administration"],
        "platforms": [
            _p("HubSpot Academy", "Free marketing, sales and CRM certificates", "free", "https://academy.hubspot.com"),
            _p("Google Career Certificates", "Digital marketing, project management", "paid (financial aid)", "https://grow.google/certificates"),
            _p("Coursera / edX", "Management, strategy, operations", "free to audit", "https://www.coursera.org"),
            _p("LinkedIn Learning", "Short professional skills courses", "free trial", "https://www.linkedin.com/learning"),
            _p("Ajira Digital", "Kenyan programme for online work skills", "free", "https://ajiradigital.go.ke"),
        ],
        "jobs": ["Marketing officer", "Sales executive", "Business development officer",
                 "Human resource officer", "Procurement / supply chain officer",
                 "Project coordinator", "Customer success officer"],
        "destinations": {
            "local": ["Nairobi", "Mombasa", "Nakuru", "Kisumu", "Eldoret"],
            "sectors": ["FMCG and manufacturing", "Banks and insurance", "Telecoms",
                        "NGOs", "Logistics and ports", "Startups"],
            "remote_or_abroad": "Remote digital marketing and customer support roles are common",
        },
        "employer_types": ["bank", "ngo"],
    },
    "accounting_finance": {
        "keywords": ["account", "finance", "bank", "economics", "audit", "tax", "actuar", "cpa", "acca"],
        "platforms": [
            _p("KASNEB (CPA / CIFA)", "Kenya's professional accountancy qualifications", "paid", "https://www.kasneb.or.ke"),
            _p("ACCA", "Global accountancy qualification", "paid", "https://www.accaglobal.com"),
            _p("Corporate Finance Institute", "Financial modelling and valuation", "some free", "https://corporatefinanceinstitute.com"),
            _p("Coursera / edX", "Finance and accounting courses", "free to audit", "https://www.coursera.org"),
            _p("Microsoft Excel / Power BI (Microsoft Learn)", "The tools every finance job uses", "free", "https://learn.microsoft.com"),
        ],
        "jobs": ["Accountant", "Auditor", "Tax officer", "Financial analyst",
                 "Credit / loan officer", "Treasury officer", "Finance assistant"],
        "destinations": {
            "local": ["Nairobi", "Mombasa", "Nakuru", "Kisumu"],
            "sectors": ["Audit firms (Big 4 and mid-tier)", "Banks, SACCOs and microfinance",
                        "Insurance", "Government (KRA, treasury, counties)", "NGOs"],
            "remote_or_abroad": "Remote bookkeeping and finance support exists; ACCA travels well abroad",
        },
        "employer_types": ["accounting_firm", "bank"],
    },
    "engineering": {
        "keywords": ["engineer", "civil", "mechanical", "electrical", "electronic", "mechatronic",
                     "construction", "architecture", "surveying", "quantity", "petroleum", "chemical"],
        "platforms": [
            _p("Coursera / edX", "University engineering and CAD courses", "free to audit", "https://www.coursera.org"),
            _p("Autodesk learning (AutoCAD, Revit)", "Industry design software training", "free student licences", "https://www.autodesk.com/education"),
            _p("Khan Academy", "Maths and physics foundations", "free", "https://www.khanacademy.org"),
            _p("Engineers Board of Kenya", "Registration route for graduate engineers", "paid", ""),
            _p("Alison", "Short free certificate courses", "free", "https://alison.com"),
        ],
        "jobs": ["Graduate engineer", "Site engineer", "Maintenance engineer", "Design / CAD technician",
                 "Project engineer", "Quantity surveyor", "Electrical technician"],
        "destinations": {
            "local": ["Nairobi", "Mombasa", "Nakuru", "Kisumu", "Thika"],
            "sectors": ["Construction and infrastructure", "Energy (KenGen, KPLC, solar companies)",
                        "Manufacturing", "Oil, gas and mining", "Government roads and water agencies"],
            "remote_or_abroad": "Gulf states and the wider East Africa region recruit engineers",
        },
        "employer_types": ["engineering_firm", "government_office"],
    },
    "health": {
        "keywords": ["nurs", "medic", "clinical", "pharmac", "health", "dental", "laborator",
                     "public health", "nutrition", "physio", "mbchb", "biomedical"],
        "platforms": [
            _p("OpenWHO", "Free WHO courses on outbreaks, emergencies, clinical care", "free", "https://openwho.org"),
            _p("Coursera / edX", "Public health and clinical courses", "free to audit", "https://www.coursera.org"),
            _p("Khan Academy (health and medicine)", "Anatomy, physiology foundations", "free", "https://www.khanacademy.org"),
            _p("Professional council CPD portals", "Nursing Council / KMPDC / PPB continuing education", "varies", ""),
        ],
        "jobs": ["Nurse", "Clinical officer", "Medical laboratory technologist", "Pharmaceutical technologist",
                 "Community health officer", "Public health officer", "Nutritionist"],
        "destinations": {
            "local": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Counties across Kenya"],
            "sectors": ["County and national government hospitals", "Private and mission hospitals",
                        "NGOs and research institutes", "Pharmaceutical companies"],
            "remote_or_abroad": "Nurses and lab staff are recruited abroad (Gulf, UK, Canada) via licensed agencies",
        },
        "employer_types": ["hospital", "ngo"],
    },
    "education": {
        "keywords": ["education", "teach", "pedagog", "early childhood", "bed", "linguistic", "literature"],
        "platforms": [
            _p("Coursera / edX", "Teaching methods, ed-tech, curriculum design", "free to audit", "https://www.coursera.org"),
            _p("Khan Academy", "Subject content and teaching resources", "free", "https://www.khanacademy.org"),
            _p("Google for Education Training Center", "Digital teaching skills", "free", "https://skillshop.exceedlms.com"),
            _p("Alison", "Short certificate courses (TEFL, classroom management)", "free", "https://alison.com"),
        ],
        "jobs": ["Secondary / primary school teacher", "ECDE teacher", "Private tutor",
                 "Curriculum or ed-tech officer", "School administrator", "Teaching assistant"],
        "destinations": {
            "local": ["Every county (teachers are needed countrywide)", "Nairobi", "Nakuru", "Kisumu"],
            "sectors": ["Public schools (TSC employment)", "Private and international schools",
                        "Colleges and TVETs", "NGOs and ed-tech companies"],
            "remote_or_abroad": "Online tutoring and teaching abroad (Gulf, Rwanda, Uganda) are options",
        },
        "employer_types": ["school", "ngo"],
    },
    "agriculture": {
        "keywords": ["agri", "farm", "crop", "horticulture", "animal", "veterinar", "food science",
                     "agronomy", "forestry", "environment", "fisheries"],
        "platforms": [
            _p("FAO eLearning Academy", "Free courses on farming, food systems, climate", "free", "https://elearning.fao.org"),
            _p("Coursera / edX", "Sustainable agriculture and agribusiness", "free to audit", "https://www.coursera.org"),
            _p("Khan Academy", "Biology and chemistry foundations", "free", "https://www.khanacademy.org"),
            _p("Alison", "Short agribusiness certificates", "free", "https://alison.com"),
        ],
        "jobs": ["Agronomist / agricultural officer", "Agribusiness officer", "Farm manager",
                 "Veterinary officer", "Food quality officer", "Environmental officer", "Extension officer"],
        "destinations": {
            "local": ["Nakuru", "Eldoret", "Nyeri", "Kisumu", "Naivasha (flowers)", "Thika", "Rural counties"],
            "sectors": ["Export farms (tea, coffee, flowers, horticulture)", "Food processing",
                        "Research (KALRO and universities)", "NGOs and county governments"],
            "remote_or_abroad": "Agri-tech startups and international agriculture NGOs hire graduates",
        },
        "employer_types": ["farm_supply", "ngo", "government_office"],
    },
    "law": {
        "keywords": ["law", "llb", "legal", "criminology", "paralegal", "human rights", "international relations"],
        "platforms": [
            _p("Kenya School of Law", "Advocates Training Programme (needed to practise)", "paid", ""),
            _p("Coursera / edX", "Law, contracts, human rights courses", "free to audit", "https://www.coursera.org"),
            _p("Kenya Law (kenyalaw.org)", "Read real case law and legislation for free", "free", "https://kenyalaw.org"),
            _p("Alison", "Short law and compliance courses", "free", "https://alison.com"),
        ],
        "jobs": ["Pupil advocate / advocate", "Paralegal", "Legal officer / in-house counsel",
                 "Compliance officer", "Legal researcher", "Court clerk"],
        "destinations": {
            "local": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"],
            "sectors": ["Law firms", "Banks and corporates (compliance)", "Judiciary and government",
                        "NGOs (human rights)", "Regulators"],
            "remote_or_abroad": "Regional and international organisations hire lawyers; compliance work can be remote",
        },
        "employer_types": ["law_firm", "ngo", "government_office"],
    },
    "design_media": {
        "keywords": ["design", "media", "journal", "communication", "film", "graphic", "animation",
                     "public relations", "creative", "photography", "music", "fine art"],
        "platforms": [
            _p("Figma Learn", "UI/UX design basics, free tool", "free", "https://www.figma.com/resources/learn-design"),
            _p("Canva Design School", "Graphic design and social media content", "free", "https://www.canva.com/designschool"),
            _p("Google News Initiative Training Center", "Digital journalism skills", "free", "https://newsinitiative.withgoogle.com/training"),
            _p("Coursera / edX", "Design, media and communication courses", "free to audit", "https://www.coursera.org"),
            _p("Behance", "Publish a portfolio employers can browse", "free", "https://www.behance.net"),
        ],
        "jobs": ["Graphic designer", "UI/UX designer", "Content creator / social media manager",
                 "Journalist / reporter", "Video editor", "PR / communications officer"],
        "destinations": {
            "local": ["Nairobi (most agencies and media houses)", "Mombasa", "Kisumu"],
            "sectors": ["Media houses", "Advertising and PR agencies", "Tech companies (product design)",
                        "NGOs (communications)", "Freelance and agency work"],
            "remote_or_abroad": "Freelance design and editing for international clients is common",
        },
        "employer_types": ["media_house", "ngo"],
    },
    "general": {
        "keywords": [],
        "platforms": [
            _p("Coursera / edX", "Courses from universities in almost every subject", "free to audit", "https://www.coursera.org"),
            _p("LinkedIn Learning", "Professional and soft skills", "free trial", "https://www.linkedin.com/learning"),
            _p("Alison", "Free short certificate courses", "free", "https://alison.com"),
            _p("Ajira Digital", "Kenyan programme for online work skills", "free", "https://ajiradigital.go.ke"),
        ],
        "jobs": ["Graduate trainee", "Administrative officer", "Customer service officer",
                 "Research assistant", "Project assistant"],
        "destinations": {
            "local": ["Nairobi", "Mombasa", "Kisumu", "Nakuru"],
            "sectors": ["Banks", "NGOs", "Government", "Telecoms", "Startups"],
            "remote_or_abroad": "Remote support roles exist for most degrees",
        },
        "employer_types": ["ngo", "government_office"],
    },
}

# APPROXIMATE gross monthly pay in Kenya, in KES. Deliberately wide ranges.
# These are rough starter numbers for the prototype - NOT official statistics.
SALARY_KES = {
    "software_it":        {"entry": (50_000, 100_000), "mid": (120_000, 250_000), "senior": (300_000, 600_000)},
    "data_ai":            {"entry": (60_000, 110_000), "mid": (130_000, 280_000), "senior": (300_000, 550_000)},
    "cybersecurity":      {"entry": (70_000, 120_000), "mid": (150_000, 300_000), "senior": (350_000, 650_000)},
    "business_marketing": {"entry": (35_000, 70_000),  "mid": (80_000, 160_000),  "senior": (180_000, 400_000)},
    "accounting_finance": {"entry": (40_000, 80_000),  "mid": (90_000, 180_000),  "senior": (200_000, 450_000)},
    "engineering":        {"entry": (45_000, 90_000),  "mid": (100_000, 200_000), "senior": (220_000, 450_000)},
    "health":             {"entry": (45_000, 90_000),  "mid": (100_000, 200_000), "senior": (220_000, 500_000)},
    "education":          {"entry": (30_000, 55_000),  "mid": (55_000, 90_000),   "senior": (90_000, 150_000)},
    "agriculture":        {"entry": (30_000, 60_000),  "mid": (65_000, 120_000),  "senior": (130_000, 250_000)},
    "law":                {"entry": (50_000, 100_000), "mid": (120_000, 250_000), "senior": (280_000, 600_000)},
    "design_media":       {"entry": (30_000, 65_000),  "mid": (70_000, 140_000),  "senior": (150_000, 300_000)},
    "general":            {"entry": (30_000, 60_000),  "mid": (60_000, 120_000),  "senior": (120_000, 250_000)},
}


def _match_field(text: str) -> str:
    """Pick the best-matching career field for a course or job title.

    A keyword matches at the START of a word ("nurs" finds "nursing").
    A keyword with a trailing space (" it ", " ai ") must be a whole word.
    """
    text = text.lower()
    best, best_hits = "general", 0
    for name, info in FIELDS.items():
        hits = 0
        for kw in info["keywords"]:
            pattern = r"(?<![a-z])" + re.escape(kw.strip())
            if kw.endswith(" "):
                pattern += r"(?![a-z])"
            if re.search(pattern, text):
                hits += 1
        if hits > best_hits:
            best, best_hits = name, hits
    return best


# ---------------------------------------------------------------------------
# Tool 1: where to build skills
# ---------------------------------------------------------------------------

def get_learning_platforms(course: str) -> dict:
    """Learning platforms and programmes that suit a student's course."""
    field = _match_field(course)
    return {"course": course, "matched_field": field,
            "platforms": FIELDS[field]["platforms"],
            "tip": "Build 2-3 real projects or certificates; employers trust proof of skill."}


# ---------------------------------------------------------------------------
# Tool 2: jobs and job destinations
# ---------------------------------------------------------------------------

def get_career_paths(course: str) -> dict:
    """Possible jobs and job destinations (places, sectors, remote) for a course."""
    field = _match_field(course)
    info = FIELDS[field]
    return {"course": course, "matched_field": field,
            "possible_jobs": info["jobs"],
            "job_destinations": info["destinations"],
            "note": "Examples only. Check live listings for what is actually open."}


# ---------------------------------------------------------------------------
# Tool 3: approximate salary
# ---------------------------------------------------------------------------

def get_salary_estimate(course_or_job: str, level: str = "entry") -> dict:
    """Approximate monthly pay in Kenya (KES) for a course/job at a career level."""
    level = level.lower() if level.lower() in ("entry", "mid", "senior") else "entry"
    field = _match_field(course_or_job)
    low, high = SALARY_KES[field][level]
    return {"for": course_or_job, "matched_field": field, "level": level,
            "currency": "KES per month (gross, before tax)",
            "approx_range": f"{low:,} - {high:,}",
            "all_levels": {lv: f"{a:,} - {b:,}" for lv, (a, b) in SALARY_KES[field].items()},
            "warning": "Rough starter estimates for Kenya, not official statistics. "
                       "Pay varies by employer, county and experience. Verify before relying on it."}


# ---------------------------------------------------------------------------
# Shared helper: turn a place name into coordinates (Open-Meteo geocoding, free)
# ---------------------------------------------------------------------------

def _geocode(place: str):
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": place, "count": 1},
        headers=HEADERS, timeout=TIMEOUT,
    ).json()
    if not geo.get("results"):
        return None
    r = geo["results"][0]
    return {"name": r["name"], "country": r.get("country"),
            "country_code": r.get("country_code"),
            "lat": r["latitude"], "lon": r["longitude"]}


def _distance_km(lat1, lon1, lat2, lon2) -> float:
    """Straight-line distance between two points (haversine formula)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Tool 4: live job listings
#   - Remotive (remote jobs, free, no key). Please link back to Remotive.
#   - Tavily limited to Kenyan job boards (only if TAVILY_API_KEY is set)
#   - Ready-made search links, so the student always has somewhere to click
# ---------------------------------------------------------------------------

KENYAN_JOB_SITES = ["brightermonday.co.ke", "myjobmag.co.ke", "fuzu.com",
                    "careerpointkenya.co.ke"]


def find_jobs(job_title: str, location: str = "Nairobi", include_remote: bool = True) -> dict:
    """Find current job listings for a job title near a location."""
    try:
        place = _geocode(location)
    except Exception:  # geocoder down: carry on with the name the student typed
        place = None
    place_name = place["name"] if place else location
    out = {"searched_for": job_title,
           "location": place_name + (f", {place['country']}" if place and place.get("country") else "")}

    # 1) Remote jobs (work from anywhere)
    if include_remote:
        try:
            data = requests.get("https://remotive.com/api/remote-jobs",
                                params={"search": job_title, "limit": 5},
                                headers=HEADERS, timeout=TIMEOUT).json()
            out["remote_jobs"] = [
                {"title": j["title"], "company": j["company_name"],
                 "open_to": j.get("candidate_required_location", ""),
                 "posted": j.get("publication_date", "")[:10],
                 "link": j["url"]}
                for j in data.get("jobs", [])[:5]
            ]
        except Exception as e:
            out["remote_jobs_error"] = str(e)

    # 2) Local listings from Kenyan job boards (needs the optional Tavily key)
    if TAVILY_API_KEY:
        try:
            data = requests.post(
                "https://api.tavily.com/search",
                json={"query": f"{job_title} job vacancy {place_name}",
                      "max_results": 5, "include_domains": KENYAN_JOB_SITES},
                headers={**HEADERS, "Authorization": f"Bearer {TAVILY_API_KEY}"},
                timeout=TIMEOUT,
            ).json()
            out["local_listings"] = [
                {"title": r["title"], "link": r["url"], "snippet": r["content"][:250]}
                for r in data.get("results", [])
            ]
        except Exception as e:
            out["local_listings_error"] = str(e)
    else:
        out["local_listings_note"] = ("Live local-board search is off (no TAVILY_API_KEY). "
                                      "Use the search_links below instead.")

    # 3) Always give clickable searches on the big boards
    q, loc = quote_plus(job_title), quote_plus(place_name)
    out["search_links"] = {
        "LinkedIn": f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}",
        "Indeed Kenya": f"https://ke.indeed.com/jobs?q={q}&l={loc}",
        "BrighterMonday": f"https://www.brightermonday.co.ke/jobs?q={q}",
    }
    return out


# ---------------------------------------------------------------------------
# Tool 5: the nearest real employers (OpenStreetMap / Overpass, free, no key)
# Great for walk-in applications, attachments and internships.
# ---------------------------------------------------------------------------

# employer type  ->  OpenStreetMap tags that mean "this kind of place"
EMPLOYER_TAGS = {
    "hospital":          [("amenity", "hospital"), ("amenity", "clinic")],
    "school":            [("amenity", "school"), ("amenity", "college"), ("amenity", "university")],
    "bank":              [("amenity", "bank")],
    "it_company":        [("office", "it"), ("office", "company"), ("office", "telecommunication")],
    "accounting_firm":   [("office", "accountant"), ("office", "financial")],
    "law_firm":          [("office", "lawyer"), ("office", "notary")],
    "engineering_firm":  [("office", "engineer"), ("office", "construction_company"), ("craft", "electrician")],
    "media_house":       [("office", "newspaper"), ("office", "advertising_agency"), ("office", "association")],
    "ngo":               [("office", "ngo"), ("office", "foundation")],
    "government_office": [("office", "government")],
    "hotel":             [("tourism", "hotel")],
    "farm_supply":       [("shop", "agrarian"), ("landuse", "farmyard")],
}


def find_nearby_employers(location: str, employer_type: str, radius_km: int = 15) -> dict:
    """Closest organisations of a given type to a place, nearest first."""
    if employer_type not in EMPLOYER_TAGS:
        return {"error": f"Unknown employer_type '{employer_type}'. "
                         f"Choose one of: {', '.join(EMPLOYER_TAGS)}"}
    place = _geocode(location)
    if not place:
        return {"error": f"Could not find a place called '{location}'."}

    radius_m = max(1, min(int(radius_km), 50)) * 1000
    parts = []
    for key, value in EMPLOYER_TAGS[employer_type]:
        for kind in ("node", "way"):
            parts.append(f'{kind}["{key}"="{value}"]["name"](around:{radius_m},{place["lat"]},{place["lon"]});')
    query = f'[out:json][timeout:25];({"".join(parts)});out center 60;'

    data = requests.post("https://overpass-api.de/api/interpreter",
                         data={"data": query}, headers=HEADERS, timeout=40).json()

    found = {}
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        name = tags.get("name")
        if not (name and lat and lon):
            continue
        found[name] = {
            "name": name,
            "distance_km": round(_distance_km(place["lat"], place["lon"], lat, lon), 1),
            "website": tags.get("website") or tags.get("contact:website") or "",
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "street": tags.get("addr:street", ""),
        }
    nearest = sorted(found.values(), key=lambda x: x["distance_km"])[:8]
    if not nearest:
        return {"location": place["name"], "employer_type": employer_type, "employers": [],
                "note": f"Nothing mapped within {radius_km} km. Try a larger radius or a nearby town."}
    return {"location": place["name"], "employer_type": employer_type,
            "employers": nearest,
            "note": "From OpenStreetMap volunteers, so the list may be incomplete. "
                    "These are places to approach, not confirmed vacancies."}


# ---------------------------------------------------------------------------
# Tool 6 (optional): web search  (Tavily - https://tavily.com)
# Only offered to the LLM if TAVILY_API_KEY is in your .env file.
# ---------------------------------------------------------------------------

def web_search(query: str) -> dict:
    """Search the live web. Good for checking salaries, deadlines and news."""
    data = requests.post(
        "https://api.tavily.com/search",
        json={"query": query, "max_results": 3},
        headers={**HEADERS, "Authorization": f"Bearer {TAVILY_API_KEY}"},
        timeout=TIMEOUT,
    ).json()
    if "results" not in data:
        detail = data.get("detail", data)
        if isinstance(detail, dict):
            detail = detail.get("error", detail)
        return {"error": f"Web search problem: {detail}"}
    return {"results": [
        {"title": r["title"], "url": r["url"], "snippet": r["content"][:400]}
        for r in data["results"]
    ]}


WEB_SEARCH_DECLARATION = {
    "name": "web_search",
    "description": "Search the live web to verify salaries, application deadlines, "
                   "scholarships or recent hiring news.",
    "parameters_json_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}


# ---------------------------------------------------------------------------
# Tool "menu": what we show the LLM.  name + description + parameters
# The LLM reads ONLY this - it never sees the Python code above.
# ---------------------------------------------------------------------------

TOOL_DECLARATIONS = [
    {
        "name": "get_learning_platforms",
        "description": "Learning platforms, courses and programmes where a student "
                       "can build skills for their course.",
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "course": {"type": "string", "description": "e.g. 'Nursing' or 'BSc Computer Science'"},
            },
            "required": ["course"],
        },
    },
    {
        "name": "get_career_paths",
        "description": "Possible jobs and job destinations (cities, sectors, remote "
                       "or abroad) for a student's course.",
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "course": {"type": "string", "description": "e.g. 'Accounting'"},
            },
            "required": ["course"],
        },
    },
    {
        "name": "get_salary_estimate",
        "description": "APPROXIMATE monthly salary range in Kenya (KES) for a course "
                       "or job at entry, mid or senior level.",
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "course_or_job": {"type": "string", "description": "e.g. 'Data analyst'"},
                "level": {"type": "string", "description": "entry, mid or senior (default entry)"},
            },
            "required": ["course_or_job"],
        },
    },
    {
        "name": "find_jobs",
        "description": "Find CURRENT job listings (remote jobs, Kenyan job boards, "
                       "search links) for a job title near a place.",
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "e.g. 'Clinical officer'"},
                "location": {"type": "string", "description": "The student's town, e.g. 'Nakuru'"},
                "include_remote": {"type": "boolean", "description": "Also search remote jobs (default true)"},
            },
            "required": ["job_title", "location"],
        },
    },
    {
        "name": "find_nearby_employers",
        "description": "Find the real organisations of one type closest to the "
                       "student's town (for walk-in applications, attachments, internships).",
        "parameters_json_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The student's town, e.g. 'Kisumu'"},
                "employer_type": {"type": "string", "enum": list(EMPLOYER_TAGS)},
                "radius_km": {"type": "integer", "description": "Search radius, 1 to 50 (default 15)"},
            },
            "required": ["location", "employer_type"],
        },
    },
]

# Lookup table: tool name (text from the LLM) -> real Python function
TOOL_FUNCTIONS = {
    "get_learning_platforms": get_learning_platforms,
    "get_career_paths": get_career_paths,
    "get_salary_estimate": get_salary_estimate,
    "find_jobs": find_jobs,
    "find_nearby_employers": find_nearby_employers,
}

# The optional sixth tool: only switched on when there's a key.
if TAVILY_API_KEY:
    TOOL_DECLARATIONS.append(WEB_SEARCH_DECLARATION)
    TOOL_FUNCTIONS["web_search"] = web_search


if __name__ == "__main__":
    # Run `python tools.py` to test the tools WITHOUT any LLM.
    print(get_learning_platforms("Nursing")["matched_field"])
    print(get_career_paths("BSc Computer Science")["possible_jobs"])
    print(get_salary_estimate("Accounting", "entry")["approx_range"])
    print(find_jobs("nurse", "Nakuru"))
    print(find_nearby_employers("Nakuru", "hospital"))
    if TAVILY_API_KEY:
        print(web_search("nurse salary Kenya"))
    else:
        print("web_search skipped: no TAVILY_API_KEY in .env")
