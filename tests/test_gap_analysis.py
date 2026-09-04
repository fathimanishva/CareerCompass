import unittest
from app import create_app
from config import Config
from models import db, User, Skill, UserSkill, CareerRole, CareerSkillRequirement
from services.gap_analyzer import analyze_skill_gap, find_top_career_matches

class TestConfig(Config):
    TESTING = True
    MONGO_URI = 'mongomock://localhost:27017/test_gap_analysis'
    MONGO_DB_NAME = 'test_gap_analysis'
    WTF_CSRF_ENABLED = False

class GapAnalysisTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test skills
        self.s_python = Skill(name='Python', category='Backend', description='Python lang')
        self.s_flask = Skill(name='Flask', category='Backend', description='Flask web')
        self.s_react = Skill(name='React', category='Frontend', description='React UI')
        self.s_docker = Skill(name='Docker', category='DevOps', description='Docker containers')
        db.session.add_all([self.s_python, self.s_flask, self.s_react, self.s_docker])
        db.session.commit()

        # Create test career
        self.career = CareerRole(
            title='Test Full Stack Engineer',
            category='Software Engineering',
            description='Test engineering role'
        )
        db.session.add(self.career)
        db.session.commit()

        # Add requirements
        req1 = CareerSkillRequirement(
            career_id=self.career.id, skill_id=self.s_python.id,
            importance='Critical', target_proficiency='Advanced', weight=3
        )
        req2 = CareerSkillRequirement(
            career_id=self.career.id, skill_id=self.s_flask.id,
            importance='Critical', target_proficiency='Intermediate', weight=3
        )
        req3 = CareerSkillRequirement(
            career_id=self.career.id, skill_id=self.s_react.id,
            importance='Recommended', target_proficiency='Intermediate', weight=2
        )
        req4 = CareerSkillRequirement(
            career_id=self.career.id, skill_id=self.s_docker.id,
            importance='Optional', target_proficiency='Beginner', weight=1
        )
        db.session.add_all([req1, req2, req3, req4])
        db.session.commit()

        # Create user
        self.user = User(full_name='Test Student', email='test@student.com')
        self.user.set_password('Pass@123')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_zero_skills_gap(self):
        """User with no skills should have 0% match score."""
        analysis = analyze_skill_gap(self.user, self.career)
        self.assertEqual(analysis['match_score'], 0.0)
        self.assertEqual(len(analysis['matched_skills']), 0)
        self.assertEqual(len(analysis['missing_critical_skills']), 2)
        self.assertEqual(len(analysis['missing_recommended_skills']), 1)
        self.assertEqual(len(analysis['missing_optional_skills']), 1)

    def test_partial_skills_gap(self):
        """User with Python (Advanced) and Flask (Intermediate) should match critical weight."""
        us1 = UserSkill(user_id=self.user.id, skill_id=self.s_python.id, proficiency='Advanced')
        us2 = UserSkill(user_id=self.user.id, skill_id=self.s_flask.id, proficiency='Intermediate')
        db.session.add_all([us1, us2])
        db.session.commit()

        analysis = analyze_skill_gap(self.user, self.career)
        # Total weight = 3*1 + 3*1 + 2*1 + 1*1 = 9
        # Earned = 3*1.0 + 3*0.8 = 3.0 + 2.4 = 5.4
        # Expected % = (5.4 / 9) * 100 = 60.0%
        self.assertAlmostEqual(analysis['match_score'], 60.0, places=1)
        self.assertEqual(len(analysis['matched_skills']), 2)
        self.assertEqual(len(analysis['missing_critical_skills']), 0)
        self.assertEqual(len(analysis['missing_recommended_skills']), 1)

    def test_career_matcher_ranking(self):
        """Find top matches should rank career with higher match first."""
        us1 = UserSkill(user_id=self.user.id, skill_id=self.s_python.id, proficiency='Advanced')
        db.session.add(us1)
        db.session.commit()

        rankings = find_top_career_matches(self.user)
        self.assertTrue(len(rankings) >= 1)
        self.assertEqual(rankings[0]['career'].id, self.career.id)

if __name__ == '__main__':
    unittest.main()
