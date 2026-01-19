#!/usr/bin/env python3
"""
Document Database Demo - Shows how to use the new database storage system

This script demonstrates the new database-first approach for storing
generated CVs and cover letters instead of text files.
"""

import os
import json
from datetime import datetime
from src.utils.document_database import DocumentStorage, DocumentDatabase


def demo_document_storage():
    """Demonstrate the document storage functionality"""

    print("🚀 Document Database Storage Demo")
    print("=" * 50)

    # Sample job posting data
    sample_job = {
        "company_name": "TechCorp",
        "job_title": "Senior Python Developer",
        "job_location": "Remote",
        "job_description": "We are looking for an experienced Python developer...",
        "requirements": ["Python", "FastAPI", "PostgreSQL"],
        "salary_info": "$120,000 - $150,000",
    }

    # Sample generated content
    sample_cv = """
JOHN DOE
Senior Python Developer

EXPERIENCE:
• 5+ years developing Python applications
• Expert in FastAPI, Django, and Flask
• Strong database skills with PostgreSQL
• Experience with cloud platforms (AWS, Azure)

SKILLS:
• Python, JavaScript, SQL
• Docker, Kubernetes, CI/CD
• RESTful APIs, Microservices
"""

    sample_cover_letter = """
Dear Hiring Manager,

I am writing to express my strong interest in the Senior Python Developer position at TechCorp. With over 5 years of experience in Python development and a proven track record of building scalable web applications, I am confident I would be a valuable addition to your team.

My expertise includes:
- Advanced Python development with FastAPI and Django
- Database design and optimization with PostgreSQL
- Cloud deployment and containerization with Docker

I am excited about the opportunity to contribute to TechCorp's innovative projects and would welcome the chance to discuss how my skills align with your team's needs.

Best regards,
John Doe
"""

    process_id = f"demo_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"📝 Process ID: {process_id}")
    print()

    # Store CV in database
    print("💾 Storing CV in database...")
    cv_id = DocumentStorage.store_cv(
        content=sample_cv,
        job_posting=sample_job,
        process_id=process_id,
        state_json='{"version": "1.0", "agent": "demo"}',
        template_used="professional_cv.txt",
    )
    print(f"✅ CV stored with ID: {cv_id}")
    print()

    # Store cover letter in database
    print("💾 Storing Cover Letter in database...")
    cl_id = DocumentStorage.store_cover_letter(
        content=sample_cover_letter,
        job_posting=sample_job,
        process_id=process_id,
        state_json='{"version": "1.0", "agent": "demo"}',
        template_used="professional_cover_letter.txt",
    )
    print(f"✅ Cover Letter stored with ID: {cl_id}")
    print()

    # Retrieve documents by process
    print("🔍 Retrieving documents by process...")
    process_docs = DocumentStorage.get_documents_for_process(process_id)

    print(
        f"📊 Found {len(process_docs['all_documents'])} documents for process {process_id}"
    )
    if process_docs["cv"]:
        print(
            f"   📄 CV: ID {process_docs['cv']['id']} - {process_docs['cv']['company_name']}"
        )
    if process_docs["cover_letter"]:
        print(
            f"   📄 Cover Letter: ID {process_docs['cover_letter']['id']} - {process_docs['cover_letter']['company_name']}"
        )
    print()

    # Show database statistics
    print("📈 Database Statistics:")
    db = DocumentDatabase()
    try:
        stats = db.get_document_stats()
        print(f"   Total Documents: {stats['total_documents']}")
        print(f"   Total Processes: {stats['total_processes']}")
        print(f"   By Type: {stats['by_type']}")

        if stats["by_company"]:
            print("   Top Companies:")
            for company in stats["by_company"][:3]:
                print(f"     - {company['company']}: {company['count']} documents")
    finally:
        db.close()
    print()

    # Export to files for backward compatibility
    print("📁 Exporting to files for backward compatibility...")
    exported_files = DocumentStorage.export_process_documents_to_files(
        process_id, "output/demo"
    )

    for doc_type, filepath in exported_files.items():
        print(f"   💾 {doc_type.upper()}: {filepath}")
    print()

    print("✅ Demo completed successfully!")
    print()
    print("🎯 Key Benefits of Database Storage:")
    print("   • Searchable and queryable document history")
    print("   • Version tracking and revision history")
    print("   • Better organization and metadata")
    print("   • Faster retrieval and filtering")
    print("   • Still compatible with file exports when needed")


def show_recent_documents():
    """Show recent documents in the database"""

    print("\n📚 Recent Documents in Database")
    print("=" * 40)

    db = DocumentDatabase()
    try:
        # Get recent CVs
        recent_cvs = db.get_recent_documents(document_type="CV", limit=5)
        print(f"\n📄 Recent CVs ({len(recent_cvs)}):")
        for cv in recent_cvs:
            created = cv["created_at"][:19]  # Remove microseconds
            print(
                f"   • ID {cv['id']}: {cv['company_name']} - {cv['job_title']} ({created})"
            )

        # Get recent cover letters
        recent_cls = db.get_recent_documents(document_type="COVER_LETTER", limit=5)
        print(f"\n📝 Recent Cover Letters ({len(recent_cls)}):")
        for cl in recent_cls:
            created = cl["created_at"][:19]  # Remove microseconds
            print(
                f"   • ID {cl['id']}: {cl['company_name']} - {cl['job_title']} ({created})"
            )

    finally:
        db.close()


def search_documents_demo():
    """Demonstrate document search functionality"""

    print("\n🔍 Document Search Demo")
    print("=" * 30)

    db = DocumentDatabase()
    try:
        # Search by keyword
        print("\n🔍 Searching for 'Python' documents:")
        python_docs = db.search_documents(keyword="Python")
        for doc in python_docs[:3]:  # Show first 3
            print(
                f"   • {doc['document_type']}: {doc['company_name']} - {doc['job_title']}"
            )

        # Search by company
        print("\n🔍 Searching for 'TechCorp' documents:")
        techcorp_docs = db.search_documents(company="TechCorp")
        for doc in techcorp_docs:
            print(f"   • {doc['document_type']}: {doc['job_title']} (ID: {doc['id']})")

    finally:
        db.close()


if __name__ == "__main__":
    try:
        # Run the main demo
        demo_document_storage()

        # Show recent documents
        show_recent_documents()

        # Demonstrate search
        search_documents_demo()

        print("\n🎉 All demos completed successfully!")
        print("\n💡 Next Steps:")
        print("   1. The main API now stores documents in database by default")
        print("   2. Access documents via new API endpoints:")
        print("      - GET /documents - List recent documents")
        print("      - GET /documents/search - Search documents")
        print("      - GET /process/{process_id}/documents - Get documents for process")
        print("      - GET /documents/stats - Get database statistics")
        print("   3. Files are still created for backward compatibility")

    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback

        traceback.print_exc()
