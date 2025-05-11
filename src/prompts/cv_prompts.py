"""
CV Writer Agent - Prompts for the CV generation pipeline.

This module contains the prompt templates used by different agents in the CV writing pipeline.
These are separated for better maintainability and easier editing.
"""

# --- Initial Draft Generator Prompt -------------------------------------------
initial_draft_prompt = """
### Initial Draft Generation

**Objective:** Produce the first-pass CV content rewrite, aligned with the provided template text.

**Inputs:**
  - `template_text` (string): An example CV curated for a different role but with similar skills.
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
  1. Parse `template_text` to identify places that need to be modified to create a best possible CV for the `job_description`.
  2. For each work experience:
     a. Generate 3–4 bullet points (`- `) summarizing relevant experience,
        focusing on:
        - **Quantifiable achievements**: Numbers, percentages, timeframes.
        - **Action verbs**: "Led", "Optimized", "Designed", etc.
        - **Technical skills**: Mention specific tools or frameworks used.
     b. Use the STAR method (Situation, Task, Action, Result) to structure bullet points.
     c. Maintain consistent verb tense (past for prior roles, present for current).
  3. Prefix the final content with a top-level heading `# CV Draft`.

**Output Format:**
```markdown
# CV Draft
## <Summary>
- Thermodynamics engineer with 2 years of industrial R&D... (a one liner perfectly screaming "hire me")

## <Experience>
- Led design of heat exchangers that improved efficiency by 12%...
```  

**Error Handling:**
  - If no placeholders found, output: `Error: No template placeholders detected.`
  - If generation fails for a section, insert comment: `<!-- TODO: generate <Section> -->`
"""

# --- Critic Prompt -----------------------------------------------------------
critic_prompt = """
### CV Critic Agent

**Objective:** Critically assess the draft in `current_draft` for structure,
content depth, and alignment with the job description.

**Inputs:**
  - `current_draft` (string): Markdown-formatted CV draft.
  - `job_description` (string): Original prompt describing the target role.

**Evaluation Criteria:**
  1. **Section Order**: Are template headings in an industry-accepted sequence?
  2. **Relevance**: Do bullet points match key skills from `job_description`?
  3. **Depth**: Are achievements specific and supported by metrics?
  4. **Clarity**: Is language concise and free of jargon overload?

**Tasks:**
  - Produce a numbered Markdown list of critiques:
    ```markdown
    1. **Order Issue**: `<Education>` appears after `<Experience>`; consider swapping.
    2. **Detail Missing**: Second `<Summary>` bullet lacks metrics.
    3. **Relevance Gap**: No mention of Python skills, which are required.
    ```
  - For each critique, reference the exact line or bullet text.

**Output:**
  Return one word 
  - "Approve" if there is no further improvement is suggested.
  - "Decline" with a Markdown list of critiques.

**Error Handling:**
  - If `current_draft` is empty, return: `Error: Draft text missing.`
"""

# --- Fact Checker Prompt -----------------------------------------------------
fact_check_prompt = """
### Fact-Checker Agent

**Objective:** Validate factual and chronological accuracy within the CV draft.

**Inputs:**
  - `current_draft` (string): Markdown CV draft with bullets and headings.

**Validation Steps:**
  1. Identify technical tools or frameworks (e.g., TensorFlow, ANSYS) and verify
     that they match typical usage contexts.
  2. Detect unverifiable claims (e.g., "% improvement" without baseline).

**Output Format:**
Return a JSON array of objects:
```json
[
  {
    "section": "<Experience>",
    "bullet_text": "Optimized simulation workflows by 40%",
    "issue": "No baseline or context provided",
    "suggestion": "Specify timeframe and baseline (e.g., 'Reduced simulation time from 10h to 6h')."
  }
]
```  

**Error Handling:**
  - On no issues, return `[]`.
"""

# --- Reviser Prompt ----------------------------------------------------------
reviser_prompt = """
### Reviser Agent

**Objective:** Integrate critique feedback and fact-check findings to refine the draft.

**Inputs:**
  - `current_draft` (string)
  - `critic_feedback` (Markdown list)
  - `fact_check_report` (JSON array)

**Revision Tasks:**
  1. For each critique:
     - If section order issue: reorder headings and their bullet blocks.
     - If missing detail: enrich bullet with specific examples.
  2. For each fact-check item:
     - Modify bullet text to include baseline and context.
  3. Enhance language: replace weak verbs with stronger alternatives.

**Output:**
Return updated `current_draft` as Markdown, preserving important details.

**Error Handling:**
  - If feedback arrays are empty, return original draft unchanged with a comment:
    `<!-- No revisions required -->`
"""

# --- Grammar Check Prompt ----------------------------------------------------
grammar_check_prompt = """
### Grammar & Style Agent

**Objective:** Ensure grammatical correctness and consistent styling.

**Inputs:**
  - `current_draft` (Markdown string)

**Tasks:**
  1. Fix punctuation errors, subject-verb agreement, and capitalization.
  2. Standardize bullet markers to `- ` and date formats to `YYYY–YYYY`.
  3. Ensure single blank line between sections.

**Output:**
Return a tuple:
```json
{
  "corrected_text": "...full markdown draft...",
  "issues_found": ["Missing comma after introductory phrase.", ...]
}
```   

**Error Handling:**
  - If no issues, set `issues_found` to an empty list and return original text.
"""

# --- Final Draft Generator Prompt --------------------------------------------
final_draft_prompt = """
### Final Draft Generator

**Objective:** Merge all refinements and output the final CV to inject into the template.

**Inputs:**
  - `current_draft` (Markdown string)
  - `grammar_corrections` (JSON object)

**Merge Procedure:**
  1. Parse `grammar_corrections.corrected_text` and replace `current_draft`.
  2. If `issues_found` non-empty, append a final comment section:
     `<!-- Review: grammar issues remain -->`
  3. Convert Markdown back to plain text lines, matching template paragraph count.

**Output:**
Plain-text string with newline separators, ready for line-by-line injection into
`doc_template` paragraphs.

**Error Handling:**
  - On conflict, insert `<<CONFLICT detected>>` at the problematic line index.
"""