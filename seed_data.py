import json
from datetime import datetime, date
from models import (
    db, User, Skill, UserSkill, CareerRole, CareerSkillRequirement,
    LearningResource, Certification, ProjectIdea, UserRoadmapProgress, DailyLog
)

def seed_database(app, force=False):
    with app.app_context():
        db.create_all()
        
        # Check if database is already fully seeded
        if not force and CareerRole.query.count() >= 50 and User.query.filter_by(email='admin@careercompass.com').first():
            print("Database already contains all 50 career roles. Skipping...")
            return

        print("Seeding CareerCompass database with 50 rich career paths and 100+ skills...")
        # Clear existing collections for a clean, consistent seed
        db.drop_all()
        db.create_all()

        # 1. Create Default Users
        admin_user = User(
            full_name='System Administrator',
            email='admin@careercompass.com',
            role='admin',
            education='Master in Computer Science',
            bio='CareerCompass platform administrator and lead mentor.'
        )
        admin_user.set_password('Admin@123')
        db.session.add(admin_user)

        demo_student = User(
            full_name='Fathima Nishva',
            email='student@careercompass.com',
            role='student',
            education='B.Tech in Computer Science & Engineering',
            bio='Aspiring Full Stack & AI Engineer passionate about building scalable web systems.'
        )
        demo_student.set_password('Student@123')
        db.session.add(demo_student)
        db.session.flush()

        # 2. Seed Skills (Categorized - 100+ skills)
        skills_data = [
            # Frontend
            ("HTML5", "Frontend", "Standard markup language for creating web pages."),
            ("CSS3", "Frontend", "Style sheet language used for styling HTML elements."),
            ("JavaScript", "Frontend", "High-level, just-in-time compiled programming language of the Web."),
            ("TypeScript", "Frontend", "Strict syntactical superset of JavaScript adding static typing."),
            ("React", "Frontend", "Component-based UI library for building responsive user interfaces."),
            ("Vue.js", "Frontend", "Progressive framework for building modern user interfaces."),
            ("Angular", "Frontend", "Enterprise-grade component framework developed by Google."),
            ("Svelte", "Frontend", "Radical new approach to building user interfaces with zero-runtime compilation."),
            ("Tailwind CSS", "Frontend", "Utility-first CSS framework for rapid UI styling."),
            ("Next.js", "Frontend", "React framework for server-side rendering and static web apps."),
            ("Redux / State Management", "Frontend", "Predictable state container for JavaScript apps."),
            ("WebAssembly", "Frontend", "Binary instruction format for high-performance execution on the web."),
            ("Design Systems", "Frontend", "Reusable components and standard guidelines for cohesive UI design."),
            
            # Backend
            ("Python", "Backend", "High-level programming language emphasizing readability and rapid development."),
            ("Flask", "Backend", "Lightweight WSGI web application framework in Python."),
            ("Django", "Backend", "High-level Python web framework encouraging clean, pragmatic design."),
            ("FastAPI", "Backend", "Modern, high-performance web framework for building APIs with Python 3.8+."),
            ("Node.js", "Backend", "Asynchronous event-driven JavaScript runtime environment."),
            ("Express.js", "Backend", "Fast, unopinionated, minimalist web framework for Node.js."),
            ("Java", "Backend", "Class-based, object-oriented programming language."),
            ("Spring Boot", "Backend", "Enterprise-ready framework for building stand-alone Spring applications."),
            ("Go (Golang)", "Backend", "Statically typed, compiled language engineered at Google for concurrency."),
            ("C# (.NET Core)", "Backend", "Cross-platform enterprise backend runtime and programming language."),
            ("Rust Programming", "Backend", "Memory-safe, high-performance systems programming language without garbage collection."),
            ("C++ Programming", "Backend", "General-purpose programming language with low-level memory manipulation."),
            ("REST APIs", "Backend", "Architectural style for designing networked web applications."),
            ("GraphQL", "Backend", "Query language and server runtime for flexible APIs."),
            ("gRPC & Protocol Buffers", "Backend", "High performance, open source universal RPC framework."),
            ("Kafka & Message Queues", "Backend", "Distributed event streaming platform for high-throughput data pipelines."),
            ("Microservices Architecture", "Backend", "Modular architectural pattern for building scalable enterprise systems."),
            
            # Database
            ("SQL & Relational Databases", "Database", "Structured Query Language for managing relational databases."),
            ("PostgreSQL", "Database", "Powerful, open-source object-relational database system."),
            ("MySQL", "Database", "Popular open-source relational database management system."),
            ("MongoDB", "Database", "Document-oriented NoSQL database program."),
            ("Redis", "Database", "In-memory data structure store used as a database, cache, and message broker."),
            ("Cassandra", "Database", "Distributed wide-column NoSQL database designed for massive data volumes."),
            ("Elasticsearch", "Database", "Distributed, JSON-based search and analytics engine."),
            ("Vector Databases & Pinecone", "Database", "Specialized database indexing high-dimensional embeddings for AI search."),
            ("Snowflake & dbt", "Database", "Cloud data warehouse and transformation framework for modern analytics."),
            
            # AI & Data Science
            ("Machine Learning", "AI & Data", "Algorithms that learn patterns directly from data to make predictions."),
            ("Deep Learning", "AI & Data", "Neural network architectures capable of learning complex data representations."),
            ("PyTorch", "AI & Data", "Open source machine learning framework based on the Torch library."),
            ("TensorFlow", "AI & Data", "End-to-end open source platform for machine learning."),
            ("Scikit-learn", "AI & Data", "Simple and efficient tools for predictive data analysis in Python."),
            ("Pandas & NumPy", "AI & Data", "Core libraries for data manipulation, numerical computing, and array processing."),
            ("Natural Language Processing", "AI & Data", "Field of AI enabling computers to understand and generate human text."),
            ("Computer Vision", "AI & Data", "Field of AI dealing with how computers can gain high-level understanding from digital images."),
            ("Generative AI & LLMs", "AI & Data", "Techniques and architectures behind Large Language Models and prompt engineering."),
            ("Prompt Engineering & LangChain", "AI & Data", "Frameworks and techniques for building context-aware LLM applications."),
            ("MLOps & MLflow", "AI & Data", "Practices for deploying and maintaining machine learning models in production reliably."),
            ("Transformers & Hugging Face", "AI & Data", "State-of-the-art pretrained transformer models for natural language understanding."),
            ("OpenCV & Image Processing", "AI & Data", "Open source computer vision and machine learning software library."),
            ("Apache Spark", "AI & Data", "Unified analytics engine for large-scale data processing and ETL pipelines."),
            ("Airflow & Data Pipelines", "AI & Data", "Workflow orchestration platform to programmatically author and monitor workflows."),
            ("Data Visualization", "AI & Data", "Techniques for representing data graphically (Chart.js, Matplotlib, Tableau)."),
            ("Reinforcement Learning", "AI & Data", "Machine learning training method based on rewarding desired behaviors."),
            
            # Cloud & DevOps
            ("Git & GitHub", "DevOps", "Distributed version control system for tracking changes in source code."),
            ("Docker", "DevOps", "Platform for containerizing applications to ensure uniform environments."),
            ("Kubernetes", "DevOps", "Open-source system for automating deployment, scaling, and container operations."),
            ("CI/CD Pipelines", "DevOps", "Continuous Integration and Continuous Deployment automation (GitHub Actions, Jenkins)."),
            ("AWS Cloud", "Cloud", "Comprehensive cloud computing platform provided by Amazon."),
            ("Google Cloud Platform", "Cloud", "Suite of cloud computing services that runs on Google's infrastructure."),
            ("Microsoft Azure", "Cloud", "Enterprise cloud platform offering computing, analytics, and networking."),
            ("Linux Administration", "DevOps", "Managing and configuring Linux-based operating systems and servers."),
            ("Terraform / IaC", "DevOps", "Infrastructure as Code tool to build, change, and version cloud infrastructure safely."),
            ("Ansible", "DevOps", "Open-source IT engine that automates provisioning, configuration management, and app deployment."),
            ("Prometheus & Grafana", "DevOps", "Systems monitoring and alerting toolkit with interactive visual dashboards."),
            ("Helm & Cloud Native Tooling", "DevOps", "Package manager for Kubernetes to define, install, and upgrade complex K8s applications."),
            
            # Mobile
            ("Flutter", "Mobile", "UI toolkit for building cross-platform natively compiled mobile apps from a single codebase."),
            ("React Native", "Mobile", "Framework for creating native mobile apps for iOS and Android using React."),
            ("Swift / iOS", "Mobile", "Modern programming language for iOS, iPadOS, macOS, and watchOS."),
            ("SwiftUI", "Mobile", "Declarative framework for building user interfaces across all Apple platforms."),
            ("Kotlin / Android", "Mobile", "Modern statically typed programming language used for Android development."),
            ("Jetpack Compose", "Mobile", "Android's modern toolkit for building native UI."),
            
            # Cybersecurity
            ("Web Application Security", "Security", "Practices and defenses to protect web applications from malicious attacks."),
            ("OWASP Top 10", "Security", "Standard awareness document for developers detailing critical security risks."),
            ("Network Security", "Security", "Policies and practices adopted to prevent unauthorized access and network threats."),
            ("Cryptography", "Security", "Techniques for secure communication in the presence of adversarial third parties."),
            ("Penetration Testing & Metasploit", "Security", "Offensive security methodologies and ethical exploitation tools."),
            ("Cloud Security & IAM", "Security", "Securing cloud workloads, identities, policies, and boundary access control."),
            ("SIEM & Threat Hunting", "Security", "Security Information and Event Management analysis (Splunk, Elastic, Sentinel)."),
            ("Reverse Engineering & Malware Analysis", "Security", "Decompiling binaries and analyzing malicious payload mechanics."),
            
            # UI/UX & Design
            ("Figma", "UI/UX", "Collaborative cloud-based interface design and wireframing tool."),
            ("UI/UX Design Systems", "UI/UX", "Standardized reusable components and visual guidelines."),
            ("User Research & Usability Testing", "UI/UX", "Methodologies to validate interfaces with real human user behavior."),
            ("Information Architecture", "UI/UX", "Structural design of shared information environments and navigation flows."),
            
            # Specialized & Emerging
            ("Solidity", "Blockchain", "Object-oriented language for writing smart contracts on Ethereum."),
            ("Ethereum & Web3.js", "Blockchain", "Decentralized application protocols and blockchain interaction libraries."),
            ("Smart Contract Auditing", "Blockchain", "Security analysis of blockchain code for vulnerabilities and re-entrancy bugs."),
            ("Embedded C & Microcontrollers", "Hardware & IoT", "Programming microcontrollers (ARM, ESP32, Arduino) and RTOS."),
            ("ROS (Robot Operating System)", "Hardware & IoT", "Robotics middleware suite providing hardware abstraction and device drivers."),
            ("IoT Protocols (MQTT, CoAP)", "Hardware & IoT", "Lightweight messaging protocols engineered for low-bandwidth, high-latency IoT networks."),
            ("C# & Unity Engine", "Game Dev", "C# programming and cross-platform real-time 3D game engine."),
            ("Unreal Engine & C++", "Game Dev", "High-fidelity real-time 3D creation tool and game engine."),
            ("Unity XR & Spatial Computing", "Game Dev", "SDKs and frameworks for building interactive VR, AR, and mixed reality applications."),
            ("Shader Programming (GLSL/HLSL)", "Game Dev", "GPU graphics programming for lighting, post-processing, and visual VFX."),
            ("Quantum Computing & Qiskit", "Emerging Tech", "Quantum programming SDK for working with quantum circuits and algorithms."),
            ("Bioinformatics & Biopython", "HealthTech", "Computational analysis of biological sequencing, genomic datasets, and protein folding."),
            ("GIS & Spatial Analysis", "Spatial", "Geographic Information Systems mapping, spatial indexing (PostGIS), and satellite imagery processing."),
            ("Product Roadmap & Strategy", "Management", "Defining product vision, user journey mapping, metrics, and sprint backlogs."),
            ("FinTech & FIX Protocol", "FinTech", "Financial message exchange standards and ultra-low latency transaction architectures."),
            ("Developer Experience & Tooling", "DevOps", "Optimizing developer workflows, internal platforms, build systems, and CLI tools.")
        ]

        skill_map = {}
        for name, category, desc in skills_data:
            skill = Skill(name=name, category=category, description=desc)
            db.session.add(skill)
            skill_map[name] = skill
        db.session.flush()

        # 3. Seed 50 Comprehensive Career Roles
        careers_data = [
            # 1
            {
                "title": "Full Stack Web Developer",
                "category": "Software Engineering",
                "description": "Designs, builds, and maintains both client-facing frontends and robust server-side APIs and databases for modern web applications.",
                "salary": "$90,000 - $140,000 / yr",
                "demand": "Very High",
                "difficulty": "Intermediate",
                "icon": "fa-layer-group",
                "skills": [
                    ("HTML5", "Critical", "Advanced"),
                    ("CSS3", "Critical", "Advanced"),
                    ("JavaScript", "Critical", "Advanced"),
                    ("React", "Critical", "Intermediate"),
                    ("Python", "Critical", "Intermediate"),
                    ("Flask", "Critical", "Intermediate"),
                    ("SQL & Relational Databases", "Critical", "Intermediate"),
                    ("REST APIs", "Critical", "Advanced"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                    ("Docker", "Recommended", "Beginner"),
                    ("TypeScript", "Recommended", "Intermediate"),
                    ("Tailwind CSS", "Recommended", "Intermediate"),
                    ("CI/CD Pipelines", "Recommended", "Beginner"),
                ]
            },
            # 2
            {
                "title": "AI & Machine Learning Engineer",
                "category": "AI & Data Science",
                "description": "Researches, builds, and deploys intelligent models and machine learning pipelines that solve complex classification, prediction, and generative tasks.",
                "salary": "$115,000 - $175,000 / yr",
                "demand": "Extremely High",
                "difficulty": "Advanced",
                "icon": "fa-brain",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("Machine Learning", "Critical", "Advanced"),
                    ("Deep Learning", "Critical", "Intermediate"),
                    ("PyTorch", "Critical", "Intermediate"),
                    ("Pandas & NumPy", "Critical", "Advanced"),
                    ("Scikit-learn", "Critical", "Advanced"),
                    ("Natural Language Processing", "Recommended", "Intermediate"),
                    ("Generative AI & LLMs", "Recommended", "Intermediate"),
                    ("Prompt Engineering & LangChain", "Recommended", "Intermediate"),
                    ("Docker", "Recommended", "Intermediate"),
                    ("REST APIs", "Recommended", "Intermediate"),
                    ("SQL & Relational Databases", "Recommended", "Intermediate"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                ]
            },
            # 3
            {
                "title": "Data Scientist",
                "category": "AI & Data Science",
                "description": "Extracts actionable business insights, creates predictive models, and conducts exploratory statistical analysis on massive multi-dimensional datasets.",
                "salary": "$105,000 - $160,000 / yr",
                "demand": "Very High",
                "difficulty": "Intermediate",
                "icon": "fa-chart-pie",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("Pandas & NumPy", "Critical", "Advanced"),
                    ("SQL & Relational Databases", "Critical", "Advanced"),
                    ("Data Visualization", "Critical", "Advanced"),
                    ("Machine Learning", "Critical", "Intermediate"),
                    ("Scikit-learn", "Critical", "Intermediate"),
                    ("Deep Learning", "Recommended", "Beginner"),
                    ("Git & GitHub", "Recommended", "Intermediate"),
                ]
            },
            # 4
            {
                "title": "Cloud & DevOps Engineer",
                "category": "Cloud & Infrastructure",
                "description": "Automates cloud infrastructure, manages continuous integration/continuous delivery pipelines, and ensures high availability and scalability.",
                "salary": "$110,000 - $165,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-cloud",
                "skills": [
                    ("Linux Administration", "Critical", "Advanced"),
                    ("Docker", "Critical", "Advanced"),
                    ("Kubernetes", "Critical", "Intermediate"),
                    ("AWS Cloud", "Critical", "Intermediate"),
                    ("CI/CD Pipelines", "Critical", "Advanced"),
                    ("Git & GitHub", "Critical", "Advanced"),
                    ("Python", "Recommended", "Intermediate"),
                    ("Terraform / IaC", "Recommended", "Intermediate"),
                    ("Network Security", "Recommended", "Intermediate"),
                    ("REST APIs", "Recommended", "Intermediate"),
                ]
            },
            # 5
            {
                "title": "Cybersecurity Analyst",
                "category": "Security & Defense",
                "description": "Monitors networks, identifies system vulnerabilities, audits application defenses, and investigates security incidents.",
                "salary": "$95,000 - $150,000 / yr",
                "demand": "Very High",
                "difficulty": "Intermediate",
                "icon": "fa-shield-halved",
                "skills": [
                    ("Web Application Security", "Critical", "Advanced"),
                    ("OWASP Top 10", "Critical", "Advanced"),
                    ("Network Security", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Intermediate"),
                    ("Cryptography", "Recommended", "Intermediate"),
                    ("Python", "Recommended", "Intermediate"),
                    ("Git & GitHub", "Recommended", "Beginner"),
                ]
            },
            # 6
            {
                "title": "Mobile App Developer (Cross-Platform)",
                "category": "Mobile Development",
                "description": "Engineers fluid, cross-platform mobile apps for iOS and Android with responsive touch interfaces and cloud backend integration.",
                "salary": "$90,000 - $145,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-mobile-screen-button",
                "skills": [
                    ("Flutter", "Critical", "Advanced"),
                    ("JavaScript", "Critical", "Intermediate"),
                    ("React Native", "Critical", "Intermediate"),
                    ("REST APIs", "Critical", "Advanced"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                    ("UI/UX Design Systems", "Recommended", "Intermediate"),
                    ("SQL & Relational Databases", "Recommended", "Intermediate"),
                ]
            },
            # 7
            {
                "title": "UI/UX Designer & Design Technologist",
                "category": "Design & User Experience",
                "description": "Creates human-centered interface architectures, interactive wireframes, and design systems while bridging the gap between design and frontend code.",
                "salary": "$85,000 - $135,000 / yr",
                "demand": "High",
                "difficulty": "Beginner-friendly",
                "icon": "fa-palette",
                "skills": [
                    ("Figma", "Critical", "Advanced"),
                    ("UI/UX Design Systems", "Critical", "Advanced"),
                    ("User Research & Usability Testing", "Critical", "Advanced"),
                    ("HTML5", "Critical", "Intermediate"),
                    ("CSS3", "Critical", "Advanced"),
                    ("JavaScript", "Recommended", "Intermediate"),
                    ("Tailwind CSS", "Recommended", "Intermediate"),
                ]
            },
            # 8
            {
                "title": "Data Engineer (Big Data & ETL)",
                "category": "AI & Data Science",
                "description": "Constructs robust data extraction pipelines, lakehouse architectures, and real-time streaming infrastructure for large-scale enterprise analytics.",
                "salary": "$110,000 - $165,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-database",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("SQL & Relational Databases", "Critical", "Advanced"),
                    ("PostgreSQL", "Critical", "Intermediate"),
                    ("Apache Spark", "Critical", "Intermediate"),
                    ("Airflow & Data Pipelines", "Critical", "Intermediate"),
                    ("Docker", "Recommended", "Intermediate"),
                    ("AWS Cloud", "Recommended", "Intermediate"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                ]
            },
            # 9
            {
                "title": "Generative AI & LLM Solutions Engineer",
                "category": "AI & Data Science",
                "description": "Develops Retrieval-Augmented Generation (RAG) applications, custom agentic workflows, and fine-tunes open-source LLMs for production deployment.",
                "salary": "$125,000 - $190,000 / yr",
                "demand": "Extremely High",
                "difficulty": "Advanced",
                "icon": "fa-microchip",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("Generative AI & LLMs", "Critical", "Advanced"),
                    ("Prompt Engineering & LangChain", "Critical", "Advanced"),
                    ("PyTorch", "Critical", "Intermediate"),
                    ("Natural Language Processing", "Critical", "Intermediate"),
                    ("REST APIs", "Critical", "Intermediate"),
                    ("Docker", "Recommended", "Intermediate"),
                    ("Vector Databases & Pinecone", "Critical", "Advanced"),
                ]
            },
            # 10
            {
                "title": "Blockchain & Smart Contract Developer",
                "category": "Web3 & Decentralized Systems",
                "description": "Programs decentralized applications, smart contract protocols, and cryptographically verified Web3 systems on EVM and Solana chains.",
                "salary": "$100,000 - $160,000 / yr",
                "demand": "Moderate",
                "difficulty": "Advanced",
                "icon": "fa-cubes",
                "skills": [
                    ("Solidity", "Critical", "Advanced"),
                    ("Ethereum & Web3.js", "Critical", "Advanced"),
                    ("JavaScript", "Critical", "Advanced"),
                    ("Cryptography", "Critical", "Intermediate"),
                    ("Web Application Security", "Critical", "Intermediate"),
                    ("Git & GitHub", "Critical", "Advanced"),
                ]
            },
            # 11
            {
                "title": "Site Reliability Engineer (SRE)",
                "category": "Cloud & Infrastructure",
                "description": "Bridges software engineering and system operations to maximize uptime, automate disaster recovery, and optimize infrastructure latency at scale.",
                "salary": "$120,000 - $175,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-server",
                "skills": [
                    ("Linux Administration", "Critical", "Advanced"),
                    ("Kubernetes", "Critical", "Advanced"),
                    ("Docker", "Critical", "Advanced"),
                    ("Go (Golang)", "Critical", "Intermediate"),
                    ("Python", "Critical", "Intermediate"),
                    ("CI/CD Pipelines", "Critical", "Advanced"),
                    ("AWS Cloud", "Recommended", "Intermediate"),
                    ("Prometheus & Grafana", "Critical", "Advanced"),
                ]
            },
            # 12
            {
                "title": "QA Automation & SDET Engineer",
                "category": "Software Engineering",
                "description": "Designs automated testing frameworks, end-to-end regression suites, and load testing pipelines to guarantee rock-solid software quality.",
                "salary": "$85,000 - $135,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-vial-circle-check",
                "skills": [
                    ("Python", "Critical", "Intermediate"),
                    ("JavaScript", "Critical", "Intermediate"),
                    ("Test Automation & Selenium", "Critical", "Advanced"),
                    ("API Testing & Postman", "Critical", "Advanced"),
                    ("CI/CD Pipelines", "Critical", "Intermediate"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                    ("SQL & Relational Databases", "Recommended", "Intermediate"),
                ]
            },
            # 13
            {
                "title": "Game Developer (3D & Interactive Engines)",
                "category": "Interactive Entertainment",
                "description": "Builds immersive 3D/2D games, physics engines, real-time shaders, and gameplay mechanics for PC, consoles, and mobile platforms.",
                "salary": "$85,000 - $140,000 / yr",
                "demand": "Moderate",
                "difficulty": "Intermediate",
                "icon": "fa-gamepad",
                "skills": [
                    ("C# & Unity Engine", "Critical", "Advanced"),
                    ("C++ Programming", "Critical", "Intermediate"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                    ("Unreal Engine & C++", "Recommended", "Intermediate"),
                    ("Shader Programming (GLSL/HLSL)", "Recommended", "Intermediate"),
                ]
            },
            # 14
            {
                "title": "Computer Vision & Visual AI Engineer",
                "category": "AI & Data Science",
                "description": "Engineers real-time object detection, facial recognition, video analytics, and spatial perception models for autonomous robots and edge devices.",
                "salary": "$115,000 - $170,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-eye",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("Computer Vision", "Critical", "Advanced"),
                    ("OpenCV & Image Processing", "Critical", "Advanced"),
                    ("Deep Learning", "Critical", "Advanced"),
                    ("PyTorch", "Critical", "Intermediate"),
                    ("TensorFlow", "Recommended", "Intermediate"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                ]
            },
            # 15
            {
                "title": "Natural Language Processing (NLP) Specialist",
                "category": "AI & Data Science",
                "description": "Develops conversational agents, semantic search engines, sentiment analysis models, and tokenization pipelines using transformer architectures.",
                "salary": "$120,000 - $180,000 / yr",
                "demand": "Extremely High",
                "difficulty": "Advanced",
                "icon": "fa-language",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("Natural Language Processing", "Critical", "Advanced"),
                    ("Transformers & Hugging Face", "Critical", "Advanced"),
                    ("Generative AI & LLMs", "Critical", "Intermediate"),
                    ("PyTorch", "Critical", "Intermediate"),
                    ("Deep Learning", "Critical", "Intermediate"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                ]
            },
            # 16
            {
                "title": "Technical Product Manager (TPM)",
                "category": "Engineering Management",
                "description": "Guides technical roadmaps, translates high-level customer requirements into sprint backlogs, and aligns engineering teams with business outcomes.",
                "salary": "$110,000 - $165,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-diagram-project",
                "skills": [
                    ("Product Roadmap & Strategy", "Critical", "Advanced"),
                    ("User Research & Usability Testing", "Critical", "Advanced"),
                    ("SQL & Relational Databases", "Critical", "Intermediate"),
                    ("REST APIs", "Recommended", "Intermediate"),
                    ("Git & GitHub", "Recommended", "Beginner"),
                    ("Data Visualization", "Recommended", "Intermediate"),
                ]
            },
            # 17
            {
                "title": "Embedded Systems & IoT Engineer",
                "category": "Hardware & Embedded Systems",
                "description": "Programs firmware, bare-metal microcontrollers, sensor network communications, and low-power hardware circuits for connected IoT ecosystems.",
                "salary": "$90,000 - $145,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-microchip",
                "skills": [
                    ("Embedded C & Microcontrollers", "Critical", "Advanced"),
                    ("C++ Programming", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Intermediate"),
                    ("Network Security", "Recommended", "Intermediate"),
                    ("Python", "Recommended", "Intermediate"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                    ("IoT Protocols (MQTT, CoAP)", "Critical", "Advanced"),
                ]
            },
            # 18
            {
                "title": "Penetration Tester & Ethical Hacker",
                "category": "Security & Defense",
                "description": "Conducts offensive security engagements, simulates cyberattacks against corporate perimeters, and discovers zero-day exploits before malicious adversaries.",
                "salary": "$100,000 - $160,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-user-secret",
                "skills": [
                    ("Penetration Testing & Metasploit", "Critical", "Advanced"),
                    ("OWASP Top 10", "Critical", "Advanced"),
                    ("Web Application Security", "Critical", "Advanced"),
                    ("Network Security", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Advanced"),
                    ("Python", "Critical", "Intermediate"),
                    ("Cryptography", "Recommended", "Intermediate"),
                ]
            },
            # 19
            {
                "title": "Systems Software Engineer (Rust & C++)",
                "category": "Software Engineering",
                "description": "Develops hyper-optimized low-level infrastructure, memory-safe system daemons, compilers, file systems, and high-frequency communication protocols.",
                "salary": "$115,000 - $175,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-gear",
                "skills": [
                    ("Rust Programming", "Critical", "Advanced"),
                    ("C++ Programming", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Advanced"),
                    ("Git & GitHub", "Critical", "Advanced"),
                    ("WebAssembly", "Recommended", "Intermediate"),
                ]
            },
            # 20
            {
                "title": "AR / VR (XR) & Spatial Computing Developer",
                "category": "Interactive Entertainment",
                "description": "Creates spatial user interfaces, hand-tracking interactions, real-time 3D environments, and immersive enterprise simulations for Meta Quest and Apple Vision Pro.",
                "salary": "$95,000 - $155,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-vr-cardboard",
                "skills": [
                    ("Unity XR & Spatial Computing", "Critical", "Advanced"),
                    ("C# & Unity Engine", "Critical", "Advanced"),
                    ("UI/UX Design Systems", "Critical", "Intermediate"),
                    ("JavaScript", "Recommended", "Intermediate"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                ]
            },
            
            # --- 30 NEW FEATURED CAREER PATHS ---
            # 21
            {
                "title": "Frontend Architect & Modern UI Engineer",
                "category": "Software Engineering",
                "description": "Architects large-scale micro-frontend web applications, component libraries, state synchronization layers, and ultra-performant client experiences.",
                "salary": "$115,000 - $170,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-laptop-code",
                "skills": [
                    ("TypeScript", "Critical", "Advanced"),
                    ("React", "Critical", "Advanced"),
                    ("Next.js", "Critical", "Advanced"),
                    ("Design Systems", "Critical", "Advanced"),
                    ("HTML5", "Critical", "Advanced"),
                    ("CSS3", "Critical", "Advanced"),
                    ("Tailwind CSS", "Critical", "Advanced"),
                    ("GraphQL", "Recommended", "Intermediate"),
                    ("CI/CD Pipelines", "Recommended", "Intermediate"),
                ]
            },
            # 22
            {
                "title": "Backend & Distributed Systems Engineer",
                "category": "Software Engineering",
                "description": "Constructs fault-tolerant distributed servers, high-concurrency microservices, caching clusters, and message-driven transaction systems.",
                "salary": "$120,000 - $180,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-network-wired",
                "skills": [
                    ("Go (Golang)", "Critical", "Advanced"),
                    ("Python", "Critical", "Advanced"),
                    ("REST APIs", "Critical", "Advanced"),
                    ("PostgreSQL", "Critical", "Advanced"),
                    ("Redis", "Critical", "Advanced"),
                    ("Kafka & Message Queues", "Critical", "Advanced"),
                    ("gRPC & Protocol Buffers", "Critical", "Intermediate"),
                    ("Docker", "Critical", "Advanced"),
                ]
            },
            # 23
            {
                "title": "iOS Native Application Engineer",
                "category": "Mobile Development",
                "description": "Designs and builds premium native iOS, iPadOS, and watchOS apps leveraging Swift, SwiftUI, Combine, and Apple's CoreData architectures.",
                "salary": "$105,000 - $160,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-apple-whole",
                "skills": [
                    ("Swift / iOS", "Critical", "Advanced"),
                    ("SwiftUI", "Critical", "Advanced"),
                    ("REST APIs", "Critical", "Intermediate"),
                    ("Git & GitHub", "Critical", "Advanced"),
                    ("UI/UX Design Systems", "Recommended", "Intermediate"),
                    ("SQL & Relational Databases", "Recommended", "Intermediate"),
                ]
            },
            # 24
            {
                "title": "Android Native Software Engineer",
                "category": "Mobile Development",
                "description": "Builds high-performance native Android applications with Kotlin, Jetpack Compose, Coroutines, and modern Clean Architecture.",
                "salary": "$100,000 - $155,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-android",
                "skills": [
                    ("Kotlin / Android", "Critical", "Advanced"),
                    ("Jetpack Compose", "Critical", "Advanced"),
                    ("REST APIs", "Critical", "Advanced"),
                    ("SQL & Relational Databases", "Critical", "Intermediate"),
                    ("Git & GitHub", "Critical", "Advanced"),
                    ("UI/UX Design Systems", "Recommended", "Intermediate"),
                ]
            },
            # 25
            {
                "title": "MLOps & AI Infrastructure Engineer",
                "category": "AI & Data Science",
                "description": "Builds continuous training pipelines, model registries, GPU cluster orchestration, and automated monitoring for production AI systems.",
                "salary": "$125,000 - $185,000 / yr",
                "demand": "Extremely High",
                "difficulty": "Advanced",
                "icon": "fa-infinity",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("MLOps & MLflow", "Critical", "Advanced"),
                    ("Docker", "Critical", "Advanced"),
                    ("Kubernetes", "Critical", "Advanced"),
                    ("AWS Cloud", "Critical", "Advanced"),
                    ("CI/CD Pipelines", "Critical", "Advanced"),
                    ("PyTorch", "Recommended", "Intermediate"),
                    ("Airflow & Data Pipelines", "Recommended", "Intermediate"),
                ]
            },
            # 26
            {
                "title": "Cloud Security & DevSecOps Engineer",
                "category": "Security & Defense",
                "description": "Integrates security gates into automated CI/CD pipelines, enforces cloud identity management (IAM), and hardens cloud-native architectures.",
                "salary": "$115,000 - $175,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-lock",
                "skills": [
                    ("Cloud Security & IAM", "Critical", "Advanced"),
                    ("Terraform / IaC", "Critical", "Advanced"),
                    ("Docker", "Critical", "Advanced"),
                    ("Kubernetes", "Critical", "Intermediate"),
                    ("CI/CD Pipelines", "Critical", "Advanced"),
                    ("AWS Cloud", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Advanced"),
                ]
            },
            # 27
            {
                "title": "Database Administrator & Data Architect",
                "category": "Database & Infrastructure",
                "description": "Designs high-throughput relational and NoSQL database schemas, configures replication and failover, and optimizes query execution plans.",
                "salary": "$100,000 - $155,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-table",
                "skills": [
                    ("SQL & Relational Databases", "Critical", "Advanced"),
                    ("PostgreSQL", "Critical", "Advanced"),
                    ("MongoDB", "Critical", "Advanced"),
                    ("Redis", "Critical", "Intermediate"),
                    ("Linux Administration", "Critical", "Intermediate"),
                    ("Cassandra", "Recommended", "Intermediate"),
                ]
            },
            # 28
            {
                "title": "Enterprise Java Solutions Architect",
                "category": "Enterprise Software",
                "description": "Architects resilient, multi-tiered enterprise backend applications utilizing Java 21+, Spring Boot, Hibernate, and cloud microservices.",
                "salary": "$120,000 - $175,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-mug-hot",
                "skills": [
                    ("Java", "Critical", "Advanced"),
                    ("Spring Boot", "Critical", "Advanced"),
                    ("SQL & Relational Databases", "Critical", "Advanced"),
                    ("REST APIs", "Critical", "Advanced"),
                    ("Docker", "Critical", "Intermediate"),
                    ("Microservices Architecture", "Critical", "Advanced"),
                    ("Kafka & Message Queues", "Recommended", "Intermediate"),
                ]
            },
            # 29
            {
                "title": "Microservices & API Platform Engineer",
                "category": "Software Engineering",
                "description": "Engineers high-throughput API gateways, service meshes (Istio), GraphQL federation, and inter-service authentication fabrics.",
                "salary": "$115,000 - $170,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-arrows-split-up-and-left",
                "skills": [
                    ("Go (Golang)", "Critical", "Advanced"),
                    ("REST APIs", "Critical", "Advanced"),
                    ("GraphQL", "Critical", "Advanced"),
                    ("gRPC & Protocol Buffers", "Critical", "Advanced"),
                    ("Kubernetes", "Critical", "Intermediate"),
                    ("Docker", "Critical", "Advanced"),
                ]
            },
            # 30
            {
                "title": "Autonomous Systems & Robotics Engineer",
                "category": "Robotics & IoT",
                "description": "Programs perception algorithms, path-planning nodes, and actuator controls for autonomous mobile robots and unmanned aerial vehicles.",
                "salary": "$110,000 - $170,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-robot",
                "skills": [
                    ("ROS (Robot Operating System)", "Critical", "Advanced"),
                    ("C++ Programming", "Critical", "Advanced"),
                    ("Python", "Critical", "Advanced"),
                    ("Computer Vision", "Critical", "Intermediate"),
                    ("Linux Administration", "Critical", "Intermediate"),
                ]
            },
            # 31
            {
                "title": "Business Intelligence (BI) & Analytics Engineer",
                "category": "AI & Data Science",
                "description": "Transforms raw enterprise data into actionable visual executive dashboards, automated metric forecasts, and semantic BI models.",
                "salary": "$85,000 - $135,000 / yr",
                "demand": "High",
                "difficulty": "Beginner-friendly",
                "icon": "fa-chart-column",
                "skills": [
                    ("SQL & Relational Databases", "Critical", "Advanced"),
                    ("Data Visualization", "Critical", "Advanced"),
                    ("Pandas & NumPy", "Critical", "Intermediate"),
                    ("Snowflake & dbt", "Critical", "Intermediate"),
                    ("Python", "Recommended", "Intermediate"),
                ]
            },
            # 32
            {
                "title": "Security Operations Center (SOC) Analyst",
                "category": "Security & Defense",
                "description": "Monitors security telemetry 24/7, analyzes suspicious log events, investigates malware intrusions, and triages threat vectors.",
                "salary": "$80,000 - $130,000 / yr",
                "demand": "Very High",
                "difficulty": "Intermediate",
                "icon": "fa-tower-observation",
                "skills": [
                    ("SIEM & Threat Hunting", "Critical", "Advanced"),
                    ("Network Security", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Intermediate"),
                    ("Python", "Recommended", "Intermediate"),
                    ("OWASP Top 10", "Recommended", "Intermediate"),
                ]
            },
            # 33
            {
                "title": "Prompt Engineer & AI Interaction Designer",
                "category": "AI & Data Science",
                "description": "Designs robust prompt chains, multi-turn system instructions, few-shot evaluations, and guardrail architectures for foundation models.",
                "salary": "$95,000 - $150,000 / yr",
                "demand": "Extremely High",
                "difficulty": "Intermediate",
                "icon": "fa-wand-magic-sparkles",
                "skills": [
                    ("Prompt Engineering & LangChain", "Critical", "Advanced"),
                    ("Generative AI & LLMs", "Critical", "Advanced"),
                    ("Python", "Critical", "Intermediate"),
                    ("Natural Language Processing", "Recommended", "Intermediate"),
                    ("Vector Databases & Pinecone", "Recommended", "Intermediate"),
                ]
            },
            # 34
            {
                "title": "Quantum Computing Software Researcher",
                "category": "Emerging Tech & Research",
                "description": "Designs quantum gate algorithms, error mitigation techniques, and hybrid quantum-classical optimization programs using Qiskit.",
                "salary": "$130,000 - $200,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-atom",
                "skills": [
                    ("Quantum Computing & Qiskit", "Critical", "Advanced"),
                    ("Python", "Critical", "Advanced"),
                    ("Pandas & NumPy", "Critical", "Advanced"),
                    ("C++ Programming", "Recommended", "Intermediate"),
                ]
            },
            # 35
            {
                "title": "Digital Forensics & Incident Response (DFIR) Specialist",
                "category": "Security & Defense",
                "description": "Investigates cyber breaches, extracts memory artifacts, performs disk forensics, and drafts legally admissible incident reports.",
                "salary": "$105,000 - $165,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-magnifying-glass-chart",
                "skills": [
                    ("Reverse Engineering & Malware Analysis", "Critical", "Advanced"),
                    ("Network Security", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Advanced"),
                    ("Python", "Critical", "Intermediate"),
                    ("Cryptography", "Recommended", "Intermediate"),
                ]
            },
            # 36
            {
                "title": "Linux Kernel & Low-Level Firmware Developer",
                "category": "Hardware & Systems",
                "description": "Develops Linux kernel device drivers, memory management subsystems, bootloaders (U-Boot), and board support packages (BSP).",
                "salary": "$120,000 - $180,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-terminal",
                "skills": [
                    ("C++ Programming", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Advanced"),
                    ("Rust Programming", "Critical", "Intermediate"),
                    ("Embedded C & Microcontrollers", "Critical", "Advanced"),
                ]
            },
            # 37
            {
                "title": "FinTech & Algorithmic Trading Systems Engineer",
                "category": "Financial Engineering",
                "description": "Engineers nanosecond-latency order routing engines, market data feed handlers, risk validation engines, and quantitative trading systems.",
                "salary": "$140,000 - $230,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-money-bill-trend-up",
                "skills": [
                    ("C++ Programming", "Critical", "Advanced"),
                    ("FinTech & FIX Protocol", "Critical", "Advanced"),
                    ("Python", "Critical", "Advanced"),
                    ("SQL & Relational Databases", "Critical", "Advanced"),
                    ("Linux Administration", "Critical", "Advanced"),
                ]
            },
            # 38
            {
                "title": "Bioinformatics & HealthTech Data Scientist",
                "category": "Health & MedTech",
                "description": "Analyzes genomic sequences, performs molecular modeling, and trains deep learning models on clinical biomarker datasets.",
                "salary": "$100,000 - $155,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-dna",
                "skills": [
                    ("Bioinformatics & Biopython", "Critical", "Advanced"),
                    ("Python", "Critical", "Advanced"),
                    ("Pandas & NumPy", "Critical", "Advanced"),
                    ("Machine Learning", "Critical", "Intermediate"),
                    ("Deep Learning", "Recommended", "Intermediate"),
                ]
            },
            # 39
            {
                "title": "Golang Cloud-Native Microservices Engineer",
                "category": "Software Engineering",
                "description": "Builds concurrent, lightweight microservices in Go, writing Kubernetes operators and high-throughput background processing workers.",
                "salary": "$115,000 - $170,000 / yr",
                "demand": "Very High",
                "difficulty": "Intermediate",
                "icon": "fa-feather",
                "skills": [
                    ("Go (Golang)", "Critical", "Advanced"),
                    ("Docker", "Critical", "Advanced"),
                    ("Kubernetes", "Critical", "Advanced"),
                    ("REST APIs", "Critical", "Advanced"),
                    ("PostgreSQL", "Critical", "Intermediate"),
                    ("gRPC & Protocol Buffers", "Critical", "Intermediate"),
                ]
            },
            # 40
            {
                "title": "Cloud Network & Infrastructure Architect",
                "category": "Cloud & Infrastructure",
                "description": "Designs hybrid-cloud VPC topologies, software-defined WANs, transit gateways, and multi-region failover network routing.",
                "salary": "$125,000 - $185,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-globe",
                "skills": [
                    ("AWS Cloud", "Critical", "Advanced"),
                    ("Google Cloud Platform", "Critical", "Advanced"),
                    ("Microsoft Azure", "Critical", "Intermediate"),
                    ("Network Security", "Critical", "Advanced"),
                    ("Terraform / IaC", "Critical", "Advanced"),
                ]
            },
            # 41
            {
                "title": "Application Security (AppSec) Engineer",
                "category": "Security & Defense",
                "description": "Performs secure code reviews (SAST/DAST), conducts threat modeling sessions with engineering teams, and patches critical web vulnerabilities.",
                "salary": "$110,000 - $170,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-shield-halved",
                "skills": [
                    ("Web Application Security", "Critical", "Advanced"),
                    ("OWASP Top 10", "Critical", "Advanced"),
                    ("Python", "Critical", "Intermediate"),
                    ("JavaScript", "Critical", "Intermediate"),
                    ("CI/CD Pipelines", "Critical", "Intermediate"),
                ]
            },
            # 42
            {
                "title": "Product Analytics & Growth Data Engineer",
                "category": "Data & Business Intelligence",
                "description": "Instruments event tracking pipelines (Segment), designs A/B experimentation frameworks, and models user retention cohorts.",
                "salary": "$95,000 - $145,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-arrow-trend-up",
                "skills": [
                    ("SQL & Relational Databases", "Critical", "Advanced"),
                    ("Python", "Critical", "Advanced"),
                    ("Data Visualization", "Critical", "Advanced"),
                    ("Snowflake & dbt", "Critical", "Intermediate"),
                    ("Product Roadmap & Strategy", "Recommended", "Intermediate"),
                ]
            },
            # 43
            {
                "title": "Geospatial Data Scientist & GIS Developer",
                "category": "Spatial & Geospatial",
                "description": "Processes satellite raster datasets, builds spatial indexing queries with PostGIS, and visualizes interactive map applications.",
                "salary": "$90,000 - $145,000 / yr",
                "demand": "Moderate",
                "difficulty": "Intermediate",
                "icon": "fa-map-location-dot",
                "skills": [
                    ("GIS & Spatial Analysis", "Critical", "Advanced"),
                    ("Python", "Critical", "Advanced"),
                    ("PostgreSQL", "Critical", "Advanced"),
                    ("Data Visualization", "Critical", "Intermediate"),
                ]
            },
            # 44
            {
                "title": "Search & Recommendation Systems Engineer",
                "category": "AI & Information Retrieval",
                "description": "Builds personalized recommendation engines, vector search ranking algorithms, and BM25/hybrid search indexing with Elasticsearch.",
                "salary": "$125,000 - $185,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-magnifying-glass",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("Elasticsearch", "Critical", "Advanced"),
                    ("Vector Databases & Pinecone", "Critical", "Advanced"),
                    ("Machine Learning", "Critical", "Advanced"),
                    ("Deep Learning", "Recommended", "Intermediate"),
                ]
            },
            # 45
            {
                "title": "Web3 DeFi & Smart Contract Auditor",
                "category": "Web3 & Decentralized Systems",
                "description": "Performs formal verification and vulnerability audits on multi-million dollar liquidity pools, lending protocols, and DAO governance contracts.",
                "salary": "$130,000 - $210,000 / yr",
                "demand": "High",
                "difficulty": "Advanced",
                "icon": "fa-file-shield",
                "skills": [
                    ("Smart Contract Auditing", "Critical", "Advanced"),
                    ("Solidity", "Critical", "Advanced"),
                    ("Ethereum & Web3.js", "Critical", "Advanced"),
                    ("Cryptography", "Critical", "Advanced"),
                    ("Web Application Security", "Critical", "Advanced"),
                ]
            },
            # 46
            {
                "title": "Game Engine & 3D Graphics Programmer",
                "category": "Interactive Entertainment",
                "description": "Develops real-time rendering pipelines, ray-tracing shaders, physics collision solvers, and spatial scene graphs in C++ and Vulkan/DirectX.",
                "salary": "$110,000 - $165,000 / yr",
                "demand": "Moderate",
                "difficulty": "Advanced",
                "icon": "fa-cube",
                "skills": [
                    ("C++ Programming", "Critical", "Advanced"),
                    ("Unreal Engine & C++", "Critical", "Advanced"),
                    ("Shader Programming (GLSL/HLSL)", "Critical", "Advanced"),
                    ("Git & GitHub", "Critical", "Intermediate"),
                ]
            },
            # 47
            {
                "title": "Healthcare & Clinical Informatics Software Engineer",
                "category": "Health & MedTech",
                "description": "Builds HIPAA-compliant medical software, FHIR/HL7 data exchange bridges, electronic health record (EHR) integrations, and clinical workflows.",
                "salary": "$100,000 - $155,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-heart-pulse",
                "skills": [
                    ("Python", "Critical", "Advanced"),
                    ("REST APIs", "Critical", "Advanced"),
                    ("SQL & Relational Databases", "Critical", "Advanced"),
                    ("Web Application Security", "Critical", "Advanced"),
                    ("PostgreSQL", "Recommended", "Intermediate"),
                ]
            },
            # 48
            {
                "title": "Edge AI & TinyML Embedded Engineer",
                "category": "AI & Hardware",
                "description": "Quantizes neural networks to run on resource-constrained microcontrollers, wearable devices, and smart sensors with micro-watt power consumption.",
                "salary": "$115,000 - $170,000 / yr",
                "demand": "Very High",
                "difficulty": "Advanced",
                "icon": "fa-microchip",
                "skills": [
                    ("Embedded C & Microcontrollers", "Critical", "Advanced"),
                    ("TensorFlow", "Critical", "Advanced"),
                    ("PyTorch", "Critical", "Intermediate"),
                    ("C++ Programming", "Critical", "Advanced"),
                    ("Python", "Critical", "Intermediate"),
                ]
            },
            # 49
            {
                "title": "Design Systems & Frontend Platform Lead",
                "category": "Design & User Experience",
                "description": "Builds accessible, tokenized multi-brand component architectures in Figma and code, driving unified frontend standards across cross-functional squads.",
                "salary": "$115,000 - $165,000 / yr",
                "demand": "High",
                "difficulty": "Intermediate",
                "icon": "fa-shapes",
                "skills": [
                    ("Figma", "Critical", "Advanced"),
                    ("Design Systems", "Critical", "Advanced"),
                    ("TypeScript", "Critical", "Advanced"),
                    ("React", "Critical", "Advanced"),
                    ("CSS3", "Critical", "Advanced"),
                    ("Tailwind CSS", "Critical", "Advanced"),
                ]
            },
            # 50
            {
                "title": "Platform Engineering & Developer Experience (DevEx) Lead",
                "category": "Software Engineering",
                "description": "Constructs internal developer platforms (IDP), automated local dev environments, self-service CI workflows, and high-velocity build pipelines.",
                "salary": "$125,000 - $185,000 / yr",
                "demand": "Extremely High",
                "difficulty": "Advanced",
                "icon": "fa-rocket",
                "skills": [
                    ("Developer Experience & Tooling", "Critical", "Advanced"),
                    ("Kubernetes", "Critical", "Advanced"),
                    ("Docker", "Critical", "Advanced"),
                    ("CI/CD Pipelines", "Critical", "Advanced"),
                    ("Terraform / IaC", "Critical", "Advanced"),
                    ("Go (Golang)", "Critical", "Intermediate"),
                    ("Python", "Critical", "Intermediate"),
                ]
            }
        ]

        career_objs = {}
        for cdata in careers_data:
            crole = CareerRole(
                title=cdata["title"],
                category=cdata["category"],
                description=cdata["description"],
                average_salary=cdata["salary"],
                market_demand=cdata["demand"],
                difficulty=cdata["difficulty"],
                icon=cdata["icon"]
            )
            db.session.add(crole)
            db.session.flush()
            career_objs[cdata["title"]] = crole

            # Add skill requirements
            for skill_name, importance, target_prof in cdata["skills"]:
                if skill_name in skill_map:
                    weight_val = 3 if importance == "Critical" else (2 if importance == "Recommended" else 1)
                    req = CareerSkillRequirement(
                        career_id=crole.id,
                        skill_id=skill_map[skill_name].id,
                        importance=importance,
                        target_proficiency=target_prof,
                        weight=weight_val
                    )
                    db.session.add(req)

        db.session.flush()

        # 4. Seed Learning Resources for Popular Roles
        resources_data = [
            (career_objs["Full Stack Web Developer"].id, skill_map["JavaScript"].id, "JavaScript: The Definitive Guide (MDN Docs)", "Documentation", "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "Mozilla MDN", True, "Beginner", "Official and comprehensive JavaScript reference."),
            (career_objs["Full Stack Web Developer"].id, skill_map["React"].id, "React Official Interactive Tutorial", "Documentation", "https://react.dev/learn", "React Core Team", True, "Intermediate", "Step-by-step interactive documentation for modern React."),
            (career_objs["Full Stack Web Developer"].id, skill_map["Flask"].id, "Flask Mega-Tutorial by Miguel Grinberg", "Course", "https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world", "Miguel Grinberg", True, "Intermediate", "The gold standard full-stack tutorial for building production-ready Flask apps."),
            (career_objs["Full Stack Web Developer"].id, skill_map["SQL & Relational Databases"].id, "SQLZoo Interactive SQL Tutorial", "Interactive", "https://sqlzoo.net/", "SQLZoo", True, "Beginner", "Hands-on browser-based SQL exercises with real queries."),
            
            (career_objs["AI & Machine Learning Engineer"].id, skill_map["Machine Learning"].id, "Machine Learning Specialization by Andrew Ng", "Course", "https://www.coursera.org/specializations/machine-learning-introduction", "DeepLearning.AI / Coursera", False, "Intermediate", "The world's most renowned introduction to machine learning principles and algorithms."),
            (career_objs["AI & Machine Learning Engineer"].id, skill_map["PyTorch"].id, "Deep Learning with PyTorch: A 60 Minute Blitz", "Documentation", "https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html", "PyTorch Core", True, "Beginner", "Official fast-track tutorial to PyTorch tensors and neural networks."),
            (career_objs["Generative AI & LLM Solutions Engineer"].id, skill_map["Generative AI & LLMs"].id, "Generative AI for Everyone by Andrew Ng", "Course", "https://www.coursera.org/learn/generative-ai-for-everyone", "DeepLearning.AI", True, "Beginner", "Comprehensive overview of LLM architectures and prompt capabilities."),
            (career_objs["Cloud & DevOps Engineer"].id, skill_map["Docker"].id, "Docker for Absolute Beginners", "Video", "https://www.youtube.com/watch?v=fqMOX6JJhGo", "freeCodeCamp", True, "Beginner", "Full hands-on video crash course in containerizing applications."),
            (career_objs["Cloud & DevOps Engineer"].id, skill_map["Kubernetes"].id, "Kubernetes The Hard Way", "Documentation", "https://github.com/kelseyhightower/kubernetes-the-hard-way", "Kelsey Hightower", True, "Advanced", "Deep dive into bootstrapping Kubernetes clusters from scratch."),
            (career_objs["Cybersecurity Analyst"].id, skill_map["Web Application Security"].id, "PortSwigger Web Security Academy", "Interactive", "https://portswigger.net/web-security", "PortSwigger", True, "Intermediate", "Free interactive labs on SQL injection, XSS, and CSRF."),
            (career_objs["Frontend Architect & Modern UI Engineer"].id, skill_map["Next.js"].id, "Next.js Official Interactive Course", "Course", "https://nextjs.org/learn", "Vercel", True, "Intermediate", "Official Vercel interactive course for App Router and SSR."),
            (career_objs["Backend & Distributed Systems Engineer"].id, skill_map["Go (Golang)"].id, "A Tour of Go", "Interactive", "https://go.dev/tour/", "Go Team", True, "Beginner", "Official interactive tutorial covering Go fundamentals, goroutines, and channels."),
            (career_objs["Autonomous Systems & Robotics Engineer"].id, skill_map["ROS (Robot Operating System)"].id, "ROS 2 Official Documentation and Tutorials", "Documentation", "https://docs.ros.org/en/humble/", "Open Robotics", True, "Intermediate", "Comprehensive guide to robotics middleware, node communication, and topics.")
        ]

        for rdata in resources_data:
            res = LearningResource(
                career_id=rdata[0],
                skill_id=rdata[1],
                title=rdata[2],
                resource_type=rdata[3],
                url=rdata[4],
                provider=rdata[5],
                is_free=rdata[6],
                difficulty=rdata[7],
                description=rdata[8]
            )
            db.session.add(res)

        # 5. Seed Certifications
        certs_data = [
            (career_objs["Cloud & DevOps Engineer"].id, "AWS Certified Solutions Architect - Associate", "Amazon Web Services", "https://aws.amazon.com/certification/certified-solutions-architect-associate/", "Paid ($150)", "Intermediate", "Validates expertise in designing highly available, cost-effective AWS systems."),
            (career_objs["Cloud & DevOps Engineer"].id, "Certified Kubernetes Administrator (CKA)", "Cloud Native Computing Foundation (CNCF)", "https://www.cncf.io/certification/cka/", "Paid ($395)", "Advanced", "Industry-standard performance-based certification for administering K8s clusters."),
            (career_objs["Cybersecurity Analyst"].id, "CompTIA Security+ (SY0-701)", "CompTIA", "https://www.comptia.org/certifications/security", "Paid ($392)", "Beginner", "Baseline cybersecurity certification validating core security knowledge."),
            (career_objs["AI & Machine Learning Engineer"].id, "Google Cloud Professional Machine Learning Engineer", "Google Cloud", "https://cloud.google.com/learn/certification/machine-learning-engineer", "Paid ($200)", "Advanced", "Validates ability to design, build, and productionize ML models on GCP."),
            (career_objs["MLOps & AI Infrastructure Engineer"].id, "AWS Certified Machine Learning - Specialty", "Amazon Web Services", "https://aws.amazon.com/certification/certified-machine-learning-specialty/", "Paid ($300)", "Advanced", "Validates expertise in architecting and deploying production ML on AWS."),
            (career_objs["Penetration Tester & Ethical Hacker"].id, "OffSec Certified Professional (OSCP)", "OffSec", "https://www.offsec.com/courses/pen-200/", "Paid ($1600)", "Advanced", "The gold-standard hands-on penetration testing and ethical hacking certification.")
        ]

        for c in certs_data:
            cert = Certification(
                career_id=c[0],
                name=c[1],
                issuer=c[2],
                url=c[3],
                cost_type=c[4],
                difficulty=c[5],
                description=c[6]
            )
            db.session.add(cert)

        # 6. Seed Project Ideas
        projects_data = [
            (
                career_objs["Full Stack Web Developer"].id,
                "Real-Time Collaborative Markdown Workspace",
                "Full stack collaborative workspace with live WebSocket editing, authentication, and revision history.",
                "Intermediate",
                "Python, Flask, React, WebSockets, PostgreSQL, Tailwind CSS",
                json.dumps([
                    "Design schema for users, documents, and real-time operational transformation events.",
                    "Implement Flask backend with JWT auth and WebSocket broadcast channels.",
                    "Build responsive React frontend with live markdown rendering and syntax highlighting.",
                    "Deploy to Docker container with persistent PostgreSQL database."
                ])
            ),
            (
                career_objs["AI & Machine Learning Engineer"].id,
                "End-to-End Multimodal Medical Imaging Classifier",
                "Deep learning computer vision system to detect anomalies from chest X-ray images with Grad-CAM visual heatmaps.",
                "Capstone",
                "PyTorch, Torchvision, FastAPI, Docker, Streamlit",
                json.dumps([
                    "Preprocess and augment Kaggle NIH Chest X-ray dataset with PyTorch data loaders.",
                    "Fine-tune ResNet-50 / DenseNet architecture with focal loss for class imbalance.",
                    "Generate Grad-CAM explainability heatmaps visualizing model attention.",
                    "Wrap in high-throughput FastAPI endpoint and build interactive Streamlit dashboard."
                ])
            ),
            (
                career_objs["Generative AI & LLM Solutions Engineer"].id,
                "Enterprise Knowledge RAG Agent with Semantic Search",
                "Retrieval-Augmented Generation agent capable of parsing corporate PDFs, embedding with HuggingFace, and querying with LangChain.",
                "Advanced",
                "Python, LangChain, Pinecone, FastAPI, OpenAI / Gemini API",
                json.dumps([
                    "Build document ingestion pipeline with recursive character text splitters.",
                    "Store and index high-dimensional embeddings in Pinecone vector index.",
                    "Implement hybrid keyword + dense vector search retrieval with re-ranking.",
                    "Construct conversational memory agent with source citation badges."
                ])
            )
        ]

        for p in projects_data:
            proj = ProjectIdea(
                career_id=p[0],
                title=p[1],
                description=p[2],
                difficulty=p[3],
                tech_stack=p[4],
                milestones_json=p[5]
            )
            db.session.add(proj)

        # 7. Seed Student Demo Skills & Initial Target Career
        demo_student.target_career_id = career_objs["Full Stack Web Developer"].id
        db.session.add(demo_student)
        
        student_skills = [
            ("HTML5", "Advanced", 1.5),
            ("CSS3", "Intermediate", 1.0),
            ("JavaScript", "Intermediate", 1.0),
            ("Python", "Intermediate", 1.0),
            ("Flask", "Beginner", 0.5),
            ("SQL & Relational Databases", "Beginner", 0.5),
            ("Git & GitHub", "Intermediate", 1.0)
        ]

        for sname, prof, yrs in student_skills:
            if sname in skill_map:
                us = UserSkill(
                    user_id=demo_student.id,
                    skill_id=skill_map[sname].id,
                    proficiency=prof,
                    years_experience=yrs
                )
                db.session.add(us)

        # Seed student initial roadmap progress
        demo_roadmap = UserRoadmapProgress(
            user_id=demo_student.id,
            career_id=career_objs["Full Stack Web Developer"].id,
            completed_milestones_json=json.dumps([
                "Master core syntax, design patterns, and environment setup for HTML5, CSS3, JavaScript.",
                "Complete official documentation tutorials and 10+ hands-on coding challenges."
            ]),
            progress_percentage=25.0,
            notes="Completed basic frontend milestones. Focusing on Flask backend next!"
        )
        db.session.add(demo_roadmap)

        # Seed student daily log
        demo_log = DailyLog(
            user_id=demo_student.id,
            date=date.today(),
            hours_spent=2.5,
            topic_studied="Flask routing and MongoDB document modeling",
            notes="Created User and Skill models with document relationships in MongoDB."
        )
        db.session.add(demo_log)

        db.session.commit()
        print("Database seeded successfully with 50 careers, 100+ skills, resources, and demo data!")


if __name__ == '__main__':
    from flask import Flask
    from config import Config
    
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    seed_database(app, force=True)
