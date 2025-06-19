# backend/app/utils/nlp.py

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import logging
import nltk
import os
import dateparser # For parsing various date string formats
from datetime import datetime # For handling "Present" dates and duration calculation

# Attempt to import sentence-transformers related libraries
try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logging.error("CRITICAL: sentence-transformers library or its dependencies (like torch) not found. "
                  "Semantic similarity WILL NOT WORK. Install with: pip install sentence-transformers torch", exc_info=False)
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None # Define for graceful failure if calculate_semantic_similarity is called
    util = None
    torch = None

# --- DEFINE LOGGER ---
logger = logging.getLogger(__name__)

# --- NLTK Resource Checks ---
def ensure_nltk_resource(resource_id_path, resource_name_for_log): # resource_id_path e.g. 'tokenizers/punkt'
    try:
        nltk.data.find(resource_id_path)
        logger.debug(f"NLTK resource '{resource_name_for_log}' found.")
    except LookupError:
        logger.info(f"NLTK resource '{resource_name_for_log}' not found. Downloading '{resource_id_path.split('/')[-1]}'...")
        try:
            nltk.download(resource_id_path.split('/')[-1]) # e.g., download 'punkt' or 'stopwords'
            logger.info(f"NLTK resource '{resource_name_for_log}' downloaded successfully.")
        except Exception as e:
            logger.error(f"Failed to download NLTK resource '{resource_name_for_log}': {e}", exc_info=True)
    except Exception as e:
         logger.error(f"Error checking NLTK resource '{resource_name_for_log}': {e}", exc_info=True)

ensure_nltk_resource('tokenizers/punkt', 'punkt tokenizer data')
ensure_nltk_resource('corpora/stopwords', 'stopwords corpus')

# --- Globals / Setup ---
NLP_MODEL_NAME = "en_core_web_lg" # Using large model as per your last successful load
SENTENCE_MODEL_NAME = 'all-MiniLM-L6-v2'
W_SEMANTIC = 0.35; W_SKILL = 0.45; W_EXPERIENCE = 0.20

# --- Helper Function Definitions ---
def load_spacy_model(model_name):
    try:
        nlp = spacy.load(model_name)
        logger.info(f"spaCy model '{model_name}' loaded successfully.")
        return nlp
    except OSError:
        logger.warning(f"spaCy model '{model_name}' not found. Attempting download...")
        try:
            spacy.cli.download(model_name)
            nlp = spacy.load(model_name)
            logger.info(f"spaCy model '{model_name}' downloaded and loaded successfully.")
            return nlp
        except SystemExit as e:
             logger.error(f"spaCy download command failed for model '{model_name}'. Error: {e}", exc_info=True); return None
        except Exception as e:
            logger.error(f"Failed to download/load spaCy model '{model_name}': {e}", exc_info=True); return None
    except Exception as e:
        logger.error(f"Unexpected error loading spaCy model '{model_name}': {e}", exc_info=True); return None

# --- Load Resources ---
nlp_model = load_spacy_model(NLP_MODEL_NAME)
sentence_model = None
if SENTENCE_TRANSFORMERS_AVAILABLE:
   try:
       logger.info(f"Attempting to load SentenceTransformer model: {SENTENCE_MODEL_NAME}...")
       sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME)
       logger.info(f"SentenceTransformer model '{SENTENCE_MODEL_NAME}' loaded successfully.")
   except Exception as e:
       logger.error(f"Failed to load SentenceTransformer model '{SENTENCE_MODEL_NAME}': {e}", exc_info=True)
       SENTENCE_TRANSFORMERS_AVAILABLE = False # Set flag if model loading fails
       sentence_model = None # Ensure it's None
else: logger.warning("SentenceTransformer library was not imported; semantic features will be disabled.")

stop_words = set()
try:
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
    logger.debug("NLTK English stopwords loaded.")
except Exception as e: logger.error(f"Could not load NLTK stopwords: {e}")


# --- Skill Keywords ---
# CRITICAL: MANUALLY CURATE THIS LIST BASED ON YOUR TARGET ROLES!
SKILL_KEYWORDS = {
    # --- Core Programming & Scripting ---
    "python", "java", "javascript", "js", "ecmascript", "typescript", "ts",
    "c++", "cpp", "c#", "csharp", "c lang", "c",
    "html", "html5", "css", "css3", "scss", "sass",
    "php", "ruby", "go", "golang", "swift", "kotlin", "scala", "perl",
    "bash", "shell", "shell scripting", "ksh", "powershell",
    "sql", "pl/sql", "tsql", "sql server", "mssql", # Grouped SQL variants
    "r",

    # --- Web Development - Backend Frameworks/Libraries ---
    "node.js", "nodejs", "express", "express.js",
    "flask", "django", "fastapi",
    "ruby on rails", "ror",
    "laravel", "symfony",
    "spring", "spring boot", "java ee", "jakarta ee", "j2ee",
    ".net", ".net core", ".net framework", "asp.net", "asp.net core", "entity framework",

    # --- Web Development - Frontend Frameworks/Libraries ---
    "react", "react.js", "reactjs",
    "angular", "angular.js", "angularjs", # Consider version specifics if needed e.g. "angular 2+"
    "vue", "vue.js", "vuejs",
    "next.js", "nextjs", "gatsby", "svelte", "sveltekit",
    "jquery", "bootstrap", "tailwind css", "material ui", "mui", "chakra ui", "ant design",
    "redux", "mobx", "zustand", "rxjs", "ngrx", "vuex", "pinia",
    "webpack", "vite", "parcel", "babel", "eslint", "prettier", "webassembly", "wasm",

    # --- Databases & Data Storage ---
    "mysql", "postgresql", "postgres", "mariadb", "sqlite", "microsoft sql server",
    "oracle", "oracle database", # "oracle 10g", "oracle 11g", "oracle 12c" - maybe too specific for general
    "nosql", "mongodb", "couchbase", "cassandra", "dynamodb", "firebase", "firestore",
    "redis", "memcached", "elasticsearch", "solr", "opensearch",
    "database design", "database modeling", "data modeling", "database administration", "dba",
    "data warehousing", "etl", "sqlalchemy", "hibernate", "jpa", "jdbc", "odbc",

    # --- APIs & Protocols ---
    "rest", "restful", "rest apis", "graphql", "grpc", "soap", "openapi", "swagger",
    "json", "xml", "protobuf", "http", "https_","tcp/ip", "udp", "websockets", "oauth", "jwt", "saml",

    # --- Cloud Platforms & Services ---
    "aws", "amazon web services", "azure", "microsoft azure", "gcp", "google cloud platform",
    "heroku", "digitalocean", "netlify", "vercel", "firebase hosting",
    "ec2", "s3", "rds", "lambda", "ebs", "elastic ip", "vpc", "route 53", "cloudfront", "iam", "cognito", # Common AWS
    "azure vm", "azure blob storage", "azure functions", "azure sql database", "azure ad", # Common Azure
    "gce", "google compute engine", "google cloud storage", "google cloud functions", "bigquery", # Common GCP
    "serverless", "faas",
    "eks", "ecs", "gke", "aks", # Kubernetes services

    # --- DevOps & Infrastructure ---
    "docker", "kubernetes", "k8s", "containerization", "containers",
    "ci/cd", "continuous integration", "continuous deployment", "continuous delivery",
    "jenkins", "gitlab ci", "github actions", "travis ci", "circleci", "argocd", "spinnaker", "azure devops",
    "terraform", "ansible", "puppet", "chef", "cloudformation", "pulumi", "infrastructure as code", "iac",
    "monitoring", "logging", "observability", "prometheus", "grafana", "datadog", "new relic", "splunk", "elk stack", "opentelemetry",
    "nginx", "apache", "haproxy", "envoy", "istio", "service mesh",
    "system administration", "sysadmin", "site reliability engineering", "sre",

    # --- OS & Systems ---
    "linux", "unix", "ubuntu", "debian", "centos", "rhel", "fedora", "windows server", "macos", "mac os x",

    # --- ML/AI/Data Science ---
    "machine learning", "ml",
    "deep learning", "dl", "neural networks",
    "nlp", "natural language processing", "text mining", "sentiment analysis",
    "computer vision", "cv", "image processing", "object detection",
    "data analysis", "data analytics", "data visualization", "business intelligence", "bi",
    "data science", "data scientist",
    "statistics", "statistical modeling", "hypothesis testing", "a/b testing",
    "pandas", "numpy", "scipy", "scikit-learn", "sklearn", "statsmodels",
    "tensorflow", "tf", "keras",
    "pytorch", "torch",
    "jupyter", "jupyter notebook", "jupyterlab",
    "matplotlib", "seaborn", "plotly", "bokeh", "d3.js", "tableau", "power bi", "qlik",
    "big data", "spark", "pyspark", "hadoop", "mapreduce", "hive", "presto", "kafka", "flink",
    "data mining", "feature engineering", "model evaluation", "model deployment", "mlops",
    "recommender systems", "time series analysis", "forecasting", "optimization", "operations research",

    # --- Version Control ---
    "git", "github", "gitlab", "bitbucket", "svn", "version control", "gitflow",

    # --- Testing Frameworks/Tools ---
    "testing", "test automation", "unit testing", "integration testing", "system testing", "acceptance testing", "e2e testing",
    "qa", "quality assurance", "manual testing",
    "selenium", "webdriver", "cypress", "playwright", "puppeteer", "appium",
    "jest", "mocha", "chai", "enzyme", "react testing library", "rtl", "vue test utils",
    "junit", "testng", "nunit", "xunit",
    "pytest", "unittest", "tox", "nose", "robot framework",
    "postman", "insomnia", "api testing", "load testing", "performance testing", "jmeter", "locust", "k6",

    # --- Methodologies & Project Management ---
    "agile", "scrum", "kanban", "lean", "xp", "extreme programming", "waterfall", "safe", "scaled agile framework",
    "jira", "confluence", "trello", "asana", "slack", "microsoft teams",
    "project management", "product management", "product owner", "scrum master", "business analysis", "user stories", "sprint",

    # --- Specific Tools/Software (Add more very specific ones if truly common in your JDs) ---
    # "oracle enterprise manager", "oem", "rman", "data guard", "rac", "asm", "expdp", "impdp", # More DBA focused
    "qt framework", "qml", # If C++ GUI is common
    "sphinx", # For Python docs
    # "toad", "putty", "winscp", # General dev tools
    # "unity3d", "unity", "unreal engine", # Game dev

    # --- Soft Skills (Matched as keywords, their semantic meaning is harder for simple systems) ---
    "communication", "teamwork", "collaboration", "problem solving", "analytical skills",
    "leadership", "mentoring", "critical thinking", "adaptability", "time management",
    "attention to detail", "creativity", "interpersonal skills", "presentation skills",
    "customer service", "client relations", "stakeholder management",

    # --- Role Titles (Can help but also be noisy if not carefully used) ---
    # "web developer", "backend developer", "frontend developer", "full stack developer", "software engineer",
    # "devops engineer", "data engineer", "qa engineer", "mobile developer",
}


# --- Core NLP Function Definitions ---
def preprocess_text(text):
    if not text: return ""
    if not nlp_model: logger.warning("spaCy model not loaded for preprocess_text."); return ""
    try:
        doc = nlp_model(text.lower())
        return " ".join([token.lemma_ for token in doc if token.is_alpha and not token.is_stop and token.lemma_ not in stop_words and len(token.lemma_) > 1])
    except Exception as e: logger.error(f"Error in preprocess_text: {e}", exc_info=False); return ""

def get_targeted_text_for_skills(full_text, section_keywords):
    if not full_text: return ""
    # Corrected pattern to be more robust for section endings and capture content properly
    pattern_str = r"(?i)^\s*(?:" + "|".join(r"\b" + re.escape(kw) + r"\b" for kw in section_keywords) + r")\s*[:\-]?\s*\n(.*?)(?=\n\s*^\s*(?:" + "|".join(r"\b" + re.escape(next_kw) + r"\b" for next_kw in SKILL_KEYWORDS | set(section_keywords) | {"education", "projects", "summary", "awards", "publications", "references"}) + r")\s*[:\-]?\s*\n|^\s*$|\Z)"
    extracted_blocks = []
    try:
        for match in re.finditer(pattern_str, full_text, re.MULTILINE | re.DOTALL): # Added DOTALL
            if match.group(1): extracted_blocks.append(match.group(1).strip())
    except Exception as e: logger.error(f"Regex error in get_targeted_text_for_skills: {e}", exc_info=False)
    if extracted_blocks:
        combined_text = "\n\n".join(extracted_blocks)
        logger.debug(f"Extracted targeted text for JD skills (len: {len(combined_text)}) using: {section_keywords}")
        return combined_text
    else: logger.debug(f"No JD sections found for skill keywords {section_keywords}, using full text for JD skill extraction."); return full_text

def extract_skills(text):
    if not text: return []
    found_skills = set(); lower_text = text.lower()
    for skill in SKILL_KEYWORDS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, lower_text): found_skills.add(skill)
    if nlp_model:
        try:
            doc = nlp_model(text)
            for ent in doc.ents:
                ent_text_lower = ent.text.lower()
                if ent_text_lower in SKILL_KEYWORDS:
                     matching_skill = next((s for s in SKILL_KEYWORDS if s.lower() == ent_text_lower), ent.text)
                     found_skills.add(matching_skill)
                elif ent.label_ in ["ORG", "PRODUCT"] and ent.text in ["Microsoft", "Google", "Amazon Web Services", "AWS", "Azure", "React", "Angular", "Docker", "Kubernetes", "MySQL", "PostgreSQL", "MongoDB"]:
                     found_skills.add(ent.text); logger.debug(f"NER found relevant ORG/PRODUCT: {ent.text}")
        except Exception as e: logger.error(f"Error in NER skill extraction: {e}", exc_info=False)
    logger.debug(f"Extracted skills (from text len {len(text if text else '')}): {len(found_skills)} - {sorted(list(found_skills))}")
    return list(found_skills)

# --- Experience Extraction Functions ---
# Inside backend/app/utils/nlp.py
# Replace the existing extract_explicit_years_mention function with this one:

def extract_explicit_years_mention(text):
    """Extracts explicit 'X years of experience' mentions using regex. Returns max found."""
    if not text:
        return 0
    pattern = r'(\d{1,2}(?:\.\d{1,2})?)\s*\+?\s*(?:years?|yrs?|year)(?:\s*(?:of|in|with)?\s*exp(?:erience)?)?'
    years_found = []
    try: # Outer try for the whole findall operation
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match_group in matches:
            num_str = match_group[0] # The number part
            try: # Inner try for float conversion
                years = float(num_str)
                if 0 < years <= 50: # Basic sanity check <<< THIS IS LIKELY AROUND LINE 277
                    years_found.append(years)
            except ValueError: # <<< This 'except' correctly matches the inner 'try'
                logger.debug(f"Could not convert '{num_str}' to float for explicit years.")
                continue # Continue the for loop

        # This 'if years_found:' block must be at the same indentation level
        # as the 'for match_group in matches:' loop, but still inside the outer 'try'.
        if years_found:
            max_years = max(years_found)
            logger.debug(f"Explicit experience mentions found: {years_found}. Max: {max_years} years.")
            return max_years
        else:
            logger.debug("No explicit 'X years of experience' pattern found by regex.")
            return 0
            
    except Exception as e: # <<< This 'except' correctly matches the OUTER 'try'
        logger.error(f"Error during regex for explicit experience years: {e}", exc_info=True)
        return 0




def extract_experience_durations_from_sections(text_content):
    if not text_content:
        logger.debug("extract_experience_durations_from_sections: Received empty text_content.")
        return 0
    
    total_experience_years = 0
    
    experience_section_keywords = [
        "Work Experience", "Experience", "Employment History", "Relevant Experience",
        "Career History", "Professional Experience", "Positions Held",
        "Work Experience & Projects", "RELEVANT EXPERIENCE", "WORK EXPERIENCE",
        "PROFESSIONAL EXPERIENCE", "EMPLOYMENT HISTORY", "EXPERIENCE"
        # Added common variants including all caps versions
    ]
    
    # Keywords that strongly indicate the end of work experience for date parsing
    section_terminators = [
        "Education", "Academic Background", "Degrees", "Certifications", "Skills",
        "Technical Skills", "Projects", "OpenSource Contributions", "Achievements",
        "Popular Blogs", "Awards", "Publications", "References", "Languages",
        "Summary", "Objective", "Personal Details", "Contact", "CODING PROFILES",
        "PROJECTS", "OPENSOURCE CONTRIBUTIONS", "SKILLS", "EDUCATION", "ACHIEVEMENTS",
        "POPULAR BLOGS"  # Added uppercase versions
    ]

    lines = text_content.splitlines()
    relevant_text_for_dates = ""
    in_experience_section = False
    current_block_lines = []

    logger.info("--- STARTING EXPERIENCE SECTION SEARCH (Strict) ---")
    logger.info(f"Total lines in document: {len(lines)}")

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # More flexible header matching - check if line contains experience keywords
        is_experience_header = False
        for kw in experience_section_keywords:
            if kw.lower() in line_lower:
                # Additional check: the keyword should be prominent in the line (not just a small part)
                if len(kw) / len(line_stripped) > 0.5 or line_lower == kw.lower():
                    is_experience_header = True
                    break
        
        # More flexible terminator matching
        is_terminator_header = False
        for kw in section_terminators:
            if kw.lower() in line_lower:
                if len(kw) / len(line_stripped) > 0.5 or line_lower == kw.lower():
                    is_terminator_header = True
                    break

        if is_experience_header:
            if in_experience_section and current_block_lines:
                logger.info(f"  New experience header '{line_stripped}' found, processing previous block.")
                relevant_text_for_dates += "\n".join(current_block_lines).strip() + "\n\n"
            
            logger.info(f"MATCHED Experience Header: '{line_stripped}' at line index {i}")
            in_experience_section = True
            current_block_lines = []
            continue

        if is_terminator_header:
            if in_experience_section:
                logger.info(f"ENDER Found: '{line_stripped}' at line index {i}. Finalizing current experience block.")
                if current_block_lines:
                    relevant_text_for_dates += "\n".join(current_block_lines).strip() + "\n\n"
            in_experience_section = False
            current_block_lines = []

        if in_experience_section and line_stripped:
            current_block_lines.append(line_stripped)
            if len(current_block_lines) <= 10:  # Log first 10 lines
                logger.debug(f"  Adding to current experience block (line {i}): '{line_stripped}'")

    # Handle case where document ends while still in experience section
    if in_experience_section and current_block_lines:
        logger.info("End of document reached while in an experience section. Adding final block.")
        relevant_text_for_dates += "\n".join(current_block_lines).strip() + "\n\n"

    logger.info("--- FINISHED EXPERIENCE SECTION SEARCH ---")
    
    if not relevant_text_for_dates.strip():
        logger.warning("No text content extracted from identified experience sections for date parsing.")
        # Log first 20 lines of the document for debugging
        logger.info("First 20 lines of document for debugging:")
        for i, line in enumerate(lines[:20]):
            logger.info(f"Line {i}: '{line.strip()}'")
        return 0
    else:
        logger.info(f"Text content identified for date parsing (length {len(relevant_text_for_dates.strip())}):")
        logger.info(f"<<<<<<<<<<\n{relevant_text_for_dates.strip()}\n>>>>>>>>>>")

    # --- Enhanced Date Range Parsing ---
    # Normalize various dash types and fix spacing
    relevant_text_for_dates = relevant_text_for_dates.replace("–", " - ").replace("—", " - ")
    relevant_text_for_dates = relevant_text_for_dates.replace("\u2013", " - ").replace("\u2014", " - ")
    relevant_text_for_dates = relevant_text_for_dates.replace("−", " - ").replace("‐", " - ")
    
    # Fix month-year spacing issues
    relevant_text_for_dates = re.sub(r'(?i)\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)(\d{4})', r'\1 \2', relevant_text_for_dates)
    relevant_text_for_dates = re.sub(r'\s+', ' ', relevant_text_for_dates).strip()

    # Enhanced date range pattern - more flexible
    date_range_pattern = r"""
        (
            \b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember|t\.?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*\d{2,4}
            |
            \b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}
            |
            \b\d{4}\b
        )
        \s*
        (?:to|until|\-|–|—|\s+\-\s+)
        \s*
        (
            \b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember|t\.?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*\d{2,4}
            |
            \b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}
            |
            \b\d{4}\b
            |
            Present|Current|Till\s+Date|To\s+Date|Ongoing|Now
        )
    """
    
    date_flags = re.IGNORECASE | re.VERBOSE

    parsed_durations = []

    # Debug: show what we're searching in
    logger.info(f"Searching for date patterns in: '{relevant_text_for_dates}'")
    
    try:
        matches = list(re.finditer(date_range_pattern, relevant_text_for_dates, date_flags))
        logger.info(f"Date range regex found {len(matches)} potential match(es)")
        
        for match_idx, match in enumerate(matches):
            start_str, end_str = match.groups()
            full_match = match.group(0)
            logger.info(f"  Match {match_idx+1}: Full match: '{full_match}' -> Parsing '{start_str}' to '{end_str}'")
            
            try:
                # More flexible date parsing
                start_date = dateparser.parse(start_str.strip(), settings={
                    'PREFER_DATES_FROM': 'past', 
                    'STRICT_PARSING': False,
                    'DATE_ORDER': 'MDY'
                })
                
                end_date_obj = None
                end_str_clean = end_str.strip()
                
                if any(keyword in end_str_clean.lower() for keyword in ["present", "current", "till date", "to date", "ongoing", "now"]):
                    end_date_obj = datetime.now()
                    logger.debug(f"    End date is current: {end_date_obj.strftime('%Y-%m-%d')}")
                else:
                    end_date_obj = dateparser.parse(end_str_clean, settings={
                        'PREFER_DATES_FROM': 'past', 
                        'STRICT_PARSING': False,
                        'DATE_ORDER': 'MDY'
                    })

                logger.debug(f"    Parsed start_date: {start_date}")
                logger.debug(f"    Parsed end_date: {end_date_obj}")

                if start_date and end_date_obj:
                    if end_date_obj >= start_date:
                        duration_days = (end_date_obj - start_date).days
                        duration_years = duration_days / 365.25
                        
                        if 0 <= duration_years <= 50:  # Reasonable range
                            parsed_durations.append(duration_years)
                            logger.info(f"    -> PARSED OK: {start_date.strftime('%b %Y')} to {end_date_obj.strftime('%b %Y')} = {duration_years:.2f} years ({duration_days} days)")
                        else:
                            logger.warning(f"    -> Duration out of reasonable range ({duration_years:.2f} years). Skipping.")
                    else:
                        logger.warning(f"    -> End date ({end_date_obj}) is before start date ({start_date}). Skipping.")
                else:
                    logger.warning(f"    -> Could not parse dates. Start: {start_date}, End: {end_date_obj}")
                    
            except Exception as date_parse_err:
                logger.error(f"    -> Error parsing date range '{start_str}' - '{end_str}': {date_parse_err}")
                
    except Exception as e:
        logger.error(f"Error processing date ranges with regex: {e}", exc_info=True)

    if parsed_durations:
        total_experience_years = sum(parsed_durations)
        logger.info(f"SUCCESS: Total experience calculated: {total_experience_years:.2f} years from {len(parsed_durations)} period(s)")
        logger.info(f"Individual durations: {[f'{d:.2f}' for d in parsed_durations]}")
    else:
        logger.warning("No valid date ranges successfully parsed from identified experience text.")
        
    return total_experience_years


def extract_years_experience(text):
    if not text: 
        logger.warning("extract_years_experience: Received empty text")
        return 0
        
    logger.info("=== STARTING EXPERIENCE EXTRACTION ===")
    
    explicit_mention_years = extract_explicit_years_mention(text)
    duration_from_dates = extract_experience_durations_from_sections(text)
    
    final_experience_years = max(explicit_mention_years, duration_from_dates)
    
    logger.info(f"=== FINAL RESULT ===")
    logger.info(f"Explicit mention: {explicit_mention_years} years")
    logger.info(f"From date ranges: {duration_from_dates:.2f} years") 
    logger.info(f"Final experience: {final_experience_years:.2f} years")
    logger.info("=== END EXPERIENCE EXTRACTION ===")
    
    return final_experience_years

# --- Scoring Component Functions ---
def calculate_semantic_similarity(text1, text2):
    if not SENTENCE_TRANSFORMERS_AVAILABLE: logger.warning("ST lib not imported. Skip semantic similarity."); return 0.0
    if not sentence_model: logger.warning("ST model not loaded. Skip semantic similarity."); return 0.0
    if not text1 or not text2: logger.debug("Empty text for semantic similarity."); return 0.0
    try:
        embedding1 = sentence_model.encode(text1, convert_to_tensor=True, normalize_embeddings=True)
        embedding2 = sentence_model.encode(text2, convert_to_tensor=True, normalize_embeddings=True)
        cosine_score = util.pytorch_cos_sim(embedding1, embedding2).item(); return max(0.0, min(1.0, cosine_score))
    except Exception as e: logger.error(f"Error in calculate_semantic_similarity: {e}", exc_info=True); return 0.0

def calculate_skill_match_score(resume_skills, jd_skills):
    if not resume_skills or not jd_skills: logger.debug("Empty skill lists for skill_match_score."); return 0.0
    set_resume_skills = set(s.lower() for s in resume_skills); set_jd_skills = set(s.lower() for s in jd_skills)
    intersection = set_resume_skills.intersection(set_jd_skills); union = set_resume_skills.union(set_jd_skills)
    if not union: return 0.0
    jaccard_score = len(intersection) / len(union)
    logger.info(f"Skill Match: Intersection({len(intersection)})={sorted(list(intersection)) if intersection else []}, Union({len(union)}), Score={jaccard_score:.4f}")
    return jaccard_score

def calculate_experience_match_score(resume_years, required_years):
    if required_years <= 0: logger.debug("No required exp or invalid (<=0). Exp score = 0.5"); return 0.5
    if resume_years < 0: logger.warning(f"Invalid resume_years ({resume_years}). Exp score = 0.0"); return 0.0
    if resume_years == 0 : logger.debug(f"Resume shows 0 years, {required_years} required. Exp score = 0.1"); return 0.1
    if resume_years >= required_years: score = 1.0
    else: score = resume_years / required_years
    score = max(0.0, min(1.0, score))
    logger.debug(f"Experience Match Score: {score:.4f} (Resume: {resume_years:.2f} vs Required: {required_years})")
    return score

# --- Main Enhanced Scoring Function ---
def calculate_enhanced_relevance(resume_text, jd_text, required_experience_years=0):
    results = {"final_score": 0.0, "semantic_score": 0.0, "skill_score": 0.0, "experience_score": 0.0, "error": None}
    if not resume_text or not jd_text:
        results["error"] = "Missing resume_text or jd_text"; logger.warning(results["error"]); return results
    try:
        logger.debug("Calculating Semantic Score..."); results["semantic_score"] = calculate_semantic_similarity(resume_text, jd_text)
        logger.debug("Extracting Skills from Resume..."); resume_skills = extract_skills(resume_text)
        logger.info(f"RESUME SKILLS Extracted ({len(resume_skills)}): {sorted(list(set(s.lower() for s in resume_skills)))}")
        logger.debug("Focusing JD text for skills..."); jd_skill_focus_text = get_targeted_text_for_skills(jd_text, ["requirements", "qualifications", "skills", "experience", "responsibilities", "must have", "needed", "proficient in"])
        logger.debug("Extracting Skills from Focused JD Text..."); jd_skills = extract_skills(jd_skill_focus_text)
        logger.info(f"JD SKILLS Extracted ({len(jd_skills)} from focused text): {sorted(list(set(s.lower() for s in jd_skills)))}")
        results["skill_score"] = calculate_skill_match_score(resume_skills, jd_skills)
        logger.debug("Extracting Experience from Resume..."); resume_years = extract_years_experience(resume_text)
        results["experience_score"] = calculate_experience_match_score(resume_years, required_experience_years)
        final_score = (W_SEMANTIC * results["semantic_score"] + W_SKILL * results["skill_score"] + W_EXPERIENCE * results["experience_score"])
        results["final_score"] = max(0.0, min(1.0, final_score))
    except Exception as calculation_error:
         logger.error(f"Error during score calculation: {calculation_error}", exc_info=True)
         results["error"] = f"Calculation Error: {type(calculation_error).__name__}: {calculation_error}"; results["final_score"] = 0.0
    logger.info(f"Enhanced Relevance: Final={results['final_score']:.4f} (Sem={results['semantic_score']:.3f}, Skill={results['skill_score']:.3f}, Exp={results['experience_score']:.3f})")
    return results

# TF-IDF function
def calculate_tfidf_cosine_similarity(resume_text, jd_text):
    logger.debug("Calculating TF-IDF..."); processed_resume = preprocess_text(resume_text); processed_jd = preprocess_text(jd_text)
    if not processed_resume or not processed_jd: return 0.0
    try:
        vectorizer = TfidfVectorizer(); texts = [processed_resume, processed_jd]; tfidf_matrix = vectorizer.fit_transform(texts)
        if tfidf_matrix.shape[1] == 0: return 0.0
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2]); return max(0.0, min(1.0, float(cosine_sim[0][0])))
    except Exception as e: logger.error(f"Error in TF-IDF: {e}", exc_info=False); return 0.0