# src/nlp.py

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import logging
import nltk
import os # Needed for path joining if loading resources

# Attempt to import sentence-transformers related libraries
try:
    from sentence_transformers import SentenceTransformer, util
    import torch # Often used with sentence-transformers
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logging.warning("sentence-transformers library not found. Semantic similarity will be skipped. "
                    "Install with: pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None # Define as None to avoid NameErrors later
    util = None
    torch = None


# Define logger early so helper functions can use it
logger = logging.getLogger(__name__)

# --- Globals / Setup ---
# Use the larger spaCy model for better NER
NLP_MODEL_NAME = "en_core_web_lg"
# Sentence Transformer model for semantic similarity
SENTENCE_MODEL_NAME = 'all-MiniLM-L6-v2'

# --- Weights for Final Score (Ensure they sum to 1.0) ---
# Adjust these based on importance for your use case
W_SEMANTIC = 0.30  # Weight for semantic meaning similarity
W_SKILL = 0.50     # Weight for specific skill overlap (often most important)
W_EXPERIENCE = 0.20 # Weight for years of experience match


# --- Helper Function Definitions (Must come BEFORE they are called) ---

def download_nltk_resource(resource_id, resource_name):
    """Downloads an NLTK resource if not found."""
    try:
        # Check if the resource is available locally
        nltk.data.find(f'corpora/{resource_id}')
        logger.debug(f"NLTK resource '{resource_name}' found.")
    except nltk.downloader.DownloadError:
        logger.info(f"NLTK resource '{resource_name}' not found. Downloading...")
        try:
            nltk.download(resource_id)
            logger.info(f"NLTK resource '{resource_name}' downloaded successfully.")
        except Exception as e:
            # Catch potential errors during download (network issues, etc.)
            logger.error(f"Failed to download NLTK resource '{resource_name}': {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error checking NLTK resource '{resource_name}': {e}", exc_info=True)


def load_spacy_model(model_name):
    """Loads a spaCy model, attempting download if not found."""
    try:
        # Try loading the model directly
        nlp = spacy.load(model_name)
        logger.info(f"spaCy model '{model_name}' loaded successfully.")
        return nlp
    except OSError:
        # Model not found, attempt to download
        logger.warning(f"spaCy model '{model_name}' not found. Attempting download...")
        try:
            spacy.cli.download(model_name)
            # After download, try loading again
            nlp = spacy.load(model_name)
            logger.info(f"spaCy model '{model_name}' downloaded and loaded successfully.")
            return nlp
        except SystemExit as e:
             # spacy.cli.download can raise SystemExit on failure
             logger.error(f"spaCy download command failed for model '{model_name}'. Is the name correct? Error: {e}", exc_info=True)
             return None
        except Exception as e:
            # Catch any other errors during download or loading
            logger.error(f"Failed to download or load spaCy model '{model_name}' after download attempt: {e}", exc_info=True)
            return None
    except Exception as e:
        # Catch unexpected errors during the initial load attempt
        logger.error(f"Unexpected error loading spaCy model '{model_name}': {e}", exc_info=True)
        return None

# --- Load Resources at Module Level (Calls the functions defined above) ---

# Ensure NLTK stopwords data is available
download_nltk_resource('stopwords', 'stopwords')

# Load the primary spaCy NLP model
nlp_model = load_spacy_model(NLP_MODEL_NAME)

# Load the Sentence Transformer model if library is available
sentence_model = None
if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME)
        logger.info(f"SentenceTransformer model '{SENTENCE_MODEL_NAME}' loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load SentenceTransformer model '{SENTENCE_MODEL_NAME}': {e}", exc_info=True)
        # sentence_model remains None

# Load NLTK stopwords after attempting download
stop_words = set() # Default to empty set
try:
    # Import here after ensuring data is downloaded
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
    logger.debug("NLTK English stopwords loaded.")
except ImportError:
    logger.error("Could not import NLTK stopwords. Please ensure NLTK is installed correctly.")
except LookupError:
    logger.error("NLTK stopwords corpus not found even after download attempt. Check NLTK setup.")
except Exception as e:
    logger.error(f"Unexpected error loading NLTK stopwords: {e}", exc_info=True)


# --- Skill Keywords (CRITICAL: Expand this list significantly!) ---
# TODO: Customize this list based on the job roles you are targeting
SKILL_KEYWORDS = {
    # Programming Languages & Scripting
    "python", "java", "c++", "c#", "javascript", "typescript", "html", "css", "php",
    "ruby", "go", "swift", "kotlin", "scala", "perl", "bash", "shell scripting", "sql",

    # Frontend Frameworks/Libraries
    "react", "react.js", "angular", "angular.js", "vue", "vue.js", "next.js", "svelte",
    "jquery", "bootstrap", "tailwind", "material ui", "redux", "mobx",

    # Backend Frameworks/Libraries
    "node.js", "express", "express.js", "flask", "django", "ruby on rails", "laravel",
    "spring", "spring boot", ".net", "asp.net", "fastapi",

    # Databases & Data Storage
    "nosql", "mongodb", "postgresql", "mysql", "sqlite", "microsoft sql server", "oracle",
    "redis", "memcached", "elasticsearch", "cassandra", "dynamodb", "firebase", "database",

    # APIs & Protocols
    "rest", "restful", "graphql", "grpc", "soap", "json", "xml", "api", "http", "tcp/ip",

    # Cloud Platforms & Services (Examples)
    "aws", "amazon web services", "azure", "microsoft azure", "gcp", "google cloud platform",
    "heroku", "digitalocean", "lambda", "azure functions", "google cloud functions", "serverless",
    "ec2", "s3", "rds", "eks", "ecs", "azure vm", "azure blob storage", "aks",

    # DevOps & Infrastructure
    "docker", "kubernetes", "containerization", "ci/cd", "continuous integration", "continuous deployment",
    "jenkins", "gitlab ci", "github actions", "travis ci", "circleci", "terraform", "ansible",
    "puppet", "chef", "infrastructure as code", "monitoring", "logging", "prometheus", "grafana", "elk stack",

    # OS & Systems
    "linux", "unix", "ubuntu", "centos", "windows server", "macos", "system administration",

    # ML/AI/Data Science
    "machine learning", "deep learning", "nlp", "natural language processing", "computer vision",
    "data analysis", "data science", "pandas", "numpy", "scipy", "scikit-learn", "statsmodels",
    "tensorflow", "pytorch", "keras", "jupyter", "matplotlib", "seaborn", "big data", "spark", "hadoop",

    # Methodologies & Project Management
    "agile", "scrum", "kanban", "waterfall", "jira", "confluence", "project management",
    "product management", "lean", "six sigma",

    # Version Control
    "git", "github", "gitlab", "bitbucket", "svn", "version control",

    # Testing
    "testing", "unit testing", "integration testing", "end-to-end testing", "e2e testing",
    "automation testing", "manual testing", "selenium", "cypress", "playwright", "jest",
    "mocha", "chai", "junit", "pytest", "postman",

    # Soft Skills (Harder to match reliably with text alone)
    "communication", "teamwork", "collaboration", "problem solving", "leadership", "mentoring",
    "critical thinking", "adaptability", "time management", "creativity", "presentation skills"
}


# --- Core NLP Function Definitions ---

def preprocess_text(text):
    """Cleans and preprocesses text: lowercase, lemmatize, remove stop words/punctuation."""
    if not text:
        return "" # Return empty string for empty input
    if not nlp_model:
        logger.warning("spaCy model not loaded. Cannot preprocess text.")
        return "" # Cannot preprocess without model

    try:
        # Use spaCy pipeline for efficient processing
        doc = nlp_model(text.lower())
        processed_tokens = [
            token.lemma_ for token in doc
            if token.is_alpha # Keep only alphabetic tokens
            # Use spaCy's default stop list AND our NLTK list
            and not token.is_stop
            and token.lemma_ not in stop_words
            and len(token.lemma_) > 1 # Remove single characters
        ]
        return " ".join(processed_tokens)
    except Exception as e:
        logger.error(f"Error during spaCy preprocessing: {e}", exc_info=False) # Keep log cleaner
        return "" # Return empty string on error


def extract_skills(text):
    """Extract skills using keyword matching and basic NER."""
    if not text: return []
    if not nlp_model:
        logger.warning("spaCy model not loaded. Cannot perform NER for skill extraction.")
        # Fallback to just keyword matching if NER model isn't available
        found_skills = set()
        lower_text = text.lower()
        for skill in SKILL_KEYWORDS:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, lower_text):
                found_skills.add(skill)
        return list(found_skills)

    # Proceed with both keyword and NER if model exists
    found_skills = set()
    # 1. Keyword Matching
    lower_text = text.lower()
    for skill in SKILL_KEYWORDS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, lower_text):
            found_skills.add(skill)

    # 2. Basic NER (using the loaded spaCy model)
    try:
        doc = nlp_model(text)
        for ent in doc.ents:
            ent_text_lower = ent.text.lower()
            # Check if the entity text itself is a skill keyword (handles variations NER might catch)
            if ent_text_lower in SKILL_KEYWORDS:
                 matching_skill = next((s for s in SKILL_KEYWORDS if s.lower() == ent_text_lower), ent.text)
                 found_skills.add(matching_skill)
            # Optional: Add entities with specific labels if they seem relevant (e.g., known tech companies)
            elif ent.label_ in ["ORG", "PRODUCT"] and ent.text in ["Microsoft", "Google", "Amazon Web Services", "AWS", "Azure", "React", "Angular", "Docker", "Kubernetes"]:
                 found_skills.add(ent.text) # Add known tech orgs/products
                 logger.debug(f"NER found relevant ORG/PRODUCT: {ent.text}")

    except Exception as e:
        logger.error(f"Error during NER skill extraction: {e}", exc_info=False)

    logger.debug(f"Extracted skills ({len(found_skills)}): {list(found_skills)}")
    return list(found_skills)


def extract_years_experience(text):
    """Extracts potential 'years of experience' mentions using regex. Returns max found."""
    if not text: return 0

    # Regex pattern:
    # - (\d{1,2}(?:\.\d{1,2})?) : Matches 1 or 2 digits, optionally followed by '.' and 1 or 2 digits (e.g., 5, 10, 2.5, 1.75)
    # - \s*                   : Optional whitespace
    # - (\+?\s*years?|yr?s?) : Optional '+', optional space, 'year' or 'years' or 'yr' or 'yrs'
    # - (?:\s*of)?            : Optional non-capturing group for optional whitespace and 'of'
    # Case insensitive
    # Increased flexibility for year formats and units
    pattern = r'(\d{1,2}(?:\.\d{1,2})?)\s*(\+?\s*(?:years?|yrs?))(?:\s*of)?'
    years_found = []
    try:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                years = float(match[0])
                # Basic sanity check (e.g., ignore values > 50 years)
                if 0 < years <= 50:
                    years_found.append(years)
            except ValueError:
                continue

        if years_found:
            max_years = max(years_found)
            logger.debug(f"Extracted years of experience candidates: {years_found}. Max: {max_years}")
            return max_years
        else:
            logger.debug("No 'years of experience' pattern found.")
            return 0
    except Exception as e:
        logger.error(f"Error during regex experience extraction: {e}", exc_info=False)
        return 0


# --- Scoring Component Functions ---

def calculate_semantic_similarity(text1, text2):
    """Calculates semantic similarity using Sentence-BERT embeddings."""
    if not SENTENCE_TRANSFORMERS_AVAILABLE or not sentence_model:
        logger.warning("SentenceTransformer model not available/loaded. Skipping semantic similarity.")
        return 0.0 # Return neutral score if model not available
    if not text1 or not text2:
        logger.debug("Cannot calculate semantic similarity with empty text.")
        return 0.0

    try:
        # Encode texts into embeddings
        embedding1 = sentence_model.encode(text1, convert_to_tensor=True, normalize_embeddings=True)
        embedding2 = sentence_model.encode(text2, convert_to_tensor=True, normalize_embeddings=True)
        # Calculate cosine similarity
        cosine_score = util.pytorch_cos_sim(embedding1, embedding2).item()
        # Clamp score between 0 and 1
        score = max(0.0, min(1.0, cosine_score))
        logger.debug(f"Calculated Semantic Similarity: {score:.4f}")
        return score
    except Exception as e:
        logger.error(f"Error calculating semantic similarity: {e}", exc_info=True) # Log full trace for errors here
        return 0.0


def calculate_skill_match_score(resume_skills, jd_skills):
    """Calculates a skill match score based on overlap (Jaccard Index)."""
    if not resume_skills or not jd_skills:
        logger.debug("Cannot calculate skill match score with empty skill lists.")
        return 0.0

    set_resume_skills = set(s.lower() for s in resume_skills)
    set_jd_skills = set(s.lower() for s in jd_skills)
    intersection = set_resume_skills.intersection(set_jd_skills)
    union = set_resume_skills.union(set_jd_skills)

    if not union: return 0.0

    jaccard_score = len(intersection) / len(union)
    logger.debug(f"Skill Match Score (Jaccard): {jaccard_score:.4f} ({len(intersection)} intersection / {len(union)} union)")
    return jaccard_score


def calculate_experience_match_score(resume_years, required_years):
    """Calculates a simple score based on years of experience match."""
    if required_years <= 0:
        logger.debug("No valid required years for experience matching (req <= 0). Returning neutral score.")
        return 0.5 # Neutral score if no requirement specified or invalid
    if resume_years < 0:
         logger.warning(f"Invalid resume_years ({resume_years}) for experience matching.")
         return 0.0

    # Simple linear scaling up to the requirement, capped at 1.0
    if resume_years >= required_years:
        score = 1.0
    else:
        # Score increases linearly from 0 to 1 as resume_years approaches required_years
        score = resume_years / required_years

    # Ensure score is between 0 and 1
    score = max(0.0, min(1.0, score))

    logger.debug(f"Experience Match Score: {score:.4f} (Resume: {resume_years} vs Required: {required_years})")
    return score


# --- Main Enhanced Scoring Function ---

def calculate_enhanced_relevance(resume_text, jd_text, required_experience_years=0):
    """
    Calculates an enhanced relevance score combining multiple factors.
    Returns a dictionary containing the final score and component scores.
    """
    results = {
        "final_score": 0.0,
        "semantic_score": 0.0,
        "skill_score": 0.0,
        "experience_score": 0.0,
        "error": None
    }

    if not resume_text or not jd_text:
        results["error"] = "Missing resume_text or jd_text"
        logger.warning(results["error"])
        return results # Return default scores (0)

    # --- Calculate Component Scores ---
    # 1. Semantic Similarity (using raw texts is often better here)
    logger.debug("Calculating Semantic Score...")
    results["semantic_score"] = calculate_semantic_similarity(resume_text, jd_text)

    # 2. Skill Extraction & Matching
    logger.debug("Extracting Skills...")
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text) # Extract skills from JD too
    logger.debug("Calculating Skill Match Score...")
    results["skill_score"] = calculate_skill_match_score(resume_skills, jd_skills)

    # 3. Experience Extraction & Matching
    logger.debug("Extracting Experience...")
    resume_years = extract_years_experience(resume_text)
    logger.debug("Calculating Experience Match Score...")
    results["experience_score"] = calculate_experience_match_score(resume_years, required_experience_years)

    # --- Calculate Final Weighted Score ---
    final_score = (W_SEMANTIC * results["semantic_score"] +
                   W_SKILL * results["skill_score"] +
                   W_EXPERIENCE * results["experience_score"])

    # Ensure final score is capped between 0 and 1
    results["final_score"] = max(0.0, min(1.0, final_score))

    logger.info(f"Enhanced Relevance Calculated: Final={results['final_score']:.4f} "
                f"(Sem: {results['semantic_score']:.3f}, Skill: {results['skill_score']:.3f}, Exp: {results['experience_score']:.3f})")

    return results

# --- Simple TF-IDF Cosine Similarity (Optional: Keep for comparison?) ---
def calculate_tfidf_cosine_similarity(resume_text, jd_text):
    """Calculates relevance using TF-IDF and Cosine Similarity on PREPROCESSED text."""
    logger.debug("Calculating TF-IDF Cosine Similarity...")
    processed_resume = preprocess_text(resume_text)
    processed_jd = preprocess_text(jd_text)

    if not processed_resume or not processed_jd:
        logger.debug("Cannot calculate TF-IDF score with empty processed text.")
        return 0.0

    try:
        vectorizer = TfidfVectorizer()
        texts = [processed_resume, processed_jd]
        tfidf_matrix = vectorizer.fit_transform(texts)

        if tfidf_matrix.shape[1] == 0:
             logger.warning("TF-IDF matrix has zero features (vocabulary likely empty after processing). Returning score 0.")
             return 0.0

        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        score = float(cosine_sim[0][0])
        score = max(0.0, min(1.0, score)) # Clamp score
        logger.debug(f"Calculated TF-IDF Cosine Similarity: {score:.4f}")
        return score

    except ValueError as e:
         logger.warning(f"TF-IDF ValueError (likely empty vocabulary): {e}")
         return 0.0
    except Exception as e:
        logger.error(f"Error calculating TF-IDF/Cosine Similarity: {e}", exc_info=False)
        return 0.0