# main_process_data.py

import os
import logging
# Optional: Remove the extra print statements added for debugging if desired
# print("--- Python script starting ---")

# --- Imports ---
# Import parsing functions
from src.parsers import extract_text_from_file, read_job_description
# Import the NEW enhanced scoring function and the nlp_model check variable
from src.nlp import calculate_enhanced_relevance, nlp_model

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# Adjust these paths based on where you saved the data
DATA_FOLDER = "data"
RESUME_FOLDER = os.path.join(DATA_FOLDER, "resumes")
JD_FOLDER = os.path.join(DATA_FOLDER, "job_descriptions")
# Specify the job description file you want to compare against
TARGET_JD_FILENAME = "sample_jd.txt"
# TODO: Implement proper extraction of required experience from JD text later
# For now, hardcode a value based on the sample JD used
HARDCODED_REQUIRED_YEARS = 2 # Example: Assume the sample JD requires 2 years

# --- Main Processing Logic ---
def main():
    # print("--- main() function entered ---") # Optional: remove debug print
    logger.info("--- Starting Resume Processing ---")

    # 1. Load the target Job Description
    target_jd_path = os.path.join(JD_FOLDER, TARGET_JD_FILENAME)
    # print(f"--- Attempting to load JD from: {target_jd_path} ---") # Optional: remove debug print
    logger.info(f"Loading Target Job Description from: {target_jd_path}")
    job_description_text = read_job_description(target_jd_path)

    if not job_description_text:
        # print(f"--- ERROR: Failed to load JD. Exiting main(). ---") # Optional: remove debug print
        logger.error("Failed to load job description. Exiting.")
        return # Exit if JD cannot be loaded

    # print(f"--- JD loaded successfully. Length: {len(job_description_text)} ---") # Optional: remove debug print
    logger.info("Job Description loaded successfully.")

    # 2. Process Resumes in the folder
    # print(f"--- Checking resume folder: {RESUME_FOLDER} ---") # Optional: remove debug print
    logger.info(f"Processing resumes from folder: {RESUME_FOLDER}")
    if not os.path.isdir(RESUME_FOLDER):
        # print(f"--- ERROR: Resume folder not found. Exiting main(). ---") # Optional: remove debug print
        logger.error(f"Resume folder not found: {RESUME_FOLDER}. Please create it and add resume files.")
        return

    # print(f"--- Starting loop through resume folder ---") # Optional: remove debug print
    results = []
    processed_count = 0
    failed_count = 0

    try:
        file_list = os.listdir(RESUME_FOLDER)
        # print(f"--- Found {len(file_list)} items in resume folder ---") # Optional: remove debug print
    except FileNotFoundError:
        logger.error(f"Resume folder path not found during listdir: {RESUME_FOLDER}")
        return
    except Exception as e:
        logger.error(f"Error listing files in resume folder {RESUME_FOLDER}: {e}", exc_info=True)
        return


    for filename in file_list:
        file_path = os.path.join(RESUME_FOLDER, filename)

        # Skip directories, process files
        if os.path.isfile(file_path):
            # print(f"--- Processing file: {filename} ---") # Optional: remove debug print
            logger.info(f"Processing file: {filename}")

            # 3. Extract text from the current resume file
            resume_text = extract_text_from_file(file_path)

            if resume_text:
                processed_count += 1
                # print(f"---   Extracted text from {filename}. Calculating score... ---") # Optional: remove debug print

                # 4. Calculate ENHANCED relevance score against the loaded JD
                #    Pass the hardcoded required years
                score_data = calculate_enhanced_relevance(resume_text,
                                                      job_description_text,
                                                      HARDCODED_REQUIRED_YEARS)

                # Store the results: filename and the dictionary returned by the function
                results.append({
                    "filename": filename,
                    "score_details": score_data # Store the whole dictionary
                })

                # Log the final score for the file (extracted from the dictionary)
                final_score_log = score_data.get('final_score', 0.0)
                # print(f"---   Score for {filename}: {final_score_log:.4f} ---") # Optional: remove debug print
                logger.info(f" -> Calculated Final Score for {filename}: {final_score_log:.4f}")

            else:
                failed_count += 1
                # print(f"---   Failed to extract text from {filename} ---") # Optional: remove debug print
                logger.warning(f" -> Failed to extract text from {filename}.")
        # else:
            # print(f"--- Skipping non-file item: {filename} ---") # Optional: remove debug print


    # print(f"--- Finished loop. Processed: {processed_count}, Failed: {failed_count} ---") # Optional: remove debug print
    logger.info("--- Processing Complete ---")
    logger.info(f"Successfully processed: {processed_count} resumes.")
    logger.info(f"Failed to parse: {failed_count} files.")

    # 5. Display Results (Sorted by Enhanced Score)
    if results:
        # Sort results by the 'final_score' within the 'score_details' dictionary
        # Use .get() with defaults for safety in case 'score_details' or 'final_score' is missing
        try:
            results.sort(key=lambda x: x.get("score_details", {}).get("final_score", 0.0), reverse=True)
        except Exception as e:
            logger.error(f"Error sorting results: {e}", exc_info=True)
            print("ERROR: Could not sort results.")


        print("\n--- Top Matching Resumes (Enhanced Score) ---") # Use print for final user output
        logger.info("\n--- Top Matching Resumes (Enhanced Score) ---") # Log as well
        for i, result in enumerate(results[:10]): # Show top 10 or fewer if less results
            details = result.get("score_details", {}) # Safely get the details dict
            # Safely get individual scores, defaulting to 0.0 if key is missing
            final_s = details.get("final_score", 0.0)
            semantic_s = details.get("semantic_score", 0.0)
            skill_s = details.get("skill_score", 0.0)
            exp_s = details.get("experience_score", 0.0)

            # Print the formatted output
            print(f"{i+1}. {result.get('filename', 'N/A')}: Score = {final_s:.4f} "
                  f"(Sem: {semantic_s:.3f}, Skill: {skill_s:.3f}, Exp: {exp_s:.3f})")
    else:
        # print("\n--- No results to display ---") # Optional: remove debug print
        logger.info("No resumes were successfully processed to show results.")
        print("\n--- No results to display ---")


if __name__ == "__main__":
    # print(f"--- Running main check (__name__ == '__main__') ---") # Optional: remove debug print
    # Ensure necessary resources are available before running main logic
    if not nlp_model: # Check if spaCy model loaded successfully in nlp.py
        # print(f"--- ERROR: nlp_model is not loaded. Cannot run main(). ---") # Optional: remove debug print
        logger.error("FATAL: spaCy model failed to load. Please check installation ('pip install spacy') and model download ('python -m spacy download en_core_web_lg').")
    else:
        # print(f"--- nlp_model loaded. Calling main() ---") # Optional: remove debug print
        main()
        # print(f"--- main() function finished ---") # Optional: remove debug print

# print("--- Python script finished ---") # Optional: remove debug print