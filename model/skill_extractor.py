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
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'experience\s*of\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?\s*of\s*experience',
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return 0


def extract_name(text: str) -> str:
    nlp = _get_nlp()
    doc = nlp(text[:500])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    lines = text.strip().split('\n')
    for line in lines[:5]:
        line = line.strip()
        if line and len(line.split()) <= 4 and line[0].isupper():
            return line
    return "Candidate"


def extract_email(text: str) -> str:
    match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = re.search(r'(\+?\d[\d\s\-().]{7,}\d)', text)
    return match.group(0).strip() if match else ""
