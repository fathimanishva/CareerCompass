import re
from pypdf import PdfReader
from models import Skill

# Common skill alias mapping
SKILL_ALIASES = {
    'js': 'JavaScript',
    'ts': 'TypeScript',
    'py': 'Python',
    'python3': 'Python',
    'react.js': 'React',
    'reactjs': 'React',
    'vue.js': 'Vue.js',
    'vuejs': 'Vue.js',
    'node.js': 'Node.js',
    'nodejs': 'Node.js',
    'express.js': 'Express.js',
    'expressjs': 'Express.js',
    'postgres': 'PostgreSQL',
    'k8s': 'Kubernetes',
    'aws': 'AWS Cloud',
    'gcp': 'Google Cloud Platform',
    'ml': 'Machine Learning',
    'dl': 'Deep Learning',
    'nlp': 'Natural Language Processing',
    'cv': 'Computer Vision',
    'ai': 'Artificial Intelligence',
    'html5': 'HTML5',
    'css3': 'CSS3',
    'ci/cd': 'CI/CD Pipelines',
    'cicd': 'CI/CD Pipelines'
}

def extract_text_from_file(file_path):
    """Extract raw text from a PDF, TXT or DOCX file."""
    text = ""
    if file_path.lower().endswith('.pdf'):
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
    else:
        # Plain text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            
    return text


def extract_skills_from_text(raw_text):
    """
    Scans raw text against the Skill database and alias map.
    Returns:
    {
        'matched_skills': [Skill, ...],
        'extracted_names': [str, ...],
        'summary': str
    }
    """
    all_skills = Skill.query.all()
    matched_skills = []
    matched_ids = set()
    
    # Lowercase text and normalize whitespace
    cleaned_text = " " + re.sub(r'[^a-zA-Z0-9\+\#\.\/]', ' ', raw_text.lower()) + " "
    
    for skill in all_skills:
        skill_name_lower = skill.name.lower()
        # Create pattern for exact word boundary match
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill_name_lower) + r'(?![a-zA-Z0-9])'
        
        if re.search(pattern, cleaned_text):
            if skill.id not in matched_ids:
                matched_ids.add(skill.id)
                matched_skills.append(skill)
                continue
                
    # Also check aliases
    for alias, standard_name in SKILL_ALIASES.items():
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(alias) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, cleaned_text):
            matched_skill = Skill.query.filter(Skill.name.ilike(f"%{standard_name}%")).first()
            if matched_skill and matched_skill.id not in matched_ids:
                matched_ids.add(matched_skill.id)
                matched_skills.append(matched_skill)
                
    return {
        'matched_skills': matched_skills,
        'extracted_names': [s.name for s in matched_skills],
        'total_found': len(matched_skills)
    }
