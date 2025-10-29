Scenario 1: Application Crash Troubleshooting

Original Prompt:

text
My app crashes when I click the submit button

Analysis JSON:

json
{
  "analysis": {
    "currentState": "User reports a crash on specific action but lacks critical diagnostic information. The prompt identifies the trigger (submit button click) but provides no technical context, error details, or environment information needed for effective troubleshooting.",
    "criticalIssues": [
      "No application type or technology stack specified",
      "Missing error messages or crash logs",
      "Environment details not provided (OS, browser, device)",
      "No information about when the issue started",
      "Recent changes or updates not mentioned",
      "Reproducibility not confirmed",
      "No description of expected vs actual behavior"
    ],
    "strengths": [
      "Specific trigger identified (submit button click)",
      "User can reproduce the issue on demand"
    ],
    "estimatedCompletenessScore": 20
  },
  
  "improvementAreas": [
    {
      "category": "Technical Environment",
      "priority": "critical",
      "issues": [
        "Application type unknown (web, mobile, desktop)",
        "Technology stack not specified",
        "Operating system and version missing",
        "Browser/runtime environment unclear"
      ]
    },
    {
      "category": "Error Details",
      "priority": "critical",
      "issues": [
        "No error message or crash report provided",
        "Stack trace not included",
        "Console logs missing",
        "Crash type unclear (freeze, close, error page)"
      ]
    },
    {
      "category": "Reproduction Context",
      "priority": "high",
      "issues": [
        "Consistent reproducibility not confirmed",
        "Steps to reproduce incomplete",
        "Data/input that triggers crash not specified",
        "Timeline of when issue started missing"
      ]
    },
    {
      "category": "Attempted Solutions",
      "priority": "medium",
      "issues": [
        "No troubleshooting steps mentioned",
        "Recent changes not documented"
      ]
    }
  ],
  
  "questions": [
    {
      "id": "q1",
      "question": "What type of application is crashing?",
      "purpose": "Identify platform-specific troubleshooting approaches",
      "category": "application_type",
      "required": true,
      "suggestedAnswers": [
        "Web application (accessed through browser)",
        "Desktop application (Windows/Mac/Linux)",
        "Mobile app (iOS/Android)",
        "Progressive Web App (PWA)"
      ]
    },
    {
      "id": "q2",
      "question": "What exactly happens when it crashes?",
      "purpose": "Understand the crash behavior and severity",
      "category": "crash_behavior",
      "required": true,
      "suggestedAnswers": [
        "App closes/terminates completely",
        "Page freezes and becomes unresponsive",
        "Error message appears (specify the exact message)",
        "Page goes blank/white screen",
        "Browser tab crashes",
        "Redirects to error page"
      ]
    },
    {
      "id": "q3",
      "question": "Can you reproduce this crash every time you click submit?",
      "purpose": "Determine if issue is consistent or intermittent",
      "category": "reproducibility",
      "required": true,
      "suggestedAnswers": [
        "Yes, happens every single time",
        "Happens most of the time (70-90%)",
        "Sometimes happens (less than 50%)",
        "Only happened once or twice",
        "Not sure - haven't tested multiple times"
      ]
    },
    {
      "id": "q4",
      "question": "What error message or code do you see (if any)?",
      "purpose": "Get specific error details for diagnosis",
      "category": "error_details",
      "required": true,
      "suggestedAnswers": [
        "Copy and paste the exact error message",
        "Error code (e.g., ERR_CONNECTION_REFUSED, 500 error)",
        "Console error (open browser DevTools > Console)",
        "No error message shown - just crashes",
        "Don't know how to find error message"
      ],
      "followUp": "If web app: Can you open browser DevTools (F12), go to Console tab, click submit, and share any red error messages?"
    },
    {
      "id": "q5",
      "question": "What are you submitting when the crash happens?",
      "purpose": "Identify if specific data/input triggers the crash",
      "category": "input_context",
      "required": true,
      "suggestedAnswers": [
        "A form with text fields (describe fields)",
        "File upload (specify file type and size)",
        "Large amount of data",
        "Special characters or specific values",
        "Empty/default form",
        "Not sure if it matters"
      ]
    },
    {
      "id": "q6",
      "question": "What is your technical environment?",
      "purpose": "Identify environment-specific issues",
      "category": "environment",
      "required": true,
      "suggestedAnswers": [
        "Browser and version (Chrome 118, Firefox 120, Safari 17, etc.)",
        "Operating System (Windows 11, macOS Sonoma, Ubuntu 22.04)",
        "Device type (Desktop, laptop, tablet, phone)",
        "Mobile: Device model and OS version"
      ]
    },
    {
      "id": "q7",
      "question": "When did this problem start?",
      "purpose": "Correlate with potential triggering events",
      "category": "timeline",
      "required": true,
      "suggestedAnswers": [
        "Just started today",
        "Started this week",
        "Has been happening for a while",
        "Immediately after an update/change",
        "Always been broken since I started using it"
      ]
    },
    {
      "id": "q8",
      "question": "Did anything change before the crash started happening?",
      "purpose": "Identify root cause through recent changes",
      "category": "recent_changes",
      "required": true,
      "suggestedAnswers": [
        "App/website was updated",
        "Updated my browser or OS",
        "Installed new browser extensions",
        "Changed network/WiFi",
        "Nothing changed that I'm aware of"
      ]
    },
    {
      "id": "q9",
      "question": "Does this happen on other devices or browsers?",
      "purpose": "Determine if issue is device/browser-specific or widespread",
      "category": "cross_platform",
      "required": false,
      "suggestedAnswers": [
        "Yes, tested on multiple devices - same issue",
        "Only happens on this device/browser",
        "Haven't tested on other devices yet",
        "Works fine on my phone but not computer (or vice versa)"
      ]
    },
    {
      "id": "q10",
      "question": "What troubleshooting have you already tried?",
      "purpose": "Avoid suggesting already-attempted solutions",
      "category": "attempted_solutions",
      "required": false,
      "suggestedAnswers": [
        "Cleared browser cache and cookies",
        "Tried different browser",
        "Restarted device",
        "Disabled browser extensions",
        "Checked internet connection",
        "Reinstalled the app",
        "Nothing yet - not sure where to start"
      ]
    }
  ],
  
  "blueprint": {
    "refinementStrategy": "Transform basic crash report into comprehensive troubleshooting request with diagnostic information, error details, and environmental context",
    "requiredInformation": [
      "Application type and technology stack",
      "Exact crash behavior and error messages",
      "Reproducibility and steps to reproduce",
      "Input/data being submitted",
      "Technical environment (OS, browser, device)",
      "Timeline and recent changes",
      "Cross-platform testing results",
      "Prior troubleshooting attempts"
    ],
    "plannedStructure": {
      "sections": [
        "Problem summary (what crashes, when, how often)",
        "Application details (type, platform, version)",
        "Exact error details (messages, codes, logs)",
        "Reproduction steps (consistent trigger, input data)",
        "Technical environment (OS, browser, device specs)",
        "Timeline and context (when started, what changed)",
        "Scope testing (other devices/browsers affected)",
        "Prior troubleshooting attempts",
        "Expected vs actual behavior",
        "Urgency and impact (blocking work, critical function)"
      ]
    },
    "expectedOutputFormat": "Detailed crash troubleshooting request with all diagnostic information for effective debugging",
    "estimatedTokensNeeded": 400
  }
}




-----

Scenario 2: Excel Automation with Python

Original Prompt:

text
Write Python code to automate Excel

Analysis JSON:

json
{
  "analysis": {
    "currentState": "Vague automation request without specifying what Excel tasks need automation. 'Automate Excel' could mean reading, writing, formatting, calculating, charting, or dozens of other operations. No information about data structure, desired operations, or business logic.",
    "criticalIssues": [
      "Specific Excel operations not defined",
      "Input data format and structure unknown",
      "Desired output not specified",
      "Business logic and calculations not described",
      "Excel file structure unclear (sheets, columns, ranges)",
      "Library preference not stated (openpyxl, pandas, xlwings, etc.)",
      "Automation trigger and workflow unknown"
    ],
    "strengths": [
      "Language specified (Python)",
      "General task identified (Excel automation)"
    ],
    "estimatedCompletenessScore": 18
  },
  
  "improvementAreas": [
    {
      "category": "Task Definition",
      "priority": "critical",
      "issues": [
        "Specific Excel operations undefined",
        "Business logic not described",
        "Input and output not specified",
        "Automation workflow unclear"
      ]
    },
    {
      "category": "Data Context",
      "priority": "critical",
      "issues": [
        "Excel file structure unknown",
        "Data types and formats not specified",
        "Volume of data not mentioned",
        "Relationships between sheets/data unclear"
      ]
    },
    {
      "category": "Technical Requirements",
      "priority": "high",
      "issues": [
        "Library/framework preference not stated",
        "Python version not specified",
        "Error handling requirements unclear",
        "Performance needs unknown"
      ]
    }
  ],
  
  "questions": [
    {
      "id": "q1",
      "question": "What specific Excel tasks do you want to automate?",
      "purpose": "Define the core automation operations",
      "category": "task_type",
      "required": true,
      "suggestedAnswers": [
        "Read data from Excel file(s)",
        "Write/export data to Excel",
        "Update existing Excel files",
        "Perform calculations on data",
        "Create charts/visualizations",
        "Format cells (colors, fonts, borders)",
        "Merge/combine multiple Excel files",
        "Filter and sort data",
        "Create pivot tables or summary reports",
        "Validate data and flag errors",
        "Multiple operations (describe workflow)"
      ]
    },
    {
      "id": "q2",
      "question": "What does your Excel file structure look like?",
      "purpose": "Understand data organization and access patterns",
      "category": "file_structure",
      "required": true,
      "suggestedAnswers": [
        "Single sheet with tabular data (rows and columns)",
        "Multiple sheets (describe each sheet's purpose)",
        "Complex structure with merged cells, headers, etc.",
        "Provide column names/headers if known",
        "Provide sample data or describe structure",
        "Don't have file yet - need to create from scratch"
      ]
    },
    {
      "id": "q3",
      "question": "Where does the input data come from?",
      "purpose": "Determine data source and reading approach",
      "category": "data_source",
      "required": true,
      "suggestedAnswers": [
        "Existing Excel file(s) - need to read from them",
        "CSV files that need conversion to Excel",
        "Database query results",
        "API or web scraping",
        "User input or generated by code",
        "Manual data entry (creating template)"
      ]
    },
    {
      "id": "q4",
      "question": "What should the output be?",
      "purpose": "Define the end result of automation",
      "category": "output",
      "required": true,
      "suggestedAnswers": [
        "New Excel file with processed data",
        "Updated/modified existing Excel file",
        "Multiple Excel files (reports, summaries)",
        "Formatted Excel report with charts",
        "Extract specific data (printed or saved elsewhere)",
        "Just analyze data, no Excel output needed"
      ]
    },
    {
      "id": "q5",
      "question": "What data processing or business logic is needed?",
      "purpose": "Understand calculations, transformations, and rules",
      "category": "business_logic",
      "required": true,
      "suggestedAnswers": [
        "Simple read/write (no processing)",
        "Mathematical calculations (describe formulas)",
        "Data filtering based on conditions",
        "Aggregations (sums, averages, counts)",
        "Data cleaning (remove duplicates, handle missing values)",
        "Lookups or matching data across sheets",
        "Date/time calculations",
        "Text processing (split, concatenate, format)",
        "Describe specific logic needed"
      ]
    },
    {
      "id": "q6",
      "question": "How much data are you working with?",
      "purpose": "Determine appropriate libraries and performance considerations",
      "category": "data_volume",
      "required": false,
      "suggestedAnswers": [
        "Small (under 1,000 rows)",
        "Medium (1,000-50,000 rows)",
        "Large (50,000+ rows)",
        "Multiple files with varying sizes",
        "Not sure yet"
      ]
    },
    {
      "id": "q7",
      "question": "Do you need to preserve Excel formatting, formulas, or just work with values?",
      "purpose": "Choose appropriate library (openpyxl vs pandas)",
      "category": "excel_features",
      "required": true,
      "suggestedAnswers": [
        "Just read/write values (formatting doesn't matter)",
        "Need to preserve existing formatting",
        "Need to apply new formatting (colors, fonts, borders)",
        "Need to work with Excel formulas",
        "Need charts and visualizations",
        "Need advanced features (pivot tables, data validation)"
      ]
    },
    {
      "id": "q8",
      "question": "How will this automation be triggered?",
      "purpose": "Understand execution context and workflow integration",
      "category": "execution",
      "required": false,
      "suggestedAnswers": [
        "Run manually when needed",
        "Scheduled (daily, weekly, monthly)",
        "Triggered by event (new file arrives, button click)",
        "Part of larger data pipeline",
        "One-time task",
        "Not sure yet"
      ]
    },
    {
      "id": "q9",
      "question": "What Python version and libraries can you use?",
      "purpose": "Ensure code compatibility with environment",
      "category": "technical_environment",
      "required": false,
      "suggestedAnswers": [
        "Python 3.x (latest version)",
        "Specific version constraint",
        "Can install any libraries needed",
        "Limited to specific libraries (list them)",
        "Not sure - provide recommendations"
      ]
    },
    {
      "id": "q10",
      "question": "Do you have a sample Excel file or example of what you're working with?",
      "purpose": "Get concrete example for accurate solution",
      "category": "sample_data",
      "required": false,
      "suggestedAnswers": [
        "Yes, can provide sample file",
        "Can describe structure in detail",
        "Can show example data format",
        "No sample yet - need to create from description"
      ]
    }
  ],
  
  "blueprint": {
    "refinementStrategy": "Transform generic automation request into detailed specification with Excel operations, data structure, and business logic",
    "requiredInformation": [
      "Specific Excel tasks to automate",
      "Excel file structure and organization",
      "Input data source and format",
      "Desired output and deliverables",
      "Business logic and calculations",
      "Data volume and scale",
      "Excel features needed (formatting, formulas, charts)",
      "Execution context and triggers",
      "Python version and library constraints",
      "Sample data or file structure"
    ],
    "plannedStructure": {
      "sections": [
        "Automation objectives (what tasks to automate, why)",
        "Input data specification (source, format, structure)",
        "Excel file structure (sheets, columns, data organization)",
        "Processing logic (calculations, transformations, rules)",
        "Output requirements (format, structure, delivery)",
        "Excel features needed (formatting, formulas, charts)",
        "Technical environment (Python version, libraries)",
        "Code quality requirements (error handling, logging, comments)",
        "Performance considerations (data volume, speed needs)",
        "Execution workflow (how and when code runs)"
      ]
    },
    "expectedOutputFormat": "Comprehensive Excel automation specification ready for Python implementation",
    "estimatedTokensNeeded": 450
  }
}


----

Scenario 3: SQL Data Analytics Query

Original Prompt:

text
Write a SQL query to analyze sales performance

Analysis JSON:

json
{
  "analysis": {
    "currentState": "Request for SQL analytics query with no database schema, specific metrics, or analysis objectives. 'Sales performance' is too broad - could mean revenue, growth, product performance, regional analysis, customer segments, or many other dimensions.",
    "criticalIssues": [
      "Database schema unknown (tables, columns, relationships)",
      "Specific metrics not defined",
      "Analysis dimensions unclear (time, product, region, customer)",
      "No indication of what questions need answering",
      "Time period not specified",
      "SQL dialect/database system not mentioned",
      "Output format expectations unclear"
    ],
    "strengths": [
      "Query language specified (SQL)",
      "General domain identified (sales performance)",
      "Intent to analyze data is clear"
    ],
    "estimatedCompletenessScore": 20
  },
  
  "improvementAreas": [
    {
      "category": "Analysis Objectives",
      "priority": "critical",
      "issues": [
        "Specific metrics not defined",
        "Business questions not stated",
        "KPIs of interest unclear",
        "Analysis dimensions not specified"
      ]
    },
    {
      "category": "Database Context",
      "priority": "critical",
      "issues": [
        "Schema completely unknown",
        "Table structures not provided",
        "Column names and data types unclear",
        "Relationships between tables not specified"
      ]
    },
    {
      "category": "Query Specifications",
      "priority": "high",
      "issues": [
        "Time period not defined",
        "Grouping/aggregation needs unclear",
        "Filtering criteria not specified",
        "Sort order and limits not mentioned"
      ]
    }
  ],
  
  "questions": [
    {
      "id": "q1",
      "question": "What specific aspects of sales performance do you want to analyze?",
      "purpose": "Define the analysis focus and metrics",
      "category": "analysis_focus",
      "required": true,
      "suggestedAnswers": [
        "Total revenue and growth trends",
        "Sales by product/category",
        "Sales by region/location",
        "Sales by customer segment or salesperson",
        "Top performing products",
        "Sales conversion and funnel metrics",
        "Average order value and transaction counts",
        "Comparison between time periods (YoY, MoM)",
        "Customer behavior (repeat purchases, lifetime value)",
        "Multiple metrics (describe which ones)"
      ]
    },
    {
      "id": "q2",
      "question": "What specific questions are you trying to answer?",
      "purpose": "Clarify business objectives and decision-making needs",
      "category": "business_questions",
      "required": true,
      "suggestedAnswers": [
        "Which products are selling best?",
        "How are sales trending over time?",
        "Which regions are underperforming?",
        "Who are our top customers?",
        "What's our month-over-month growth?",
        "How does this quarter compare to last quarter?",
        "What's the revenue breakdown by category?",
        "Other specific question (describe)"
      ]
    },
    {
      "id": "q3",
      "question": "What does your database schema look like?",
      "purpose": "Understand available data and table structures",
      "category": "schema",
      "required": true,
      "suggestedAnswers": [
        "Provide table names and their key columns",
        "Describe the main sales/transaction table",
        "List all relevant tables (orders, products, customers, etc.)",
        "Share schema diagram or ERD if available",
        "Provide sample of table structures",
        "Common structure: orders (id, date, customer_id, total) + order_items (product_id, quantity, price)"
      ],
      "followUp": "If possible, provide: table names, key columns, and relationships (foreign keys)"
    },
    {
      "id": "q4",
      "question": "What time period should the analysis cover?",
      "purpose": "Define temporal scope of analysis",
      "category": "time_period",
      "required": true,
      "suggestedAnswers": [
        "Last 30 days",
        "Current month",
        "Last quarter",
        "Year-to-date (YTD)",
        "Last 12 months",
        "Specific date range (provide dates)",
        "All historical data",
        "Compare multiple periods (e.g., this month vs last month)"
      ]
    },
    {
      "id": "q5",
      "question": "How should the results be grouped or broken down?",
      "purpose": "Determine aggregation and grouping dimensions",
      "category": "grouping",
      "required": true,
      "suggestedAnswers": [
        "By time period (daily, weekly, monthly)",
        "By product or product category",
        "By geographic region or location",
        "By customer or customer segment",
        "By salesperson or sales team",
        "Multiple dimensions (e.g., by month AND by product)",
        "No grouping - overall totals only"
      ]
    },
    {
      "id": "q6",
      "question": "What SQL database system are you using?",
      "purpose": "Ensure syntax compatibility with specific SQL dialect",
      "category": "database_system",
      "required": true,
      "suggestedAnswers": [
        "PostgreSQL",
        "MySQL/MariaDB",
        "Microsoft SQL Server",
        "Oracle",
        "SQLite",
        "Other (specify)",
        "Not sure - use standard SQL"
      ]
    },
    {
      "id": "q7",
      "question": "Are there any filtering conditions or criteria?",
      "purpose": "Define which data to include/exclude",
      "category": "filters",
      "required": false,
      "suggestedAnswers": [
        "Only completed/paid orders",
        "Exclude returns or cancellations",
        "Specific product categories only",
        "Specific regions or locations",
        "Customers meeting certain criteria",
        "Minimum order value threshold",
        "No filters - include all data"
      ]
    },
    {
      "id": "q8",
      "question": "How should the results be sorted and limited?",
      "purpose": "Define output ordering and size",
      "category": "output_format",
      "required": false,
      "suggestedAnswers": [
        "Top N results (specify N and sort criteria)",
        "Sort by highest revenue first",
        "Sort chronologically",
        "Show all results, no limit",
        "Paginated results",
        "No specific preference"
      ]
    },
    {
      "id": "q9",
      "question": "Do you need any calculated metrics or derived fields?",
      "purpose": "Identify complex calculations needed",
      "category": "calculations",
      "required": false,
      "suggestedAnswers": [
        "Growth rates (percentage change)",
        "Running totals or cumulative sums",
        "Averages or ratios",
        "Percentages of total",
        "Year-over-year comparisons",
        "Moving averages",
        "Just basic sums and counts"
      ]
    },
    {
      "id": "q10",
      "question": "What's the approximate size of your database?",
      "purpose": "Consider performance optimization needs",
      "category": "data_scale",
      "required": false,
      "suggestedAnswers": [
        "Small (under 100K rows)",
        "Medium (100K - 1M rows)",
        "Large (1M - 10M rows)",
        "Very large (10M+ rows)",
        "Not sure",
        "Performance is critical - need optimized query"
      ]
    }
  ],
  
  "blueprint": {
    "refinementStrategy": "Transform vague analytics request into precise SQL query specification with schema details, metrics, and analysis dimensions",
    "requiredInformation": [
      "Specific sales metrics and KPIs",
      "Business questions to answer",
      "Database schema (tables, columns, relationships)",
      "Time period for analysis",
      "Grouping and aggregation dimensions",
      "SQL database system/dialect",
      "Filtering conditions",
      "Sort order and result limits",
      "Calculated metrics needed",
      "Data scale and performance needs"
    ],
    "plannedStructure": {
      "sections": [
        "Analysis objectives (what metrics, what questions)",
        "Database schema (tables, columns, relationships, sample data)",
        "Time scope (period to analyze, comparisons needed)",
        "Metrics and calculations (revenue, counts, averages, growth rates)",
        "Grouping and dimensions (how to break down results)",
        "Filtering criteria (what data to include/exclude)",
        "Output format (sort order, limits, column names)",
        "SQL dialect and database system",
        "Performance considerations (indexes, optimization needs)",
        "Expected result structure (example of desired output)"
      ]
    },
    "expectedOutputFormat": "Comprehensive SQL query specification with schema, metrics, and clear analysis objectives",
    "estimatedTokensNeeded": 450
  }
}



