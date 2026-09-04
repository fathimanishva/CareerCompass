import unittest
from app import create_app
from config import Config
from models import db, User, CareerRole
from seed_data import seed_database

class TestConfig(Config):
    TESTING = True
    MONGO_URI = 'mongomock://localhost:27017/test_career_compass'
    MONGO_DB_NAME = 'test_career_compass'
    WTF_CSRF_ENABLED = False

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        seed_database(self.app)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CareerCompass', response.data)
        self.assertIn(b'Bridge the Gap', response.data)

    def test_careers_page(self):
        response = self.client.get('/careers')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Full Stack Web Developer', response.data)

    def test_auth_login_student(self):
        # Login with seeded demo student
        response = self.client.post('/auth/login', data={
            'email': 'student@careercompass.com',
            'password': 'Student@123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Fathima Nishva', response.data)
        self.assertIn(b'Student Portal', response.data)

    def test_auth_login_admin(self):
        # Login with seeded admin
        response = self.client.post('/auth/login', data={
            'email': 'admin@careercompass.com',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    def test_career_detail_page(self):
        career = CareerRole.query.first()
        self.assertIsNotNone(career)
        response = self.client.get(f'/careers/{career.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(career.title.encode(), response.data)

    def test_student_dashboard_authenticated(self):
        self.client.post('/auth/login', data={
            'email': 'student@careercompass.com',
            'password': 'Student@123'
        }, follow_redirects=True)

        response = self.client.get('/student/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Portal', response.data)
        self.assertIn(b'Fathima Nishva', response.data)

    def test_student_gap_analysis(self):
        self.client.post('/auth/login', data={
            'email': 'student@careercompass.com',
            'password': 'Student@123'
        }, follow_redirects=True)

        career = CareerRole.query.first()
        response = self.client.get(f'/student/gap-analysis/{career.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Skill Gap Analysis', response.data)

    def test_student_roadmap(self):
        self.client.post('/auth/login', data={
            'email': 'student@careercompass.com',
            'password': 'Student@123'
        }, follow_redirects=True)

        career = CareerRole.query.first()
        response = self.client.get(f'/student/roadmap/{career.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Phased Milestone Roadmap', response.data)

    def test_admin_dashboard_authenticated(self):
        self.client.post('/auth/login', data={
            'email': 'admin@careercompass.com',
            'password': 'Admin@123'
        }, follow_redirects=True)

        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Administrator Control Center', response.data)
        self.assertIn(b'Platform Overview & Metrics', response.data)

    def test_admin_skills_crud(self):
        self.client.post('/auth/login', data={
            'email': 'admin@careercompass.com',
            'password': 'Admin@123'
        }, follow_redirects=True)

        # Create new skill
        res = self.client.post('/admin/skills', data={
            'name': 'MongoDB Database',
            'category': 'Database',
            'description': 'NoSQL document-oriented database system'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'MongoDB Database', res.data)

if __name__ == '__main__':
    unittest.main()

