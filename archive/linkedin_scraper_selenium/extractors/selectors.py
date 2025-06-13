"""
Shared CSS/XPath selectors as constants for LinkedIn job extraction.
"""

# Job card selectors
JOB_CARD_SELECTORS = [
    "li[data-occludable-job-id]",
    "li.jobs-search-results__list-item",
    "li.scaffold-layout__list-item",
    ".job-card-container",
    "[data-job-id]",
]

# Job link selectors
JOB_LINK_SELECTORS = [
    "a.job-card-container__link",
    "a[href*='/jobs/view/']",
    "a[data-control-id]",
    "a.job-card-list__title-link",
    "a.job-card-list__title--link",
]

# Job title selectors
JOB_TITLE_SELECTORS = [
    ".jobs-unified-top-card__job-title",
    ".job-details-jobs-unified-top-card__job-title",
    "h1.jobs-unified-top-card__job-title",
    "h1[data-test-job-title]",
    "h1[data-test-job-card-title]",
    "h1.t-24",
    "h1",
    ".job-card-container__title",
    ".job-title",
]

# Company name selectors
COMPANY_NAME_SELECTORS = [
    ".jobs-unified-top-card__company-name",
    ".job-details-jobs-unified-top-card__company-name",
    "a.jobs-unified-top-card__company-name",
    "[data-test-job-company-name]",
    ".jobs-details__top-card-company-url",
    ".jobs-details__top-card-company-name",
    ".job-card-container__company-name",
    ".artdeco-entity-lockup__subtitle",
    ".company-name",
]

# Location selectors
LOCATION_SELECTORS = [
    ".jobs-unified-top-card__bullet",
    ".job-details-jobs-unified-top-card__bullet",
    ".jobs-unified-top-card__workplace-type",
    "[data-test-job-location]",
    ".job-card-container__location",
    ".location",
]

# Posted date selectors
POSTED_DATE_SELECTORS = [
    ".jobs-unified-top-card__posted-date",
    ".jobs-details-job-summary__text--ellipsis",
    "[data-test-job-posted-date]",
    ".job-card-container__posted-date",
    ".posted-date",
]

# Job description selectors
JOB_DESCRIPTION_SELECTORS = [
    ".jobs-description",
    ".jobs-description-content",
    "#job-details",
    ".jobs-box__html-content",
    "[data-test-job-description]",
]

# Article selectors for full description
ARTICLE_SELECTORS = [
    "article.jobs-description__container",
    "article.jobs-description__container--condensed",
    ".jobs-description__container",
    "article[class*='jobs-description__container']",
]

# Job description content selectors
DESCRIPTION_CONTENT_SELECTORS = [
    ".jobs-description__content.jobs-description-content",
    ".jobs-description__content",
    ".jobs-description-content",
    ".jobs-box__html-content",
    "div.jobs-box__html-content.jobs-description-content__text--stretch",
    "[data-test-job-description]",
    "div.jobs-box__html-content",
]

# See more button selectors
SEE_MORE_BUTTON_SELECTORS = [
    "button.jobs-description__footer-button",
    "button[aria-label*='see more']",
    "button[aria-label*='Click to see more description']",
    ".jobs-description__footer-button",
    "button.artdeco-button--tertiary:contains('See more')",
    "button[class*='jobs-description__footer-button']",
    "button.artdeco-button.artdeco-button--tertiary.artdeco-button--fluid",
]

# Company logo selectors
COMPANY_LOGO_SELECTORS = [
    ".jobs-details-top-card__company-logo",
    ".jobs-unified-top-card__company-logo",
    ".jobs-details__top-card-company-logo",
    ".artdeco-entity-image",
    ".artdeco-entity-lockup__image img",
    ".ivm-view-attr__img--centered",
]

# Apply button selectors
APPLY_BUTTON_SELECTORS = [
    "button",
    "a[role='button']",
    "[role='link']",
    ".jobs-apply-button",
    "#jobs-apply-button-id",
    ".jobs-s-apply button",
    ".jobs-s-apply .jobs-apply-button",
    "button[aria-label*='Apply']",
]

# Skills selectors
SKILLS_SELECTORS = [
    ".job-details-jobs-unified-top-card__job-insight-text-button",
    ".job-details-jobs-unified-top-card__job-insight button",
    ".jobs-unified-top-card__job-insight-text-button",
    "button[aria-label*='Skills']",
    "button[data-tracking-control-name*='skills']",
]

# Job insights selectors
JOB_INSIGHTS_SELECTORS = [
    "li.job-details-jobs-unified-top-card__job-insight",
    ".job-details-jobs-unified-top-card__job-insight",
    ".jobs-unified-top-card__job-insight",
    ".job-details-jobs-unified-top-card__insights li",
    "li.job-details-jobs-unified-top-card__job-insight--highlight",
]

# Applicant count selectors
APPLICANT_COUNT_SELECTORS = [
    ".jobs-unified-top-card__applicant-count",
    ".jobs-details-top-card__applicant-count",
    "[data-test-applicant-count]",
    ".jobs-details__top-card-applicant-count",
    ".jobs-unified-top-card__subtitle-secondary-grouping span[class*='applicant']",
]

# Contact info selectors
CONTACT_INFO_SELECTORS = [
    ".jobs-unified-top-card__job-insight--recruiter",
    ".jobs-details-top-card__job-posting-recruiter",
    ".jobs-poster__details",
]

# Company info selectors
COMPANY_INFO_SELECTORS = [
    ".jobs-company__box",
    ".jobs-company__content",
    ".jobs-company-information",
]

# Company website selectors
COMPANY_WEBSITE_SELECTORS = [
    ".jobs-company__box a[href*='http']",
    ".jobs-company__content a[href*='http']",
    ".jobs-company-information a[href*='http']",
]

# Tertiary description container selectors
TERTIARY_DESCRIPTION_SELECTORS = [
    ".job-details-jobs-unified-top-card__primary-description-container .job-details-jobs-unified-top-card__tertiary-description-container",
    ".job-details-jobs-unified-top-card__tertiary-description-container",
    ".jobs-unified-top-card__tertiary-description-container",
]

# Text span selectors for metadata
TEXT_SPAN_SELECTORS = [
    ".tvm__text.tvm__text--low-emphasis",
    ".tvm__text",
    "span.tvm__text--low-emphasis",
    "span",
]

# Hiring team selectors
HIRING_TEAM_SECTION_SELECTORS = [
    ".job-details-people-who-can-help__section",
    ".jobs-poster",
    ".jobs-poster__details",
    ".hirer-card",
]

HIRING_MEMBER_SELECTORS = [
    ".hirer-card__hirer-information",
    ".jobs-poster__name",
    ".display-flex.align-items-center",
]

HIRING_NAME_SELECTORS = [
    ".jobs-poster__name",
    ".t-black.jobs-poster__name",
    "strong",
    ".text-body-medium-bold strong",
]

HIRING_TITLE_SELECTORS = [
    ".text-body-small.t-black",
    ".hirer-card__job-poster",
    ".jobs-poster__title",
]

# Related jobs selectors
RELATED_JOBS_SECTION_SELECTORS = [
    "ul.card-list.card-list--tile.js-similar-jobs-list",
    ".js-similar-jobs-list",
    ".similar-jobs",
    ".jobs-similar-jobs",
]

RELATED_JOB_CARD_SELECTORS = [
    "li.list-style-none",
    ".job-card-job-posting-card-wrapper",
    ".job-card",
]

RELATED_JOB_TITLE_SELECTORS = [
    ".artdeco-entity-lockup__title strong",
    ".job-card-job-posting-card-wrapper__title strong",
    ".job-card__title",
]

RELATED_JOB_COMPANY_SELECTORS = [
    ".artdeco-entity-lockup__subtitle",
    ".job-card__company-name",
    ".job-card-job-posting-card-wrapper__company",
]

RELATED_JOB_LOCATION_SELECTORS = [
    ".artdeco-entity-lockup__caption",
    ".job-card__location",
    ".job-card-job-posting-card-wrapper__location",
]

RELATED_JOB_DATE_SELECTORS = [
    "time",
    ".job-card__date",
    ".job-card-job-posting-card-wrapper__footer-item time",
]

RELATED_JOB_INSIGHT_SELECTORS = [
    ".job-card-job-posting-card-wrapper__job-insight-text",
    ".job-card__insight",
    ".job-card-job-posting-card-wrapper__footer-item",
]

# Pagination selectors
PAGINATION_STATE_SELECTORS = [
    ".jobs-search-pagination__page-state",
    ".jobs-search-results-list__pagination .jobs-search-pagination__page-state",
    "p.jobs-search-pagination__page-state",
]

NEXT_BUTTON_SELECTORS = [
    "button.jobs-search-pagination__button--next",
    ".jobs-search-pagination__button--next",
    "button[aria-label='View next page']",
    "button.artdeco-button.jobs-search-pagination__button--next",
    ".jobs-search-pagination button[aria-label*='next']",
    "button[aria-label='Next']",
    ".artdeco-pagination__button--next",
    "button.artdeco-pagination__button--next",
    "[data-test-pagination-page-btn='next']",
]

PAGE_BUTTON_SELECTORS = [
    ".jobs-search-pagination__indicator-button",
    ".jobs-search-pagination__pages .jobs-search-pagination__indicator button",
]
