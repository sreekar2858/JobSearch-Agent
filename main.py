from src.agents.cv_writer import call_cv_agent
from src.agents.job_details_parser import call_job_parsr_agent
import os
import json

def slugify(text: str) -> str:
    """Create filesystem-safe folder names."""
    return "".join(c if c.isalnum() else "_" for c in text)

def process_jobs(json_path: str, output_dir: str = "output") -> None:
    """Load jobs and generate output folders for each."""
    print("📋 Loading job postings from JSON file...")
    with open(json_path, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    print(f"📊 Found {len(jobs)} job postings to process")

    for i, job in enumerate(jobs):
        # Create a folder for this job
        company = job.get('company_name', '')
        job_title = job.get('job_title', '')
        print(f"\n🔹 Processing job {i+1}/{len(jobs)}: {job_title} at {company}")
        
        folder_name = os.path.join(output_dir, slugify(f"{company}_{job_title}"))
        os.makedirs(folder_name, exist_ok=True)
        print(f"📁 Created folder: {folder_name}")
        
        # Save job details
        print(f"💾 Saving job details to {folder_name}/details.json")
        with open(os.path.join(folder_name, 'details.json'), 'w', encoding='utf-8') as detail_file:
            json.dump(job, detail_file, indent=2)
        
        # Generate custom CV using the agent
        print(f"🤖 Starting CV generation for {job_title}...")
        job_details_str = json.dumps(job)
        try:
            cv_text, state_json, cv_path = call_cv_agent(job_details_str)
            # Save the CV text
            print(f"📄 Saving CV text to {folder_name}/custom_cv.txt")
            with open(os.path.join(folder_name, 'custom_cv.txt'), 'w', encoding='utf-8') as cv_file:
                cv_file.write(cv_text)
        except Exception as e:
            print(f"❌ Error generating CV for {folder_name}: {e}")
        
        # TODO: Implement agent for cover letter generation
        # For now, Placeholder for cover letter
        print("📝 Creating cover letter placeholder...")
        cover_letter_text = f"Cover letter placeholder for {job_title} at {company}\n"
        with open(os.path.join(folder_name, 'cover_letter.txt'), 'w', encoding='utf-8') as cl_file:
            cl_file.write(cover_letter_text)
            
    print("\n✅ All jobs processed successfully!")
    print(f"📂 Output files are available in the '{output_dir}' directory")

def process_single_job(job_title: str, company: str, description: str) -> str:
    """Process a single job without saving to JSON."""
    print(f"🔹 Processing single job: {job_title} at {company}")
    
    job_info = {
        "job_title": job_title,
        "company_name": company,
        "job_description": description
    }
    
    print("🤖 Starting CV generation...")
    job_details_str = json.dumps(job_info)
    cv_text, _, cv_path = call_cv_agent(job_details_str)
    print(f"✅ CV generation complete! Document saved to: {cv_path}")
    return cv_path

def parse_job_postings(text:str=None, **kwargs) -> None:
    # Parses the job postings from the given text file by passing to the 
    input_file = kwargs.get('input_file', None)
    if input_file:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
            
    if not text:
        print("❌ No text provided for parsing. Exiting.")
        return
    
    # Run the Job Parser agent
    print("🔍 Parsing job postings...")
    job_postings = call_job_parsr_agent(text)
    
    # Save the parsed job postings to a JSON file
    output_file = kwargs.get('output_file', None)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json.loads(job_postings), f, indent=2)
        print(f"💾 Parsed job postings saved to {output_file}")
    else:
        print("❌ No output file specified. Job postings not saved.")
        print("📋 Job postings:")
        print(json.dumps(job_postings, indent=2))

if __name__ == "__main__":
    # Option 1: Process all jobs in the JSON file
    # process_jobs('jobs/job_postings.json')
    parse_job_postings(input_file='E:/Stuff/Jobs_Agent/JobSearch-Agent/jobs/job_bulk_text_1.txt', 
                       output_file='E:/Stuff/Jobs_Agent/JobSearch-Agent/jobs/job_bulk_text_1.json')
    
    # Option 2: Process a single custom job (uncomment to use)
    # custom_cv_path = process_single_job(
    #     "Principal Software Engineer", 
    #     "InnovateX", 
    #     "5+ yrs experience in cloud and microservices."
    # )
    # print(f"Generated custom CV at: {custom_cv_path}")
