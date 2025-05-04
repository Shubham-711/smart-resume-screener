import PyPDF2
import docx
import textract # Needs OS dependencies like antiword, pdftotext
import os
import logging

# Configure basic logging for this script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            # logger.info(f"Reading PDF: {os.path.basename(file_path)}, Pages: {len(reader.pages)}")
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_err:
                    logger.debug(f"Debug: Error extracting text from page {i+1} of {os.path.basename(file_path)}: {page_err}") # Use debug for less noise
            # logger.info(f"Finished reading PDF: {os.path.basename(file_path)}. Text length: {len(text)}")
        return text.strip() if text else None
    except FileNotFoundError:
        logger.error(f"PDF file not found: {file_path}")
        return None
    except PyPDF2.errors.PdfReadError as e:
         logger.warning(f"PyPDF2 could not read PDF {os.path.basename(file_path)} (possibly encrypted or corrupted): {e}")
         return None # Indicate failure to read
    except Exception as e:
        logger.error(f"Unexpected error reading PDF {file_path}: {e}", exc_info=False) # Keep log clean unless debugging
        return None

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file using python-docx."""
    try:
        doc = docx.Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        # logger.info(f"Reading DOCX: {os.path.basename(file_path)}. Paragraphs: {len(full_text)}")
        text = "\n".join(full_text)
        return text.strip() if text else None
    except FileNotFoundError:
        logger.error(f"DOCX file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading DOCX {file_path}: {e}", exc_info=False)
        return None

def extract_text_using_textract(file_path):
    """Extracts text using the textract library as a fallback."""
    try:
        # logger.info(f"Attempting text extraction with textract for: {os.path.basename(file_path)}")
        byte_string = textract.process(file_path, encoding='utf-8')
        text = byte_string.decode('utf-8', errors='ignore').strip()
        if text:
            # logger.info(f"Text extracted successfully using textract from: {os.path.basename(file_path)}")
            return text
        else:
            logger.warning(f"Textract returned empty text for: {os.path.basename(file_path)}")
            return None
    except textract.exceptions.ShellError as e:
        logger.error(f"Textract shell command failed for {os.path.basename(file_path)}: {e}. Ensure dependencies (like pdftotext, antiword) are installed.")
        return None
    except Exception as e:
        logger.error(f"Error using textract for {file_path}: {e}", exc_info=False)
        return None


def extract_text_from_file(file_path):
    """
    Extracts text from PDF or DOCX using specific libraries,
    with textract as an optional fallback.
    """
    if not os.path.exists(file_path):
        logger.error(f"File does not exist at path: {file_path}")
        return None

    _, extension = os.path.splitext(file_path.lower())
    text = None

    # logger.debug(f"Attempting to extract text from: {os.path.basename(file_path)} (type: {extension})")

    if extension == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif extension == '.docx':
        text = extract_text_from_docx(file_path)
    elif extension == '.txt': # Handle plain text files
         try:
             with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                 text = f.read()
             # logger.info(f"Read TXT file: {os.path.basename(file_path)}")
         except Exception as e:
             logger.error(f"Error reading TXT file {file_path}: {e}", exc_info=False)
             text = None
    else:
        logger.warning(f"Extension '{extension}' not directly handled by specific parsers. Trying textract.")
        text = None # Ensure textract is tried below

    # Optional: Use textract as a primary method or fallback
    if text is None:
        # logger.info(f"Specific parser failed or unsupported type for {os.path.basename(file_path)}. Falling back to textract.")
        text = extract_text_using_textract(file_path)

    if text:
        # logger.info(f"Successfully extracted text (length: {len(text)}) from {os.path.basename(file_path)}")
        pass # Reduce log noise
    else:
         logger.warning(f"Could not extract text from {os.path.basename(file_path)} using available methods.")

    return text

def read_job_description(file_path):
    """Reads job description from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Job description file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading job description {file_path}: {e}")
        return None

# Example function if JDs are in a CSV
# import pandas as pd
# def read_jd_from_csv(csv_path, row_index, column_name='description'):
#    try:
#        df = pd.read_csv(csv_path)
#        return df.loc[row_index, column_name]
#    except Exception as e:
#        logger.error(f"Error reading JD from CSV {csv_path}: {e}")
#        return None