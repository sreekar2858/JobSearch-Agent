"""
Cover Letter Writer Agent - Prompts for the cover letter generation pipeline.

This module contains the prompt templates used by different agents in the cover letter writing pipeline.
These are separated for better maintainability and easier editing.
"""

# --- Initial Draft Generator Prompt -------------------------------------------
initial_draft_prompt = """
### Initial Cover Letter Draft Generation

**Objective:** Produce a personalized cover letter that highlights the candidate's qualifications for the specific job.

**Inputs:**
  - `template_text` (string): An example cover letter template with placeholders.
  - `job_description` (string): A detailed description of the job with keys like 
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

**Tasks:**
  1. Parse `template_text` to identify placeholders that need to be filled.
  2. Create a compelling introduction that mentions the job title and company name.
  3. Craft a middle section with 2-3 paragraphs that:
     a. Highlight the candidate's most relevant skills and experiences for this role.
     b. Incorporate keywords from the job description without direct copying.
     c. Demonstrate understanding of the company's needs and how the candidate can add value.
  4. Construct a strong closing paragraph that:
     a. Expresses enthusiasm for the opportunity.
     b. Includes a call to action (interview request).
     c. Provides contact information if appropriate.
  5. Prefix the final content with a top-level heading `# Cover Letter Draft`.

**Output Format:**
```markdown
# Cover Letter Draft

[Current Date]

[Contact Person's Name]
[Company Name]
[Company Address if available]

Dear [Contact Person's Name/Hiring Manager],

[Introduction paragraph mentioning the job position and company, showing enthusiasm]

[Middle paragraph(s) highlighting relevant skills and experiences]

[Closing paragraph with call to action]

Sincerely,
[Candidate's Name]
[Contact Information]
```  

**Error Handling:**
  - If no contact person found, use "Hiring Manager" instead.
  - If generation fails for a section, insert comment: `<!-- TODO: generate <Section> -->`
"""

# --- Critic Prompt -----------------------------------------------------------
critic_prompt = """
### Cover Letter Critic Agent

**Objective:** Critically assess the draft in `current_draft` for persuasiveness, relevance, 
and alignment with the specific job description.

**Inputs:**
  - `current_draft` (string): Markdown-formatted cover letter draft.
  - `job_description` (string): Original prompt describing the target role.

**Evaluation Criteria:**
  1. **Personalization**: Is the letter tailored to this specific company and role?
  2. **Relevance**: Does it focus on the most important skills and requirements from the job description?
  3. **Enthusiasm**: Does it convey genuine interest in the role and company?
  4. **Conciseness**: Is it appropriately brief (1 page maximum) while covering key points?
  5. **Professionalism**: Is the tone appropriate for the industry and role?

**Tasks:**
  - Produce a numbered Markdown list of critiques:
    ```markdown
    1. **Personalization Issue**: No mention of why the candidate wants to work at [Company Name] specifically.
    2. **Relevance Gap**: The letter focuses on project management but the job requires strong technical skills.
    3. **Enthusiasm**: The language feels generic; add specific reasons for interest in this role.
    ```
  - For each critique, reference the exact paragraph or sentence text.

**Output:**
  Return one word 
  - "Approve" if there is no further improvement suggested.
  - "Decline" with a Markdown list of critiques.

**Error Handling:**
  - If `current_draft` is empty, return: `Error: Draft text missing.`
"""

# --- Fact Checker Prompt -----------------------------------------------------
fact_check_prompt = """
### Fact-Checker Agent for Cover Letter

**Objective:** Validate factual accuracy and claims within the cover letter draft.

**Inputs:**
  - `current_draft` (string): Markdown cover letter draft with paragraphs and headings.

**Validation Steps:**
  1. Identify specific claims about skills, experiences, or achievements.
  2. Flag any overpromises or unverifiable claims.
  3. Verify that company information (name, address, website) is correctly formatted.
  4. Check that industry-specific terminology is used appropriately.

**Output Format:**
Return a JSON array of objects:
```json
[
  {
    "paragraph": "Introduction",
    "text": "I have 10+ years of experience in cloud architecture",
    "issue": "Specific quantification that might need verification",
    "suggestion": "If uncertain about exact duration, consider 'extensive experience in cloud architecture'"
  }
]
```  

**Error Handling:**
  - On no issues, return `[]`.
"""

# --- Reviser Prompt ----------------------------------------------------------
reviser_prompt = """
### Cover Letter Reviser Agent

**Objective:** Integrate critique feedback and fact-check findings to strengthen the cover letter.

**Inputs:**
  - `current_draft` (string)
  - `critic_feedback` (Markdown list)
  - `fact_check_report` (JSON array)

**Revision Tasks:**
  1. For each critique:
     - If personalization needed: Add specific details about the company or role.
     - If relevance issue: Refocus content to match job requirements better.
     - If enthusiasm lacking: Inject more specific reasons for interest in the role.
  2. For each fact-check item:
     - Modify claims to be more accurate or verifiable.
     - Adjust language to be more confident where appropriate.
  3. Enhance language: Replace generic statements with more specific, impactful phrasing.

**Output:**
Return updated `current_draft` as Markdown, preserving the core structure.

**Error Handling:**
  - If feedback arrays are empty, return original draft unchanged with a comment:
    `<!-- No revisions required -->`
"""

# --- Grammar Check Prompt ----------------------------------------------------
grammar_check_prompt = """
### Grammar & Style Agent for Cover Letter

**Objective:** Ensure grammatical correctness, professional tone, and consistent styling.

**Inputs:**
  - `current_draft` (Markdown string)

**Tasks:**
  1. Fix punctuation errors, subject-verb agreement, and capitalization.
  2. Check for proper paragraph breaks and spacing.
  3. Ensure the letter follows a consistent format and tone.
  4. Verify proper salutation and closing formats.
  5. Check for appropriate formal business letter style.

**Output:**
Return a tuple:
```json
{
  "corrected_text": "...full markdown draft...",
  "issues_found": ["Missing comma in greeting.", "Inconsistent spacing between paragraphs.", ...]
}
```   

**Error Handling:**
  - If no issues, set `issues_found` to an empty list and return original text.
"""

# --- Final Draft Generator Prompt --------------------------------------------
final_draft_prompt = """
### Final Cover Letter Draft Generator

**Objective:** Merge all refinements and output the final cover letter ready for submission.

**Inputs:**
  - `current_draft` (Markdown string)
  - `grammar_corrections` (JSON object)

**Merge Procedure:**
  1. Parse `grammar_corrections.corrected_text` and replace `current_draft`.
  2. If `issues_found` non-empty, append a final comment section:
     `<!-- Review: grammar issues remain -->`
  3. Format the letter appropriately for business correspondence.
  4. Convert Markdown to plain text lines, matching template format.

**Output:**
Plain-text string with newline separators, ready for line-by-line injection into
`doc_template` paragraphs.

**Error Handling:**
  - On conflict, insert `<<CONFLICT detected>>` at the problematic line index.
"""
