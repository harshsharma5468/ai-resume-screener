import re
import spacy
from typing import List

SKILLS_DB = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "scala", "kotlin",
    "swift", "go", "rust", "ruby", "php", "bash", "r", "matlab", "solidity",
    # ML / AI
    "machine learning", "deep learning", "reinforcement learning", "nlp",
    "computer vision", "neural networks", "transfer learning", "mlops",
    # Frameworks & Libraries
    "tensorflow", "pytorch", "keras", "scikit-learn", "huggingface", "spacy",
    "opencv", "xgboost", "lightgbm", "pandas", "numpy", "scipy",
    # NLP specific
    "bert", "gpt", "transformers", "word2vec", "fasttext", "nltk",
    # Web
    "react", "nodejs", "html", "css", "redux", "graphql", "django", "flask",
    "fastapi", "rest api", "microservices", "web3",
    # Databases
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
    "ci/cd", "linux", "airflow", "kafka", "spark", "hadoop",
    # Data & BI
    "tableau", "power bi", "excel", "data visualization", "etl", "data modeling",
    "statistics", "data analysis", "data engineering",
    # Other
    "blockchain", "smart contracts", "ethereum", "firebase", "ros", "ios",
    "android", "react native", "prometheus", "grafana", "siem", "agile",
    "product management", "user research", "system design", "algorithms",
    "data structures", "penetration testing", "cybersecurity", "network security",
    "cloud architecture", "sensor fusion", "control systems", "research",
    "communication", "roadmapping", "scala", "c++",
]

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.lang.en import English
            _nlp = English()
    return _nlp


def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    found = set()
    for skill in SKILLS_DB:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill)
    return sorted(found)


def extract_experience_years(text: str) -> int:
    patterns = [
        r'(\d+)\+?\s*years?\s*of\s*(?:work\s*)?experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'experience\s*of\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience',
        r'(\d+)\+?\s*years?\s*(?:in|working)',
        # date range: e.g. "2022 - 2024" or "Jan 2022 – Present"
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    # count year ranges like "2021 - 2023", "2020 – Present"
    ranges = re.findall(r'(20\d{2})\s*[-–]\s*(20\d{2}|present)', text.lower())
    if ranges:
        total = 0
        import datetime
        current_year = datetime.datetime.now().year
        for start, end in ranges:
            end_year = current_year if end == "present" else int(end)
            total += end_year - int(start)
        return total
    return 0


def extract_name(text: str) -> str:
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    # First non-empty line that looks like a name (2-4 words, all title-case, no digits)
    for line in lines[:6]:
        words = line.split()
        if (2 <= len(words) <= 4
                and all(w[0].isupper() for w in words if w)
                and not any(char.isdigit() for char in line)
                and '|' not in line and '@' not in line and '/' not in line):
            return line
    # Fallback: spaCy PERSON entity
    nlp = _get_nlp()
    doc = nlp(text[:500])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return "Candidate"


def extract_email(text: str) -> str:
    match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = re.search(r'(\+?\d[\d\s\-().]{7,}\d)', text)
    return match.group(0).strip() if match else ""
