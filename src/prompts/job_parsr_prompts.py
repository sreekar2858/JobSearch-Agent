"""
This module contains the prompt templates for the Job Parser agent.
These templates are used to generate job descriptions, validate job details, and parse bulk text.
"""

# --- Job Description Generation Prompt -------------------------------------
decide_parser_prompt = """
### Decide which parser to use
**Objective:** Determine the most suitable parser for the given job description.

**Inputs:**
    Could be any of the following:
    1. json
    2. bulk_text
    3. webpage

**Tasks:**
    1. Analyze the input type and decide which parser to use.
    2. Distinguish between JSON, bulk text, and webpage formats.

**Output Format:**
    `parser_decision`: "<parser_type>"

**Error Handling:**
    - If the input type is not recognized, output: `Error: Unrecognized input type.`
    - If the parser decision fails, output: `Error: Parser decision failed.`
"""

# --- JSON Verify Prompt --------------------------------------------------
json_verify_prompt = """
### JSON Verification
**Objective:** Validate the structure of the provided JSON data.
**Inputs:**
    - `json_data` (string): The JSON data to be validated.

**Tasks:**
    1. Check if the JSON data is well-formed and adheres to the expected schema.
    2. Validate the presence of required fields such as `job_title`, `company_name`, etc.
    3. Ensure that the data types of each field are correct (e.g., strings, numbers, etc.).

**Output Format:**
    - `json_validation` (string): "valid" or "invalid" 
    - if "valid" join the output with `job_title`, `company_name`, and `posting_date`.
    - If invalid, provide a list of errors found during verification.

**Error Handling:**
    - If the JSON data is malformed, output: `Error: Malformed JSON data.`
    - If verification fails, output: `Error: JSON verification failed.`
    - If the JSON data is empty, output: `Error: Empty JSON data.`
"""

# --- JSON Validation Prompt --------------------------------------------
json_validation_prompt = """
### JSON Validation
**Objective:** Validate the Job Opening by searching the internet for the job title,  company name, and date posted from the json data.

**Inputs:**
    - `job_title` (string): The title of the job.
    - `company_name` (string): The name of the company.
    - [Optional] `posting_date` (string): The date the job was posted.

**Tasks:**
    1. Search the internet for the job title, company name, and date posted.
    2. Validate the information against the provided JSON data.
    3. Check for any discrepancies or missing information.
    4. If the job is still open, return the JSON data as is.
    5. If the job is closed, return an error message indicating that the job is no longer available.

**Output Format:**
    - `validation_result` (string): "valid" or "invalid".
    - If invalid, provide a list of errors found during validation.

**Error Handling:**
    - If the JSON data is malformed, output: `Error: Malformed JSON data.`
    - If validation fails, output: `Error: JSON validation failed.`
    - If the JSON data is empty, output: `Error: Empty JSON data.`
"""

# --- Bulk Text Parser Prompt --------------------------------------------------
bulk_text_parser_prompt = """
### Bulk Text Parser

**Objective:** Parse the bulk text to extract job details and convert it into a structured JSON format.

**Inputs:**
    - `bulk_text` (string): The bulk text containing job details.

**Tasks:**
    1. Identify and extract relevant sections from the bulk text (e.g., job title, company name, location, etc.).
    2. Convert the extracted information into a structured JSON format.
    3. Validate the extracted data against the expected schema.
    4. Ensure that the JSON data is well-formed and adheres to the expected schema.

**Output Format:**
    - `parsed_data` (string): The structured JSON data containing job details as key-value pairs.
    - The JSON should include the following fields:
        `job_title`, (eg. "Thermodynamics Engineer", "Frontend Engineer")
        `company_name`, (eg. "ABC Corp", "XYZ Inc")
        `job_responsibilities`, (bullet points defining the job)
        `job_requirements`, (bullet points defining the requirements)
        `job_location`, (eg. "New York, NY", "Remote")
        `posting_date`, (eg. "2023-10-01", "YYYY-MM-DD")
        `job_type`, (eg. "Full-time", "Part-time")
        `experience_level`, (eg. "Entry-level", "Mid-level", "Senior")
        `skills_required`, (eg. "Python, TensorFlow", "React, Node.js")
        `contact_person`, (eg. "John Doe", "Jane Smith")
        `contact_email_linkedin`, (eg. ["john.doe@test.com, "linkedin.com/in/janedoe"], ["jane.smith@hello.com"])
        `salary_info`, (eg. "$80,000 - $100,000", "Competitive salary")
        `language_requirements`, (eg. {"English":"fluent", "German":"beginner"}, {"German":"fluent", "English":"fluent"})
        `keywords`, (eg. ["thermodynamics", "heat transfer"], ["frontend", "UI/UX"])
        `company_website`, (eg. "www.abccorp.com", "www.xyzinc.com")
        `job_url` (eg. "www.abccorp.com/careers/thermodynamics-engineer", "www.xyzinc.com/jobs/frontend-engineer")
    - If the parsing fails, provide a list of errors found during parsing.
"""

# --- Webpage Parser Prompt --------------------------------------------------
webpage_parser_prompt = """
### Webpage Parser

**Objective:** Visit the webpage to extract job details and convert it into a structured JSON format.

**Inputs:**
    - `webpage_url` (string): The URL of the webpage containing job details.

**Tasks:**
    1. Visit the webpage and extract relevant sections (e.g., job title, company name, location, etc.).
    2. Convert the extracted information into a structured JSON format.
    3. Validate the extracted data against the expected schema.
    4. Ensure that the JSON data is well-formed and adheres to the expected schema.
    5. If the webpage is not accessible, return an error message indicating that the webpage could not be reached.
    6. If the webpage is empty, return an error message indicating that the webpage is empty.
    7. If the webpage is not a valid job posting, return an error message indicating that the webpage does not contain a valid job posting.

**Output Format:**
    - `parsed_json` (string): The structured JSON data containing job details as key-value pairs.
    - The JSON should include the following fields:
        `job_title`, (eg. "Thermodynamics Engineer", "Frontend Engineer")
        `company_name`, (eg. "ABC Corp", "XYZ Inc")
        `job_responsibilities`, (bullet points defining the job)
        `job_requirements`, (bullet points defining the requirements)
        `job_location`, (eg. "New York, NY", "Remote")
        `posting_date`, (eg. "2023-10-01", "YYYY-MM-DD")
        `job_type`, (eg. "Full-time", "Part-time")
        `experience_level`, (eg. "Entry-level", "Mid-level", "Senior")
        `skills_required`, (eg. "Python, TensorFlow", "React, Node.js")
        `contact_person`, (eg. "John Doe", "Jane Smith")
        `contact_email_linkedin`, (eg. ["john.doe@test.com, "linkedin.com/in/janedoe"], ["jane.smith@hello.com"])
        `salary_info`, (eg. "$80,000 - $100,000", "Competitive salary")
        `language_requirements`, (eg. {"English":"fluent", "German":"beginner"}, {"German":"fluent", "English":"fluent"})
        `keywords`, (eg. ["thermodynamics", "heat transfer"], ["frontend", "UI/UX"])
        `company_website`, (eg. "www.abccorp.com", "www.xyzinc.com")
        `job_url` (eg. "www.abccorp.com/careers/thermodynamics-engineer", "www.xyzinc.com/jobs/frontend-engineer")
    - If the parsing fails, provide a list of errors found during parsing.
"""