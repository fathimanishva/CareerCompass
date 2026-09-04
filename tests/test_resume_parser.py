import unittest
from app import create_app
from config import Config
from models import db, Skill
from services.resume_parser import extract_skills_from_text

class TestConfig(Config):
    TESTING = True
    MONGO_URI = 'mongomock://localhost:27017/test_resume_parser'
    MONGO_DB_NAME = 'test_resume_parser'

class ResumeParserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed some skills
        skills = [
            Skill(name='Python', category='Backend'),
            Skill(name='Flask', category='Backend'),
            Skill(name='JavaScript', category='Frontend'),
            Skill(name='React', category='Frontend'),
            Skill(name='Docker', category='DevOps'),
            Skill(name='AWS Cloud', category='Cloud'),
            Skill(name='PostgreSQL', category='Database')
        ]
        db.session.add_all(skills)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_extract_skills_from_resume_text(self):
        sample_resume = """
        John Doe - Software Engineer
        Proficient in Python, Flask web framework, and JavaScript with React.
        Experienced deploying containerized microservices using Docker and AWS.
        Database expertise includes PostgreSQL and SQL optimization.
        """
        result = extract_skills_from_text(sample_resume)
        extracted_names = result['extracted_names']
        
        self.assertIn('Python', extracted_names)
        self.assertIn('Flask', extracted_names)
        self.assertIn('JavaScript', extracted_names)
        self.assertIn('React', extracted_names)
        self.assertIn('Docker', extracted_names)
        self.assertIn('PostgreSQL', extracted_names)
        self.assertTrue(result['total_found'] >= 5)

if __name__ == '__main__':
    unittest.main()
