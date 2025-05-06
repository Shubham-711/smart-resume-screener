# backend/app/utils/nlp.py

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import logging # <<< IMPORT LOGGING HERE
import nltk
import os

# Attempt to import sentence-transformers related libraries
try:
    from sentence_transformers import SentenceTransformer, util
    import torch # Often used with sentence-transformers
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logging.warning("sentence-transformers library not found. Semantic similarity will be skipped. "
                    "Install with: pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    util = None
    torch = None

# --- DEFINE LOGGER IMMEDIATELY AFTER IMPORTS ---
logger = logging.getLogger(__name__)
# ---------------------------------------------

# --- NLTK Punkt Download Check ---
# Now it's safe to use logger here
try:
    nltk.data.find('tokenizers/punkt')
    logger.debug("NLTK resource 'punkt' found.") # This line should now work
except LookupError: # Catch the correct error
    logger.info("NLTK resource 'punkt' not found. Downloading...")
    try:
        nltk.download('punkt')
        logger.info("NLTK resource 'punkt' downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download NLTK resource 'punkt': {e}", exc_info=True)
except Exception as e:
     logger.error(f"Error checking NLTK resource 'punkt': {e}", exc_info=True)
# ---------------------------------

# --- Globals / Setup ---
# Use the smaller spaCy model for now due to resource issues
# NLP_MODEL_NAME = "en_core_web_lg"
NLP_MODEL_NAME = "en_core_web_sm" # <<< KEEPING SMALL MODEL FOR NOW
# Sentence Transformer model for semantic similarity
SENTENCE_MODEL_NAME = 'all-MiniLM-L6-v2'

# --- Weights for Final Score ---
W_SEMANTIC = 0.30
W_SKILL = 0.50
W_EXPERIENCE = 0.20

# --- Helper Function Definitions ---
# ... (Keep the download_nltk_resource [Note: NLTK download checks moved above now], load_spacy_model functions) ...
def load_spacy_model(model_name):
    # ... (implementation from previous correct version) ...
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
             logger.error(f"spaCy download command failed for model '{model_name}'. Is the name correct? Error: {e}", exc_info=True)
             return None
        except Exception as e:
            logger.error(f"Failed to download or load spaCy model '{model_name}' after download attempt: {e}", exc_info=True)
            return None
    except Exception as e:
        logger.error(f"Unexpected error loading spaCy model '{model_name}': {e}", exc_info=True)
        return None


# --- Load Resources at Module Level ---
# Moved NLTK download checks near top after logger definition
# download_nltk_resource('stopwords', 'stopwords') # Still call this if needed for stopwords

nlp_model = load_spacy_model(NLP_MODEL_NAME)

# Keep Sentence Transformer loading commented out for now
sentence_model = None
# if SENTENCE_TRANSFORMERS_AVAILABLE:
#    try:
#        sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME)
#        logger.info(f"SentenceTransformer model '{SENTENCE_MODEL_NAME}' loaded successfully.")
#    except Exception as e:
#        logger.error(f"Failed to load SentenceTransformer model '{SENTENCE_MODEL_NAME}': {e}", exc_info=True)

stop_words = set()
try:
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
    logger.debug("NLTK English stopwords loaded.")
except Exception as e:
    logger.error(f"Could not load NLTK stopwords: {e}")


# --- Skill Keywords ---
# CRITICAL: MANUALLY CURATE THIS LIST!
SKILL_KEYWORDS = {
    # Programming Languages
    "python", "java", "javascript", "js", "sql",

    # Frameworks/Libraries
    "flask", "django", "react", "react.js", "pandas", "numpy", "scikit-learn",

    # Databases
    "postgresql", "postgres", "mysql", "redis",

    # Tools & Platforms
    "git", "docker", "aws", "amazon web services",

    # Concepts & Methodologies
    "rest", "api", "agile", "scrum", "machine learning", "nlp", "natural language processing",

    # Roles (Use cautiously)
    "data scientist", "backend developer",

    # Soft Skills (Use cautiously)
    "communication", "teamwork",

    # Add MANY more based on your analysis!
}
    # ... (Your curated list should be here) ...

# Ensure all subsequent functions using 'logger' appear AFTER
# the logger = logging.getLogger(__name__) line.

# Example: Keep the rest of the functions from the previous complete nlp.py here...

def preprocess_text(text):
    # ... (implementation) ...
    if not nlp_model: logger.warning(...); return "" # logger is defined now
    # ... (rest of implementation) ...

def get_jd_requirements_text(jd_text):
    # ... (implementation using re) ...
    if extracted_text: logger.debug(...); return extracted_text.strip() # logger is defined now
    # ... (rest of implementation) ...

# ... and so on for all other functions ...

# Inside nlp.py
def calculate_enhanced_relevance(resume_text, jd_text, required_experience_years=0):
    """
    Calculates an enhanced relevance score combining multiple factors.
    Returns a dictionary containing the final score and component scores.
    """
    # --- THIS MUST BE THE FIRST THING ---
    results = {
        "final_score": 0.0,
        "semantic_score": 0.0,
        "skill_score": 0.0,
        "experience_score": 0.0,
        "error": None
    }
    # ------------------------------------

    # Now the rest of the function checks and calculations
    if not resume_text or not jd_text:
        results["error"] = "Missing resume_text or jd_text"
        logger.warning(results["error"])
        return results # Return the initialized dict with the error

    # --- Calculate Component Scores ---
    try: # Add a try block around calculations in case they fail
        # 1. Semantic Similarity
        logger.debug("Calculating Semantic Score...")
        results["semantic_score"] = calculate_semantic_similarity(resume_text, jd_text)

        # 2. Skill Extraction & Matching
        logger.debug("Extracting Skills from Resume...")
        resume_skills = extract_skills(resume_text)
        logger.debug("Extracting Requirements Text from JD...")
        jd_requirements_text = get_jd_requirements_text(jd_text)
        logger.debug("Extracting Skills from JD Requirements Text...")
        jd_skills = extract_skills(jd_requirements_text)
        logger.debug("Calculating Skill Match Score...")
        results["skill_score"] = calculate_skill_match_score(resume_skills, jd_skills)

        # 3. Experience Extraction & Matching
        logger.debug("Extracting Experience from Resume...")
        resume_years = extract_years_experience(resume_text)
        logger.debug("Calculating Experience Match Score...")
        results["experience_score"] = calculate_experience_match_score(resume_years, required_experience_years)

        # --- Calculate Final Weighted Score ---
        final_score = (W_SEMANTIC * results["semantic_score"] +
                       W_SKILL * results["skill_score"] +
                       W_EXPERIENCE * results["experience_score"])
        results["final_score"] = max(0.0, min(1.0, final_score))

    except Exception as calculation_error:
         logger.error(f"Error during score calculation: {calculation_error}", exc_info=True)
         results["error"] = f"Calculation Error: {calculation_error}"
         # Keep component scores as they were before the error if needed, or zero them out
         # results["final_score"] = 0.0 # Ensure score is 0 on calculation error

    # --- Return the results dictionary ---
    logger.info(f"Enhanced Relevance Calculated: Final={results['final_score']:.4f} "
                f"(Sem={results['semantic_score']:.3f}, Skill={results['skill_score']:.3f}, Exp={results['experience_score']:.3f})")
    return results # <<< Make sure this line returns the 'results' dict