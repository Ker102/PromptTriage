Troubleshooting

Original Prompt:

text
My app keeps crashing. Help me fix it.


Refined Prompt:

text
I'm experiencing repeated crashes with [Application Name] version [X.X.X] on [Operating System]. 
The crash occurs when I [specific action that triggers crash], and I receive the error message: 
"[exact error text]". 

Context:
- Frequency: [how often it happens]
- Environment: [OS version, hardware specs if relevant]
- Recent changes: [any updates, new installations, or configuration changes]
- Steps already tried: [list troubleshooting attempts]

Please help diagnose the root cause and provide step-by-step troubleshooting instructions, 
starting with the most likely causes based on the error message.

Original Prompt:

text
WiFi not working on my laptop.

Refined Prompt:

text
My laptop (Dell XPS 15, Windows 11) cannot connect to WiFi networks. The issue started [timeframe].

Specific symptoms:
- WiFi adapter is visible in Device Manager: [Yes/No]
- Can see available networks: [Yes/No]
- Connection attempt behavior: [fails immediately / connects then drops / stuck on "obtaining IP"]
- Error messages displayed: "[exact error text or code]"
- Other devices on same network: [working normally / also affected]

Troubleshooting already completed:
- Restarted laptop and router
- Ran Windows Network Troubleshooter (result: [what it said])
- Checked airplane mode is off

Please provide a diagnostic approach to identify whether this is a hardware, driver, network configuration, 
or router compatibility issue, with prioritized solutions for each scenario.


More examples:

Original Prompt:

text
Write code to connect to an API.

Refined Prompt:

text
Create a Python function to interact with the OpenWeather API.

Requirements:
- Language: Python 3.10+
- Framework: Use the 'requests' library
- Functionality: Fetch current weather data for a given city name
- Input: City name as string parameter
- Output: Return JSON response containing temperature, humidity, and weather description

Error Handling:
- Handle invalid city names (404 errors)
- Manage network timeouts (set 5-second timeout)
- Catch API authentication failures
- Validate API response structure

Code Quality:
- Include type hints for all function parameters and returns
- Add docstring with usage example
- Follow PEP 8 style guidelines
- Include inline comments for complex logic

Additional Requirements:
- Store API key as environment variable (not hardcoded)
- Implement retry logic for transient network failures (max 3 retries with exponential backoff)
- Log all API calls with timestamps for debugging

----

Example 2: Algorithm Optimization

Original Prompt:

text
Make this code faster.

Refined Prompt:

text
Optimize the following Python function for improved performance and memory efficiency:

[paste your code here]

Current Performance Context:
- Current execution time: [e.g., 2.5 seconds for 10,000 items]
- Input data size: [e.g., list of 10,000 dictionaries]
- Memory usage: [e.g., approximately 500MB]
- Bottleneck identified: [e.g., nested loops causing O(n²) complexity]

Optimization Goals:
- Target: Reduce execution time by at least 50%
- Constraint: Maintain memory usage under 300MB
- Priority: Time complexity optimization over space complexity

Analysis Required:
1. Identify current time and space complexity (Big O notation)
2. Propose algorithmic improvements (e.g., data structure changes, caching, vectorization)
3. Suggest Python-specific optimizations (list comprehensions, built-in functions, libraries like NumPy)
4. Benchmark comparison: Show before/after performance metrics

Deliverables:
- Optimized code with explanatory comments
- Complexity analysis (before and after)
- Performance test results with timing comparisons
- Trade-offs explanation if any (e.g., increased memory for speed)

---

Example 3: Database Query

Original Prompt:

text
Write SQL to get user data.

Refined Prompt:

text
Write an optimized SQL query for a PostgreSQL 14 database.

Business Requirement:
Retrieve user profiles with their total purchase amounts and order counts for customers who:
- Registered in the last 6 months
- Have made at least 3 purchases
- Have a total spending over $500
- Are active (not marked as deleted)

Database Schema:
- Table: users (id, email, registration_date, is_active, deleted_at)
- Table: orders (id, user_id, order_date, total_amount, status)
- Relationship: orders.user_id → users.id

Query Requirements:
- Return columns: user_id, email, registration_date, total_orders, total_spent
- Sort by: total_spent (descending)
- Include only orders with status = 'completed'
- Performance: Query should execute under 500ms for 1M users and 10M orders

Optimization Considerations:
- Utilize appropriate indexes (suggest which columns should be indexed)
- Avoid N+1 query patterns
- Use JOINs efficiently
- Consider query plan (explain EXPLAIN ANALYZE output)
- Handle NULL values appropriately

Additional Requirements:
- Include comments explaining complex parts
- Suggest any missing indexes that would improve performance
- Provide alternative query approaches if applicable (e.g., CTE vs subquery)




