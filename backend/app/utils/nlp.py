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
    # Log as info or debug, as semantic similarity is optional if commented out later
    logging.info("sentence-transformers library not found. Semantic similarity will be skipped if enabled. "
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
nlp_model = load_spacy_model(NLP_MODEL_NAME)


sentence_model = None
if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME)
        logger.info(f"SentenceTransformer model '{SENTENCE_MODEL_NAME}' loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load SentenceTransformer model '{SENTENCE_MODEL_NAME}': {e}", exc_info=True)

stop_words = set()
try:
    # Try NLTK download check first
    try:
        nltk.data.find(f'corpora/stopwords')
        logger.debug("NLTK resource 'stopwords' found.")
    except LookupError:
        logger.info("NLTK resource 'stopwords' not found. Downloading...")
        try:
            nltk.download('stopwords')
            logger.info("NLTK resource 'stopwords' downloaded successfully.")
        except Exception as e:
            logger.error(f"Failed to download NLTK resource 'stopwords': {e}", exc_info=True)

    # Now try importing
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
    logger.debug("NLTK English stopwords loaded.")
except Exception as e:
    logger.error(f"Could not load NLTK stopwords: {e}")


# --- Skill Keywords ---
# CRITICAL: MANUALLY CURATE THIS LIST!
SKILL_KEYWORDS = {
    # Programming Languages
    "python", "java", "javascript", "js", "sql", "c++", "c#", "php", "ruby", "swift", "kotlin", "html", "css", "bash",

    # Frameworks/Libraries
    "flask", "django", "react", "react.js", "angular", "angular js", "angular.js", "vue", "vue.js", "node js", "node.js",
    "spring", "spring boot", ".net", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",

    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "sqlite", "redis", "nosql", "database",

    # Tools & Platforms
    "git", "docker", "kubernetes", "aws", "amazon web services", "azure", "gcp", "linux", "unix", "jira",

    # Concepts & Methodologies
    "rest", "api", "agile", "scrum", "machine learning", "deep learning", "nlp", "natural language processing",
    "data analysis", "data structures", "algorithms", "oop", "microservices", "ci/cd",

    # Roles (Use cautiously)
    "data scientist", "backend developer", "frontend developer", "web developer", "software engineer",

    # Soft Skills (Use cautiously)
    "communication", "teamwork", "problem solving", "leadership",
}


# --- Core NLP Function Definitions ---

def preprocess_text(text):
    """Cleans and preprocesses text: lowercase, lemmatize, remove stop words/punctuation."""
    if not text: return ""
    if not nlp_model:
        logger.warning("spaCy model not loaded. Cannot preprocess text.")
        return ""
    try:
        doc = nlp_model(text.lower())
        processed_tokens = [
            token.lemma_ for token in doc
            if token.is_alpha
            and not token.is_stop
            and token.lemma_ not in stop_words
            and len(token.lemma_) > 1
        ]
        return " ".join(processed_tokens)
    except Exception as e:
        logger.error(f"Error during spaCy preprocessing: {e}", exc_info=False)
        return ""

def get_jd_requirements_text(jd_text):
    """Tries to extract text specifically from Requirements/Qualifications sections."""
    if not jd_text: return ""
    patterns = [
        r'^(requirements|qualifications|required skills|minimum qualifications|must have|basic qualifications|your profile|responsibilities):?\s*\n(.*?)(?=\n\s*^\w+.*:?\s*\n|\Z)',
        r'^(skills|experience|education):?\s*\n(.*?)(?=\n\s*^\w+.*:?\s*\n|\Z)',
    ]
    extracted_text = ""
    flags = re.DOTALL | re.MULTILINE | re.IGNORECASE
    for pattern in patterns:
        matches = re.finditer(pattern, jd_text, flags)
        for match in matches:
            section_content = match.group(2)
            if section_content: extracted_text += section_content.strip() + "\n\n"
    if extracted_text:
        logger.debug(f"Extracted JD requirements text (length: {len(extracted_text)}).")
        return extracted_text.strip()
    else:
        logger.debug("No specific requirements/qualifications section found in JD, using full text for skill extraction.")
        return jd_text

def extract_skills(text):
    """Extract skills using keyword matching and basic NER."""
    if not text: return []
    found_skills = set()
    lower_text = text.lower()
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
        except Exception as e: logger.error(f"Error during NER skill extraction: {e}", exc_info=False)
    logger.debug(f"Extracted skills ({len(found_skills)}): {list(found_skills)}")
    return list(found_skills)

def extract_years_experience(text):
    """Extracts potential 'years of experience' mentions using regex. Returns max found."""
    if not text: return 0
    pattern = r'(\d{1,2}(?:\.\d{1,2})?)\s*(\+?\s*(?:years?|yrs?))(?:\s*of)?'
    years_found = []
    try:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                years = float(match[0]);
                if 0 < years <= 50: years_found.append(years)
            except ValueError: continue
        if years_found: max_years = max(years_found); logger.debug(f"Extracted years of experience candidates: {years_found}. Max: {max_years}"); return max_years
        else: logger.debug("No 'years of experience' pattern found."); return 0
    except Exception as e: logger.error(f"Error during regex experience extraction: {e}", exc_info=False); return 0

# --- Scoring Component Functions ---

# <<<--- DEFINITION of calculate_semantic_similarity placed BEFORE it's called --->>>
def calculate_semantic_similarity(text1, text2):
    """Calculates semantic similarity using Sentence-BERT embeddings."""
    # Check if library is available and model is loaded
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
        logger.error(f"Error calculating semantic similarity: {e}", exc_info=True)
        return 0.0
# <<<--- End of calculate_semantic_similarity definition --->>>

def calculate_skill_match_score(resume_skills, jd_skills):
    """Calculates a skill match score based on overlap (Jaccard Index)."""
    if not resume_skills or not jd_skills: logger.debug("Cannot calculate skill match score with empty skill lists."); return 0.0
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
    if required_years <= 0: logger.debug("No valid required years for experience matching (req <= 0). Returning neutral score."); return 0.5
    if resume_years < 0: logger.warning(f"Invalid resume_years ({resume_years}) for experience matching."); return 0.0
    if resume_years >= required_years: score = 1.0
    else: score = resume_years / required_years
    score = max(0.0, min(1.0, score))
    logger.debug(f"Experience Match Score: {score:.4f} (Resume: {resume_years} vs Required: {required_years})")
    return score


# --- Main Enhanced Scoring Function ---
def calculate_enhanced_relevance(resume_text, jd_text, required_experience_years=0):
    """
    Calculates an enhanced relevance score combining multiple factors.
    Returns a dictionary containing the final score and component scores.
    """
    # --- Initialize results dictionary FIRST ---
    results = {"final_score": 0.0, "semantic_score": 0.0, "skill_score": 0.0, "experience_score": 0.0, "error": None}
    # --------------------------------------------

    if not resume_text or not jd_text:
        results["error"] = "Missing resume_text or jd_text"; logger.warning(results["error"]); return results

    # --- Calculate Component Scores ---
    try:
        # 1. Semantic Similarity (Calls the function defined above)
        logger.debug("Calculating Semantic Score...")
        results["semantic_score"] = calculate_semantic_similarity(resume_text, jd_text) # <<< Call happens AFTER definition

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
         results["error"] = f"Calculation Error: {type(calculation_error).__name__}: {calculation_error}" # Store error type and message
         # Keep component scores as calculated before error, ensure final is 0
         results["final_score"] = 0.0

    # --- Return the results dictionary ---
    logger.info(f"Enhanced Relevance Calculated: Final={results['final_score']:.4f} "
                f"(Sem={results['semantic_score']:.3f}, Skill={results['skill_score']:.3f}, Exp={results['experience_score']:.3f})")
    return results


# Keep the simple TF-IDF function if needed for comparison
def calculate_tfidf_cosine_similarity(resume_text, jd_text):
    """Calculates relevance using TF-IDF and Cosine Similarity on PREPROCESSED text."""
    # ... (Implementation as before) ...
    logger.debug("Calculating TF-IDF Cosine Similarity...")
    processed_resume = preprocess_text(resume_text)
    processed_jd = preprocess_text(jd_text)
    if not processed_resume or not processed_jd: return 0.0
    try:
        vectorizer = TfidfVectorizer(); texts = [processed_resume, processed_jd]
        tfidf_matrix = vectorizer.fit_transform(texts)
        if tfidf_matrix.shape[1] == 0: return 0.0
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        score = max(0.0, min(1.0, float(cosine_sim[0][0])))
        logger.debug(f"Calculated TF-IDF Cosine Similarity: {score:.4f}")
        return score
    except Exception as e:
        logger.error(f"Error calculating TF-IDF/Cosine Similarity: {e}", exc_info=False); return 0.0