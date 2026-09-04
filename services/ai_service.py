import os
import json
from config import Config

def get_gemini_model():
    """Initializes and returns Gemini generative model if API key is present."""
    api_key = Config.GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Gemini init error: {e}")
        return None


def generate_personalized_roadmap(user, career_role, gap_analysis):
    """
    Generates a personalized, phased learning roadmap.
    Uses Gemini AI if available, otherwise generates a smart deterministic roadmap.
    """
    missing_crit = [m['skill'].name for m in gap_analysis['missing_critical_skills']]
    missing_rec = [m['skill'].name for m in gap_analysis['missing_recommended_skills']]
    acquired = [m['skill'].name for m in gap_analysis['matched_skills']]
    
    model = get_gemini_model()
    if model:
        try:
            prompt = f"""
            You are a senior tech career coach. Create a customized, highly structured 4-phase learning roadmap for a student targeting the role: {career_role.title}.
            
            Student Profile:
            - Target Career: {career_role.title} ({career_role.category})
            - Acquired Skills: {', '.join(acquired) if acquired else 'Beginner / None'}
            - Missing Critical Skills: {', '.join(missing_crit) if missing_crit else 'None'}
            - Missing Recommended Skills: {', '.join(missing_rec) if missing_rec else 'None'}
            - Current Match Score: {gap_analysis['match_score']}%
            
            Return a JSON object with the following structure ONLY (no markdown fences, just pure JSON):
            {{
                "summary": "2 sentence encouraging summary of their personalized path",
                "estimated_weeks": 8,
                "phases": [
                    {{
                        "phase_number": 1,
                        "phase_title": "Phase 1: Title",
                        "duration": "Weeks 1-2",
                        "focus_skills": ["Skill 1", "Skill 2"],
                        "milestones": [
                            "Specific milestone actionable task 1",
                            "Specific milestone actionable task 2",
                            "Specific milestone actionable task 3"
                        ],
                        "recommended_practice": "Hands-on mini exercise"
                    }}
                ],
                "pro_tips": [
                    "Actionable career advice tip 1",
                    "Actionable career advice tip 2"
                ]
            }}
            """
            response = model.generate_content(prompt)
            text = response.text.strip()
            # Clean possible markdown block
            if text.startswith('```'):
                text = text.strip('`')
                if text.startswith('json'):
                    text = text[4:].strip()
            return json.loads(text)
        except Exception as e:
            print(f"Gemini roadmap generation failed, falling back to smart engine: {e}")
            
    # Smart Fallback Roadmap Generator
    phases = []
    
    # Phase 1: Core Fundamentals & Missing Critical Skills (Part 1)
    phase1_skills = missing_crit[:2] if missing_crit else (missing_rec[:2] if missing_rec else ["Advanced Concepts"])
    phases.append({
        "phase_number": 1,
        "phase_title": "Foundational Mastery & Core Essentials",
        "duration": "Weeks 1 - 3",
        "focus_skills": phase1_skills,
        "milestones": [
            f"Master core syntax, design patterns, and environment setup for {', '.join(phase1_skills)}.",
            "Complete official documentation tutorials and 10+ hands-on coding challenges.",
            "Build a modular mini-prototype demonstrating fundamental architecture."
        ],
        "recommended_practice": f"Build a clean starter project leveraging {phase1_skills[0] if phase1_skills else career_role.title} with full unit test coverage."
    })
    
    # Phase 2: Intermediate Frameworks & Remaining Critical Skills
    phase2_skills = missing_crit[2:] if len(missing_crit) > 2 else (missing_rec[:2] if missing_rec else ["System Architecture"])
    phases.append({
        "phase_number": 2,
        "phase_title": "Framework Integration & Deep Dive",
        "duration": "Weeks 4 - 6",
        "focus_skills": phase2_skills,
        "milestones": [
            f"Learn idiomatic patterns, state management, and best practices in {', '.join(phase2_skills)}.",
            "Integrate RESTful APIs / databases with robust error handling and authentication.",
            "Implement automated testing and code linting workflows."
        ],
        "recommended_practice": "Develop a full-featured CRUD application with authentication and persistent database storage."
    })
    
    # Phase 3: Advanced Tools, Cloud & Optimization
    phase3_skills = missing_rec[2:] if len(missing_rec) > 2 else ["CI/CD Pipelines", "Cloud Deployment", "Performance Tuning"]
    phases.append({
        "phase_number": 3,
        "phase_title": "Production Readiness, Cloud & DevOps",
        "duration": "Weeks 7 - 9",
        "focus_skills": phase3_skills,
        "milestones": [
            f"Containerize applications with Docker and deploy to cloud platforms (AWS/GCP/Vercel).",
            "Set up automated CI/CD pipelines for continuous integration and automated deployment.",
            "Perform database query indexing, caching with Redis, and API security audits."
        ],
        "recommended_practice": "Deploy a live production application with custom domain, SSL, and automated GitHub Actions pipeline."
    })
    
    # Phase 4: Capstone Portfolio Project & Interview Mastery
    phases.append({
        "phase_number": 4,
        "phase_title": "Capstone Portfolio & Interview Prep",
        "duration": "Weeks 10 - 12",
        "focus_skills": ["Portfolio Engineering", "System Design", "Behavioral & Technical Interviews"],
        "milestones": [
            f"Build a showcase Capstone Project solving a real-world problem tailored for {career_role.title}.",
            "Write comprehensive technical documentation, architecture diagrams, and a polished README.",
            "Practice top 50 technical interview questions, LeetCode / system design challenges, and conduct mock interviews."
        ],
        "recommended_practice": "Publish live Capstone project to GitHub with live demo URL, write a technical breakdown article, and polish LinkedIn profile."
    })
    
    return {
        "summary": f"Your personalized {career_role.title} roadmap bridges your current {gap_analysis['match_score']}% match score to 100% job readiness with step-by-step phases.",
        "estimated_weeks": 12 if gap_analysis['match_score'] < 50 else (8 if gap_analysis['match_score'] < 80 else 4),
        "phases": phases,
        "pro_tips": [
            "Focus on building 2-3 deep, production-grade projects rather than 10 shallow tutorials.",
            "Commit code daily to GitHub and document your architectural decisions in clean READMEs.",
            "Network actively with professionals in this field on LinkedIn and participate in tech communities."
        ]
    }


def generate_mock_interview_questions(career_role, missing_skills, user_skills):
    """
    Generates tailored technical & scenario mock interview questions.
    """
    model = get_gemini_model()
    if model:
        try:
            prompt = f"""
            You are a Principal Hiring Manager interviewing a candidate for the position of {career_role.title}.
            Generate 5 highly realistic interview questions (mix of technical deep dive, system design, and practical troubleshooting) with ideal answer key points.
            
            Return JSON format ONLY:
            {{
                "questions": [
                    {{
                        "id": 1,
                        "type": "Technical / Architectural / Scenario",
                        "question": "Question text here",
                        "key_concepts": ["Concept 1", "Concept 2"],
                        "sample_answer_hint": "What a strong candidate should mention"
                    }}
                ]
            }}
            """
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith('```'):
                text = text.strip('`')
                if text.startswith('json'):
                    text = text[4:].strip()
            return json.loads(text)['questions']
        except Exception as e:
            print(f"Gemini interview gen error: {e}")
            
    # Default high quality questions per role category
    return [
        {
            "id": 1,
            "type": "Technical Architecture",
            "question": f"How do you design a scalable architecture for a high-traffic system in the context of {career_role.title}?",
            "key_concepts": ["Load Balancing", "Microservices vs Monolith", "Caching Strategies", "Database Sharding"],
            "sample_answer_hint": "Discuss separation of concerns, horizontal scaling, caching layers (Redis/CDN), and asynchronous processing with message queues."
        },
        {
            "id": 2,
            "type": "Debugging & Troubleshooting",
            "question": "Describe a scenario where an API endpoint or system service experiences sudden latency spikes. How do you diagnose and fix it?",
            "key_concepts": ["APM Profiling", "Database Slow Queries / Missing Indexes", "Connection Pools", "Memory Leaks"],
            "sample_answer_hint": "Walk through checking system metrics (CPU/RAM/I-O), inspecting slow query logs, utilizing distributed tracing, and isolating bottlenecks."
        },
        {
            "id": 3,
            "type": "Security & Best Practices",
            "question": "What security measures do you implement to prevent unauthorized access, data leaks, and common vulnerabilities?",
            "key_concepts": ["OWASP Top 10", "JWT / OAuth2", "Input Sanitization", "HTTPS / Data Encryption at Rest"],
            "sample_answer_hint": "Explain parameterized SQL queries to prevent injection, CORS policies, secure cookie flags, role-based access control, and rate limiting."
        },
        {
            "id": 4,
            "type": "Code Quality & CI/CD",
            "question": "How do you ensure code maintainability, testing coverage, and automated deployment safety within a cross-functional team?",
            "key_concepts": ["Unit & Integration Tests", "CI/CD Pipelines", "Code Reviews", "Docker / Blue-Green Deployment"],
            "sample_answer_hint": "Highlight comprehensive test suites, automated GitHub Actions checks on PRs, semantic versioning, and canary/zero-downtime rollouts."
        },
        {
            "id": 5,
            "type": "Behavioral & Trade-offs",
            "question": "Tell me about a time you had to make a technical trade-off under a tight deadline. How did you decide?",
            "key_concepts": ["Technical Debt Management", "MVP Prioritization", "Stakeholder Communication"],
            "sample_answer_hint": "Use the STAR method: explain the business need, compare pragmatic short-term solution vs long-term architecture, and plan for refactoring."
        }
    ]


def answer_career_query(user, query_text):
    """
    Answers free-form career questions using Gemini AI or structured advisor logic.
    """
    user_skills = [us.skill.name for us in user.user_skills]
    target_career = user.target_career.title if user.target_career else "Software Engineering"
    
    model = get_gemini_model()
    if model:
        try:
            prompt = f"""
            You are CareerCompass AI, an expert career mentor for tech students.
            User Profile:
            - Current Skills: {', '.join(user_skills) if user_skills else 'Beginner'}
            - Target Career: {target_career}
            - Education: {user.education or 'Computer Science / Self-taught'}
            
            User's Question: "{query_text}"
            
            Provide a clear, structured, encouraging, and highly actionable response formatted with clean markdown bullets and bold text. Keep response under 300 words.
            """
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini query error: {e}")
            
    # Intelligent rule-based advice fallback
    query_lower = query_text.lower()
    if 'resume' in query_lower:
        return (
            f"### 📄 Resume Optimization Tips for {target_career}:\n\n"
            "- **Quantify Your Achievements**: Use the Google XYZ formula (*'Accomplished [X] as measured by [Y], by doing [Z]'*).\n"
            f"- **Highlight Relevant Tech**: Ensure your skills section explicitly features keywords like **{', '.join(user_skills[:5]) if user_skills else target_career}**.\n"
            "- **Link Live Demos**: Include clickable GitHub repo links and deployed live application URLs for your top 2 projects.\n"
            "- **Keep it to 1 Page**: Use clean, single-column ATS-friendly layout with concise bullet points."
        )
    elif 'interview' in query_lower:
        return (
            f"### 🎯 Interview Preparation Strategy for {target_career}:\n\n"
            "- **Core Technical Fundamentals**: Review data structures, algorithms, and domain-specific concepts.\n"
            "- **System Design / Architecture**: Practice explaining how components interact, API contracts, and database schema design.\n"
            "- **Behavioral Stories**: Prepare 4-5 STAR stories (Situation, Task, Action, Result) covering leadership, conflict resolution, and debugging challenges.\n"
            "- **Ask Great Questions**: At the end of the interview, ask about their engineering culture, CI/CD workflow, and tech stack roadmap."
        )
    else:
        return (
            f"### 💡 Career Guidance for {target_career}:\n\n"
            f"Based on your profile, you currently have **{len(user_skills)} skills** logged. To accelerate your journey toward becoming a top-tier **{target_career}**:\n\n"
            "1. **Build a Standout Capstone Project**: Create a full-stack, deployed application that solves a real problem.\n"
            "2. **Daily Consistency**: Commit 1-2 hours daily following your interactive roadmap in the dashboard.\n"
            "3. **Industry Certifications**: Earning a recognized certification will validate your practical knowledge to recruiters.\n"
            "4. **Public Portfolio**: Share your learning in public via GitHub and LinkedIn articles."
        )
