# backend/config.py

# 1. This is a standard Python dictionary, which stores key-value pairs.
# 2. The 'key' (left side) is the name of a high-level domain (e.g., "Web Development").
# 3. The 'value' (right side) is a list of specific skill keywords associated with that domain.
DOMAIN_SKILL_MAP = {
    "Web Development": [
        "html", "css", "javascript", "typescript", "react", "angular", "vue.js",
        "node.js", "express.js", "django", "flask", "fastapi", "php", "ruby on rails","bootstrap", "next.js", "frontend", "backend", "web design", "responsive design"
    ],
    "Data Science": [
        "python", "r", "sql", "machine learning", "deep learning", "nlp", "tensorflow",
        "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
        "data analysis", "statistics", "big data", "spark", "hadoop"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "google cloud", "gcp", "docker", "kubernetes", "git",
        "jenkins", "ci/cd", "terraform", "ansible", "cloud computing", "serverless"
    ],
    "Mobile Development": [
        "swift", "kotlin", "java", "react native", "flutter", "ios", "android"
    ],
    "Core Software Engineering": [
        "java", "c++", "c#", ".net", "go", "rust", "data structures", "algorithms", 
        "oops", "C",  "DBMS"
    ],
    "Frontend Development": [
        "html", "css", "javascript", "react", "angular", "vue.js", "redux", "sass",
        "tailwind", "bootstrap", "typescript", "next.js", "vite", "jquery", "ui", "ux",
        "frontend", "web design", "user interface", "user experience"
    ],

    "Backend Development": [
        "node.js", "express.js", "django", "flask", "fastapi", "spring", "spring boot",
        "php", "laravel", "ruby on rails", "api", "rest api", "graphql", "mysql",
        "mongodb", "postgresql", "redis", "authentication", "authorization", "server"
    ],

    "Database & SQL": [
        "sql", "mysql", "postgresql", "mongodb", "nosql", "sqlite", "oracle",
        "database", "data modeling", "joins", "queries", "stored procedure",
        "normalization", "indexing", "query optimization", "schemas"
    ],

    "Machine Learning": [
        "python", "r", "machine learning", "deep learning", "nlp", "tensorflow",
        "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
        "data analysis", "data visualization", "statistics", "big data", "spark",
        "hadoop", "regression", "classification", "clustering", "ai"
    ],

    "Cloud & DevOps": [
        "aws", "azure", "google cloud", "gcp", "docker", "kubernetes", "git",
        "jenkins", "ci/cd", "terraform", "ansible", "cloud computing", "serverless",
        "devops", "linux", "bash", "shell scripting", "load balancing", "nginx"
    ],

    "Core Software Engineering": [
        "java", "c++", "c#", ".net", "go", "rust", "data structures", "algorithms",
        "oops", "object oriented", "design patterns", "system design", "software development",
        "problem solving", "competitive programming", "c", "dbms", "operating system"
    ],

    "Mobile Development": [
        "android", "ios", "flutter", "react native", "swift", "kotlin", "java",
        "mobile apps", "cross platform", "ui design", "firebase", "xcode", "gradle"
    ],

    "Security & Networking": [
        "networking", "cybersecurity", "firewall", "vpn", "encryption", "penetration testing",
        "ethical hacking", "wireshark", "tcp/ip", "ssl", "security", "malware", "vulnerability",
        "owasp", "intrusion detection", "cloud security"
    ],

    "Testing & QA": [
        "manual testing", "automation testing", "selenium", "pytest", "junit", "testng",
        "qa", "software testing", "unit testing", "integration testing", "regression testing",
        "bug tracking", "jira", "postman", "cypress", "load testing"
    ]
}