# JobSearch Agent - TODO & Roadmap

## ✅ Recently Completed

### Pipeline Architecture (v2.1.0)
- ✅ Unified job search pipeline consolidation
- ✅ Eliminated code duplication between sync/async versions
- ✅ Single source of truth for job search operations
- ✅ Maintained backward compatibility
- ✅ Enhanced documentation for unified architecture

## 🔄 Current Priorities

### AGENT
- Extract the messages of intermediate agents from outside the _run_async_impl function
- Add a test to check that the messages are correctly extracted

### SCRAPER (LINKEDIN)
- Resolve duplicate date fields (date_posted vs posted_date)
- Implement concurrent scraping for better performance
- Enhanced data extraction:
  - Skills extraction
  - ✅ source
  - ✅ scraped_at
  - ✅ job_title
  - ✅ company_name
  - ✅ url
  - ✅ location
  - ✅ date_posted
  - ✅ job_type
  - ✅ job_level
  - ✅ easy_apply
  - ✅ about_job
  - ✅ about_company
  - ✅ related_jobs
  - Contact details extraction

## 🚀 Future Enhancements

### Pipeline & Architecture
- Performance optimization for large job datasets
- Multi-site scraping coordination (Indeed, Glassdoor)
- Advanced filtering and ranking algorithms
- Machine learning job recommendation engine

### Integration
- Enhanced WebSocket real-time features  
- Mobile app API endpoints
- Third-party service integrations
- Advanced analytics and reporting

### Developer Experience
- Enhanced testing framework
- Documentation automation
- CI/CD pipeline improvements
- Performance monitoring tools
