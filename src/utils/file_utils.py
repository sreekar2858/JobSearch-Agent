"""
File utility functions for the Job Findr Agent.

This module provides utilities for:
- Loading and parsing configuration files (YAML)
- Working with Word document templates
- Environment variable handling
"""
import os
import dotenv
import yaml
from typing import List, Tuple
from docx import Document
from typing import Union

def load_config(config_path: str) -> dict:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing the parsed configuration
    """
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config

def load_and_check_env() -> None:
    """
    Load environment variables from .env file and check API keys.
    
    Verifies presence of critical API keys and prints status.
    """
    # Load environment variables from .env file
    dotenv.load_dotenv()
    # --- Verify Keys for Multiple LLMs ---
    required_keys = {
        "Google": "GOOGLE_API_KEY",
        "GPT_4O": "GPT_4O_API",
        "GPT_4_1": "GPT_4_1_API",
    }

    print("Verifying API Keys from .env file:")
    missing_keys = []

    for service, key in required_keys.items():
        api_key = os.environ.get(key)
        if api_key and "api" not in api_key.lower():
            print(f"✅ {service}: Successfully verified {key}")
        else:
            print(f"❌ {service}: Missing or invalid {key}")
            missing_keys.append(service)

    if missing_keys:
        print("\n⚠️ Warning: The following API keys are missing or invalid:")
        for service in missing_keys:
            print(f" - {service}")
        print("Please update your .env file with the correct keys.")
    else:
        print("\n🎉 All required API keys are set and valid.")

    # Configure ADK to use API keys directly (not Vertex AI for this multi-model setup)
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

def load_instruction_from_file(
    filename: str, default_instruction: str = "Default instruction."
) -> str:
    """
    Read instruction text from a file.
    
    Args:
        filename: Path to the instruction text file
        default_instruction: Text to use if file loading fails
        
    Returns:
        Contents of the instruction file, or the default if file not found
    """
    instruction = default_instruction

    try:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        instruction = open(filepath, "r", encoding="utf-8").read()
        print(f"Successfully loaded instruction from {filename}")

    except FileNotFoundError:
        print(f"WARNING: Instruction file not found: {filepath}. Using default.")

    except Exception as e:
        print(f"ERROR loading instruction file {filepath}: {e}. Using default.")

    return instruction

def load_docx_template(path: str) -> Tuple[Document, str]:
    """
    Load and parse a .docx template.

    Args:
      path (str): Filesystem path to the .docx file.

    Returns:
      doc (Document): python-docx Document object for in-place editing.
      joined_text (str): All non-empty paragraph texts joined by newline,
                         used as context in LLM prompts.

    Raises:
      FileNotFoundError: If template file is missing.
      ValueError: If template contains no text paragraphs.
    """
    try:
        doc = Document(path)
    except Exception as e:
        print(f"Failed to open template: {e}")
        raise FileNotFoundError(f"Template not found: {path}")

    paragraphs: List[str] = [p.text for p in doc.paragraphs if p.text.strip()]
    if not paragraphs:
        raise ValueError("Template contains no text paragraphs.")

    joined_text = "\n".join(paragraphs)
    return doc, joined_text

def ensure_dir_exists(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: The path to the directory to ensure exists
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def load_text_file(file_path: str, readlines: bool=False) -> Union[str, List[str]]:
    """
    Load text from a file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Contents of the text file in a string or list of lines if readlines is True
    
    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if readlines:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
        


