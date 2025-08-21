import sqlite3
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

class JobDatabase:
    def __init__(self, db_path: str = "jobs/jobsearch.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.commit()
        self._create_table()

    def _create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT,
                source TEXT,
                scraped_at TEXT,
                job_title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                job_description TEXT,
                job_location TEXT,
                date_posted TEXT,
                job_insights TEXT,  -- JSON string
                easy_apply BOOLEAN,
                apply_info TEXT,    -- JSON string
                company_info TEXT,  -- JSON string
                hiring_team TEXT,   -- JSON string
                related_jobs TEXT,  -- JSON string
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_url, job_title, company_name)
            )        ''')
        self.conn.commit()

    def job_exists(self, source_url: str = None, job_title: str = None, company_name: str = None) -> bool:
        """Check if a job already exists in the database"""
        cur = self.conn.cursor()
        if source_url:
            cur.execute("SELECT 1 FROM jobs WHERE source_url = ?", (source_url,))
        elif job_title and company_name:
            cur.execute("SELECT 1 FROM jobs WHERE job_title = ? AND company_name = ?", (job_title, company_name))
        else:
            return False
        return cur.fetchone() is not None

    def add_job(self, job: Dict[str, Any], max_retries: int = 3) -> bool:
        """Add a job to the database with retries and better error handling"""
        # Extract required fields with multiple possible field names
        job_title = (job.get("job_title") or 
                    job.get("title") or 
                    job.get("position_title"))
        
        company_name = (job.get("company_name") or 
                       job.get("company") or 
                       job.get("company_title"))
        
        if not job_title or not company_name:
            print(f"❌ Missing required fields: job_title={job_title}, company_name={company_name}")
            return False
            
        # Check if job already exists to avoid unnecessary database operations
        source_url = (job.get("source_url") or 
                     job.get("url") or 
                     job.get("job_url") or 
                     job.get("link"))
        
        if source_url and self.job_exists(source_url=source_url):
            print(f"⏭️  Job already exists: {job_title} at {company_name}")
            return True  # Return True since the job is already in database
        elif not source_url and self.job_exists(job_title=job_title, company_name=company_name):
            print(f"⏭️  Job already exists: {job_title} at {company_name}")
            return True
            
        # Convert complex fields to JSON strings
        def to_json_str(field):
            if isinstance(field, (dict, list)):
                return json.dumps(field)
            return str(field) if field is not None else None
          
        # Extract job description from various possible field names
        job_description_parts = []
        
        # Handle job_responsibilities (could be string or list)
        responsibilities = job.get("job_responsibilities") or job.get("job_description") or job.get("about_job") or job.get("description")
        if responsibilities:
            if isinstance(responsibilities, list):
                job_description_parts.extend(responsibilities)
            else:
                job_description_parts.append(str(responsibilities))
        
        # Handle job_requirements (could be string or list)
        requirements = job.get("job_requirements") or job.get("requirements")
        if requirements:
            if isinstance(requirements, list):
                job_description_parts.append("Requirements:")
                job_description_parts.extend(requirements)
            else:
                job_description_parts.append("Requirements: " + str(requirements))
        
        # Combine all parts into a single description
        job_description = "\n".join(job_description_parts) if job_description_parts else None
        
        # Extract location from various possible field names
        job_location = (job.get("job_location") or 
                       job.get("location") or 
                       job.get("work_location"))
        
        # Extract date from various possible field names
        date_posted = (job.get("date_posted") or 
                      job.get("posted_date") or 
                      job.get("posting_date") or 
                      job.get("date"))
        
        # Retry logic for database operations
        for attempt in range(max_retries):
            try:
                # Use a transaction for consistency
                with self.conn:
                    self.conn.execute('''
                        INSERT OR IGNORE INTO jobs (
                            source_url, source, scraped_at, job_title, company_name,
                            job_description, job_location, date_posted, job_insights,
                            easy_apply, apply_info, company_info, hiring_team, related_jobs
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        source_url,
                        job.get("source", "linkedin"),
                        job.get("scraped_at") or datetime.now().isoformat(),
                        job_title,
                        company_name,
                        job_description,
                        job_location,
                        date_posted,
                        to_json_str(job.get("job_insights") or job.get("skills_required")),
                        job.get("easy_apply"),
                        to_json_str(job.get("apply_info") or {
                            "contact_person": job.get("contact_person"),
                            "contact_email": job.get("contact_email_or_linkedin"),
                            "salary_info": job.get("salary_info")
                        }),
                        to_json_str(job.get("company_info") or job.get("about_company") or {
                            "website": job.get("company_website")
                        }),
                        to_json_str(job.get("hiring_team")),
                        to_json_str(job.get("related_jobs"))
                    ))
                
                print(f"✅ Successfully added job: {job_title} at {company_name}")
                return True
                
            except sqlite3.IntegrityError as e:
                # Duplicate job - this is fine
                if "UNIQUE constraint failed" in str(e):
                    print(f"⏭️  Job already exists (duplicate detected): {job_title} at {company_name}")
                    return True
                else:
                    print(f"❌ Integrity error adding job (attempt {attempt + 1}/{max_retries}): {e}")
                    
            except sqlite3.OperationalError as e:
                # Database locked or other operational error
                print(f"⚠️  Database operational error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                    
            except Exception as e:
                print(f"❌ Unexpected error adding job (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
        
        print(f"❌ Failed to add job after {max_retries} attempts: {job_title} at {company_name}")
        return False

    def add_job_with_immediate_feedback(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Add a job and return detailed feedback about the operation"""
        start_time = time.time()
        
        job_title = (job.get("job_title") or job.get("title") or job.get("position_title"))
        company_name = (job.get("company_name") or job.get("company") or job.get("company_title"))
        
        result = {
            "success": False,
            "job_title": job_title,
            "company_name": company_name,
            "message": "",
            "duration_ms": 0,
            "action": "unknown"
        }
        
        success = self.add_job(job)
        
        result["success"] = success
        result["duration_ms"] = int((time.time() - start_time) * 1000)
        
        if success:
            if self.job_exists(job.get("source_url"), job_title, company_name):
                result["action"] = "added_to_database"
                result["message"] = f"Successfully added {job_title} at {company_name}"
            else:
                result["action"] = "already_existed"
                result["message"] = f"Job already existed: {job_title} at {company_name}"
        else:
            result["action"] = "failed"
            result["message"] = f"Failed to add {job_title} at {company_name}"
        
        return result

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific job by ID"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_jobs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all jobs with pagination"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def search_jobs(self, keyword: str = None, company: str = None, location: str = None) -> List[Dict[str, Any]]:
        """Search jobs by keyword, company, or location"""
        cur = self.conn.cursor()
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND (job_title LIKE ? OR job_description LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if company:
            query += " AND company_name LIKE ?"
            params.append(f"%{company}%")
            
        if location:
            query += " AND job_location LIKE ?"
            params.append(f"%{location}%")
        
        query += " ORDER BY created_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        cur = self.conn.cursor()
        
        # Total jobs
        cur.execute("SELECT COUNT(*) as total FROM jobs")
        total = cur.fetchone()[0]
        
        # Jobs by company
        cur.execute("SELECT company_name, COUNT(*) as count FROM jobs GROUP BY company_name ORDER BY count DESC LIMIT 10")
        top_companies = [{"company": row[0], "count": row[1]} for row in cur.fetchall()]
        
        # Jobs by source
        cur.execute("SELECT source, COUNT(*) as count FROM jobs GROUP BY source")
        by_source = [{"source": row[0], "count": row[1]} for row in cur.fetchall()]
        
        return {
            "total_jobs": total,
            "top_companies": top_companies,
            "by_source": by_source
        }

    def migrate_from_json(self, json_files: List[str]) -> int:
        """Migrate existing JSON job files to the database"""
        migrated_count = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both single job and list of jobs
                jobs = data if isinstance(data, list) else [data]
                
                for job in jobs:
                    if self.add_job(job):
                        migrated_count += 1
                        
            except Exception as e:
                print(f"Error migrating {json_file}: {e}")
        
        return migrated_count

    def close(self):
        self.conn.close()
