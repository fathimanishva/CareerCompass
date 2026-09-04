import json
import re
from datetime import datetime, timezone, date
from flask import abort, current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo
import mongomock


def utc_now():
    return datetime.now(timezone.utc)


class FieldExpression:
    def __init__(self, field_name, op='$eq', value=None, mongo_filter=None):
        self.field_name = field_name
        self.op = op
        self.value = value
        self.mongo_filter = mongo_filter

    def to_mongo(self):
        if self.mongo_filter is not None:
            return self.mongo_filter
        if self.op == '$eq':
            return {self.field_name: self.value}
        return {self.field_name: {self.op: self.value}}

    def __or__(self, other):
        if other is False or other is None:
            return self
        if other is True:
            return True
        if self is False:
            return other
        f1 = self.to_mongo() if isinstance(self, FieldExpression) else (self if isinstance(self, dict) else {})
        f2 = other.to_mongo() if isinstance(other, FieldExpression) else (other if isinstance(other, dict) else {})
        
        if not f1:
            return other if isinstance(other, FieldExpression) else FieldExpression('', mongo_filter=f2)
        if not f2:
            return self

        # Merge or conditions
        if '$or' in f1 and '$or' in f2:
            return FieldExpression('', mongo_filter={'$or': f1['$or'] + f2['$or']})
        elif '$or' in f1:
            return FieldExpression('', mongo_filter={'$or': f1['$or'] + [f2]})
        elif '$or' in f2:
            return FieldExpression('', mongo_filter={'$or': [f1] + f2['$or']})
        else:
            return FieldExpression('', mongo_filter={'$or': [f1, f2]})

    def __ror__(self, other):
        return self.__or__(other)

    def __and__(self, other):
        if other is True or other is None:
            return self
        if other is False:
            return False
        f1 = self.to_mongo() if isinstance(self, FieldExpression) else (self if isinstance(self, dict) else {})
        f2 = other.to_mongo() if isinstance(other, FieldExpression) else (other if isinstance(other, dict) else {})
        return FieldExpression('', mongo_filter={'$and': [f1, f2]})

    def __rand__(self, other):
        return self.__and__(other)


class FieldDescriptor:
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance._data.get(self.name)

    def __set__(self, instance, value):
        instance._data[self.name] = value

    def desc(self):
        return (self.name, pymongo.DESCENDING)

    def asc(self):
        return (self.name, pymongo.ASCENDING)

    def __eq__(self, other):
        return FieldExpression(self.name, '$eq', other)

    def __ne__(self, other):
        return FieldExpression(self.name, '$ne', other)

    def __gt__(self, other):
        return FieldExpression(self.name, '$gt', other)

    def __gte__(self, other):
        return FieldExpression(self.name, '$gte', other)

    def __lt__(self, other):
        return FieldExpression(self.name, '$lt', other)

    def __lte__(self, other):
        return FieldExpression(self.name, '$lte', other)

    def in_(self, values):
        return FieldExpression(self.name, '$in', list(values))

    def ilike(self, pattern):
        # Convert SQL LIKE '%xyz%' to regex
        regex_pattern = pattern
        if regex_pattern.startswith('%'):
            regex_pattern = regex_pattern[1:]
        if regex_pattern.endswith('%'):
            regex_pattern = regex_pattern[:-1]
        return FieldExpression(self.name, '$regex', re.compile(re.escape(regex_pattern), re.IGNORECASE))


class MongoQuery:
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self.filter_spec = {}
        self.sort_spec = []
        self.limit_val = None
        self.skip_val = None
        self._projection = None

    def _clone(self):
        q = MongoQuery(self.model_cls)
        q.filter_spec = dict(self.filter_spec)
        q.sort_spec = list(self.sort_spec)
        q.limit_val = self.limit_val
        q.skip_val = self.skip_val
        q._projection = self._projection
        return q

    def filter_by(self, **kwargs):
        q = self._clone()
        for k, v in kwargs.items():
            q.filter_spec[k] = v
        return q

    def filter(self, *criteria):
        q = self._clone()
        for crit in criteria:
            if crit is True:
                continue
            if crit is False:
                q.filter_spec = {'$alwaysFalse': True, **q.filter_spec}
                continue
            if isinstance(crit, FieldExpression):
                mongo_crit = crit.to_mongo()
            elif isinstance(crit, dict):
                mongo_crit = crit
            else:
                continue

            for k, v in mongo_crit.items():
                if k in q.filter_spec and isinstance(q.filter_spec[k], dict) and isinstance(v, dict):
                    q.filter_spec[k].update(v)
                elif k == '$or' and '$or' in q.filter_spec:
                    q.filter_spec['$and'] = q.filter_spec.get('$and', []) + [{'$or': q.filter_spec.pop('$or')}, {'$or': v}]
                else:
                    q.filter_spec[k] = v
        return q

    def order_by(self, *criteria):
        q = self._clone()
        for crit in criteria:
            if isinstance(crit, tuple) and len(crit) == 2:
                q.sort_spec.append(crit)
            elif isinstance(crit, FieldDescriptor):
                q.sort_spec.append((crit.name, pymongo.ASCENDING))
            elif isinstance(crit, str):
                if crit.startswith('-'):
                    q.sort_spec.append((crit[1:], pymongo.DESCENDING))
                else:
                    q.sort_spec.append((crit, pymongo.ASCENDING))
        return q

    def limit(self, n):
        q = self._clone()
        q.limit_val = n
        return q

    def offset(self, n):
        q = self._clone()
        q.skip_val = n
        return q

    def with_entities(self, *entities):
        q = self._clone()
        field_names = []
        for ent in entities:
            if isinstance(ent, FieldDescriptor):
                field_names.append(ent.name)
            elif isinstance(ent, str):
                field_names.append(ent)
        q._projection = field_names
        return q

    def get(self, ident):
        if ident is None:
            return None
        try:
            ident_int = int(ident)
        except (ValueError, TypeError):
            ident_int = ident
        
        col = db.get_collection(self.model_cls._collection_name)
        doc = col.find_one({'$or': [{'id': ident_int}, {'_id': ident}]})
        if not doc:
            return None
        return self.model_cls._from_doc(doc)

    def get_or_404(self, ident):
        obj = self.get(ident)
        if obj is None:
            abort(404)
        return obj

    def first(self):
        col = db.get_collection(self.model_cls._collection_name)
        cursor = col.find(self._build_filter())
        if self.sort_spec:
            cursor = cursor.sort(self.sort_spec)
        if self.skip_val:
            cursor = cursor.skip(self.skip_val)
        
        try:
            doc = next(cursor)
            return self.model_cls._from_doc(doc)
        except StopIteration:
            return None

    def first_or_404(self):
        obj = self.first()
        if obj is None:
            abort(404)
        return obj

    def all(self):
        col = db.get_collection(self.model_cls._collection_name)
        cursor = col.find(self._build_filter())
        if self.sort_spec:
            cursor = cursor.sort(self.sort_spec)
        if self.skip_val:
            cursor = cursor.skip(self.skip_val)
        if self.limit_val:
            cursor = cursor.limit(self.limit_val)

        return [self.model_cls._from_doc(doc) for doc in cursor]

    def count(self):
        col = db.get_collection(self.model_cls._collection_name)
        return col.count_documents(self._build_filter())

    def distinct(self):
        col = db.get_collection(self.model_cls._collection_name)
        if self._projection and len(self._projection) == 1:
            field = self._projection[0]
            vals = col.distinct(field, self._build_filter())
            # Format as list of 1-tuples to match SQLAlchemy with_entities(Field).distinct()
            return [(v,) for v in vals if v is not None]
        return col.distinct('id', self._build_filter())

    def delete(self):
        col = db.get_collection(self.model_cls._collection_name)
        res = col.delete_many(self._build_filter())
        return res.deleted_count

    def _build_filter(self):
        if self.filter_spec.get('$alwaysFalse'):
            return {'_id': {'$exists': False}}
        return self.filter_spec


class MongoSession:
    def __init__(self, db_manager):
        self.db = db_manager
        self._pending_add = []
        self._pending_delete = []

    def add(self, instance):
        if not any(instance is x for x in self._pending_add):
            self._pending_add.append(instance)

    def add_all(self, instances):
        for inst in instances:
            self.add(inst)

    def delete(self, instance):
        self._pending_add = [x for x in self._pending_add if x is not instance]
        if not any(instance is x for x in self._pending_delete):
            self._pending_delete.append(instance)

    def flush(self):
        self.commit()

    def commit(self):
        for inst in list(self._pending_add):
            inst.save()
        self._pending_add.clear()

        for inst in list(self._pending_delete):
            inst._delete_from_db()
        self._pending_delete.clear()

    def rollback(self):
        self._pending_add.clear()
        self._pending_delete.clear()

    def remove(self):
        self.rollback()


class MongoDB:
    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.database = None
        self.session = MongoSession(self)
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        mongo_uri = app.config.get('MONGO_URI', 'mongodb://localhost:27017/career_compass')
        db_name = app.config.get('MONGO_DB_NAME', 'career_compass')

        if mongo_uri.startswith('mongomock://') or app.config.get('TESTING'):
            self.client = mongomock.MongoClient()
            self.database = self.client[db_name]
        else:
            try:
                self.client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
                # Check connection
                self.client.server_info()
                parsed_db = None
                if '/' in mongo_uri.replace('mongodb://', '').replace('mongodb+srv://', ''):
                    tail = mongo_uri.split('/')[-1]
                    parsed_db = tail.split('?')[0] if tail else None
                self.database = self.client[parsed_db or db_name]
            except Exception as e:
                print(f"[CareerCompass MongoDB Notice] Could not connect to live MongoDB server ({e}). Using in-memory MongoMock.")
                self.client = mongomock.MongoClient()
                self.database = self.client[db_name]

    def get_db(self):
        if self.database is None:
            if self.app:
                self.init_app(self.app)
            else:
                self.client = mongomock.MongoClient()
                self.database = self.client['career_compass']
        return self.database

    def get_collection(self, name):
        return self.get_db()[name]

    def get_next_id(self, collection_name):
        db_inst = self.get_db()
        col = db_inst[collection_name]
        last_doc = col.find_one(sort=[('id', pymongo.DESCENDING)])
        if last_doc and isinstance(last_doc.get('id'), int):
            return last_doc['id'] + 1
        return 1

    def create_all(self):
        db_inst = self.get_db()
        try:
            db_inst['users'].create_index('email', unique=True)
            db_inst['users'].create_index('id', unique=True)
            db_inst['skills'].create_index('name', unique=True)
            db_inst['skills'].create_index('id', unique=True)
            db_inst['career_roles'].create_index('title', unique=True)
            db_inst['career_roles'].create_index('id', unique=True)
            db_inst['user_skills'].create_index([('user_id', pymongo.ASCENDING), ('skill_id', pymongo.ASCENDING)], unique=True)
            db_inst['user_skills'].create_index('id', unique=True)
            db_inst['career_skill_requirements'].create_index([('career_id', pymongo.ASCENDING), ('skill_id', pymongo.ASCENDING)], unique=True)
            db_inst['user_roadmap_progress'].create_index([('user_id', pymongo.ASCENDING), ('career_id', pymongo.ASCENDING)], unique=True)
        except Exception:
            pass

    def drop_all(self):
        db_inst = self.get_db()
        for col_name in db_inst.list_collection_names():
            if not col_name.startswith('system.'):
                db_inst[col_name].drop()


db = MongoDB()


class ModelMeta(type):
    @property
    def query(cls):
        return MongoQuery(cls)


class BaseMongoModel(metaclass=ModelMeta):
    _collection_name = 'documents'

    def __init__(self, **kwargs):
        self._data = {}
        for k, v in kwargs.items():
            self._data[k] = v

    @property
    def query(self):
        return MongoQuery(self.__class__)

    @classmethod
    def _from_doc(cls, doc):
        if not doc:
            return None
        inst = cls()
        inst._data = dict(doc)
        return inst

    @property
    def id(self):
        return self._data.get('id')

    @id.setter
    def id(self, val):
        self._data['id'] = val

    def __eq__(self, other):
        if other is None or not isinstance(other, BaseMongoModel):
            return False
        if self.id is not None and getattr(other, 'id', None) is not None:
            return self.id == other.id and self._collection_name == getattr(other, '_collection_name', None)
        return self is other

    def __hash__(self):
        if self.id is not None:
            return hash((self._collection_name, self.id))
        return id(self)

    def save(self):
        col = db.get_collection(self._collection_name)
        if 'id' not in self._data or self._data['id'] is None:
            self._data['id'] = db.get_next_id(self._collection_name)
        
        doc_id = self._data['id']
        col.replace_one({'id': doc_id}, self._data, upsert=True)
        return self

    def _delete_from_db(self):
        if 'id' in self._data:
            col = db.get_collection(self._collection_name)
            col.delete_one({'id': self._data['id']})


# ---------------- Model Definitions ----------------

class User(UserMixin, BaseMongoModel):
    _collection_name = 'users'

    full_name = FieldDescriptor('full_name')
    email = FieldDescriptor('email')
    password_hash = FieldDescriptor('password_hash')
    role = FieldDescriptor('role')
    education = FieldDescriptor('education')
    target_career_id = FieldDescriptor('target_career_id')
    bio = FieldDescriptor('bio')
    created_at = FieldDescriptor('created_at')

    def __init__(self, full_name='', email='', password_hash='', role='student', education='', target_career_id=None, bio='', created_at=None, **kwargs):
        super().__init__(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            role=role,
            education=education,
            target_career_id=target_career_id,
            bio=bio,
            created_at=created_at or utc_now(),
            **kwargs
        )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash or '', password)

    def get_reset_token(self):
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=3600):
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def user_skills(self):
        return UserSkill.query.filter_by(user_id=self.id).all()

    @property
    def target_career(self):
        if self.target_career_id:
            return CareerRole.query.get(self.target_career_id)
        return None

    @property
    def roadmap_progress(self):
        return UserRoadmapProgress.query.filter_by(user_id=self.id).all()

    @property
    def daily_logs(self):
        return DailyLog.query.filter_by(user_id=self.id).all()

    def get_skill_names(self):
        return [us.skill.name for us in self.user_skills if us.skill]

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'education': self.education,
            'target_career': self.target_career.title if self.target_career else None,
            'skills_count': len(self.user_skills)
        }


class Skill(BaseMongoModel):
    _collection_name = 'skills'

    name = FieldDescriptor('name')
    category = FieldDescriptor('category')
    description = FieldDescriptor('description')

    def __init__(self, name='', category='', description='', **kwargs):
        super().__init__(
            name=name,
            category=category,
            description=description,
            **kwargs
        )

    @property
    def user_skills(self):
        return UserSkill.query.filter_by(skill_id=self.id).all()

    @property
    def career_requirements(self):
        return CareerSkillRequirement.query.filter_by(skill_id=self.id).all()

    @property
    def resources(self):
        return LearningResource.query.filter_by(skill_id=self.id).all()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description
        }


class UserSkill(BaseMongoModel):
    _collection_name = 'user_skills'

    user_id = FieldDescriptor('user_id')
    skill_id = FieldDescriptor('skill_id')
    proficiency = FieldDescriptor('proficiency')
    years_experience = FieldDescriptor('years_experience')
    added_at = FieldDescriptor('added_at')

    def __init__(self, user_id=None, skill_id=None, proficiency='Intermediate', years_experience=0.5, added_at=None, **kwargs):
        super().__init__(
            user_id=user_id,
            skill_id=skill_id,
            proficiency=proficiency,
            years_experience=years_experience,
            added_at=added_at or utc_now(),
            **kwargs
        )

    @property
    def skill(self):
        return Skill.query.get(self.skill_id)

    @property
    def user(self):
        return User.query.get(self.user_id)


class CareerRole(BaseMongoModel):
    _collection_name = 'career_roles'

    title = FieldDescriptor('title')
    category = FieldDescriptor('category')
    description = FieldDescriptor('description')
    average_salary = FieldDescriptor('average_salary')
    market_demand = FieldDescriptor('market_demand')
    difficulty = FieldDescriptor('difficulty')
    icon = FieldDescriptor('icon')
    roadmap_phases_json = FieldDescriptor('roadmap_phases_json')

    def __init__(self, title='', category='', description='', average_salary='$95,000 - $145,000 / yr', market_demand='High', difficulty='Intermediate', icon='fa-laptop-code', roadmap_phases_json='[]', **kwargs):
        super().__init__(
            title=title,
            category=category,
            description=description,
            average_salary=average_salary,
            market_demand=market_demand,
            difficulty=difficulty,
            icon=icon,
            roadmap_phases_json=roadmap_phases_json,
            **kwargs
        )

    @property
    def skill_requirements(self):
        return CareerSkillRequirement.query.filter_by(career_id=self.id).all()

    @property
    def resources(self):
        return LearningResource.query.filter_by(career_id=self.id).all()

    @property
    def certifications(self):
        return Certification.query.filter_by(career_id=self.id).all()

    @property
    def projects(self):
        return ProjectIdea.query.filter_by(career_id=self.id).all()

    @property
    def roadmap_progress(self):
        return UserRoadmapProgress.query.filter_by(career_id=self.id).all()

    def get_phases(self):
        try:
            return json.loads(self.roadmap_phases_json or '[]')
        except Exception:
            return []

    def set_phases(self, phases_list):
        self.roadmap_phases_json = json.dumps(phases_list)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'average_salary': self.average_salary,
            'market_demand': self.market_demand,
            'difficulty': self.difficulty,
            'icon': self.icon,
            'required_skills_count': len(self.skill_requirements)
        }


class CareerSkillRequirement(BaseMongoModel):
    _collection_name = 'career_skill_requirements'

    career_id = FieldDescriptor('career_id')
    skill_id = FieldDescriptor('skill_id')
    importance = FieldDescriptor('importance')
    target_proficiency = FieldDescriptor('target_proficiency')
    weight = FieldDescriptor('weight')

    def __init__(self, career_id=None, skill_id=None, importance='Critical', target_proficiency='Intermediate', weight=3, **kwargs):
        super().__init__(
            career_id=career_id,
            skill_id=skill_id,
            importance=importance,
            target_proficiency=target_proficiency,
            weight=weight,
            **kwargs
        )

    @property
    def skill(self):
        return Skill.query.get(self.skill_id)

    @property
    def career(self):
        return CareerRole.query.get(self.career_id)


class LearningResource(BaseMongoModel):
    _collection_name = 'learning_resources'

    career_id = FieldDescriptor('career_id')
    skill_id = FieldDescriptor('skill_id')
    title = FieldDescriptor('title')
    resource_type = FieldDescriptor('resource_type')
    url = FieldDescriptor('url')
    provider = FieldDescriptor('provider')
    is_free = FieldDescriptor('is_free')
    difficulty = FieldDescriptor('difficulty')
    description = FieldDescriptor('description')

    def __init__(self, career_id=None, skill_id=None, title='', resource_type='Course', url='', provider='Online', is_free=True, difficulty='Beginner', description='', **kwargs):
        super().__init__(
            career_id=career_id,
            skill_id=skill_id,
            title=title,
            resource_type=resource_type,
            url=url,
            provider=provider,
            is_free=is_free,
            difficulty=difficulty,
            description=description,
            **kwargs
        )

    @property
    def career(self):
        if self.career_id:
            return CareerRole.query.get(self.career_id)
        return None

    @property
    def skill(self):
        if self.skill_id:
            return Skill.query.get(self.skill_id)
        return None


class Certification(BaseMongoModel):
    _collection_name = 'certifications'

    career_id = FieldDescriptor('career_id')
    name = FieldDescriptor('name')
    issuer = FieldDescriptor('issuer')
    url = FieldDescriptor('url')
    cost_type = FieldDescriptor('cost_type')
    difficulty = FieldDescriptor('difficulty')
    description = FieldDescriptor('description')

    def __init__(self, career_id=None, name='', issuer='', url='', cost_type='Paid', difficulty='Intermediate', description='', **kwargs):
        super().__init__(
            career_id=career_id,
            name=name,
            issuer=issuer,
            url=url,
            cost_type=cost_type,
            difficulty=difficulty,
            description=description,
            **kwargs
        )

    @property
    def career(self):
        if self.career_id:
            return CareerRole.query.get(self.career_id)
        return None


class ProjectIdea(BaseMongoModel):
    _collection_name = 'project_ideas'

    career_id = FieldDescriptor('career_id')
    title = FieldDescriptor('title')
    description = FieldDescriptor('description')
    difficulty = FieldDescriptor('difficulty')
    tech_stack = FieldDescriptor('tech_stack')
    milestones_json = FieldDescriptor('milestones_json')

    def __init__(self, career_id=None, title='', description='', difficulty='Intermediate', tech_stack='', milestones_json='[]', **kwargs):
        super().__init__(
            career_id=career_id,
            title=title,
            description=description,
            difficulty=difficulty,
            tech_stack=tech_stack,
            milestones_json=milestones_json,
            **kwargs
        )

    @property
    def career(self):
        if self.career_id:
            return CareerRole.query.get(self.career_id)
        return None

    def get_milestones(self):
        try:
            return json.loads(self.milestones_json or '[]')
        except Exception:
            return []


class UserRoadmapProgress(BaseMongoModel):
    _collection_name = 'user_roadmap_progress'

    user_id = FieldDescriptor('user_id')
    career_id = FieldDescriptor('career_id')
    completed_milestones_json = FieldDescriptor('completed_milestones_json')
    progress_percentage = FieldDescriptor('progress_percentage')
    notes = FieldDescriptor('notes')
    last_updated = FieldDescriptor('last_updated')

    def __init__(self, user_id=None, career_id=None, completed_milestones_json='[]', progress_percentage=0.0, notes='', last_updated=None, **kwargs):
        super().__init__(
            user_id=user_id,
            career_id=career_id,
            completed_milestones_json=completed_milestones_json,
            progress_percentage=progress_percentage,
            notes=notes,
            last_updated=last_updated or utc_now(),
            **kwargs
        )

    @property
    def user(self):
        return User.query.get(self.user_id)

    @property
    def career(self):
        return CareerRole.query.get(self.career_id)

    def get_completed_milestones(self):
        try:
            return json.loads(self.completed_milestones_json or '[]')
        except Exception:
            return []

    def set_completed_milestones(self, milestones_list):
        self.completed_milestones_json = json.dumps(milestones_list)
        self.last_updated = utc_now()


class DailyLog(BaseMongoModel):
    _collection_name = 'daily_logs'

    user_id = FieldDescriptor('user_id')
    date = FieldDescriptor('date')
    hours_spent = FieldDescriptor('hours_spent')
    topic_studied = FieldDescriptor('topic_studied')
    notes = FieldDescriptor('notes')

    def __init__(self, user_id=None, date=None, hours_spent=1.0, topic_studied='', notes='', **kwargs):
        today_val = date if date is not None else datetime.now(timezone.utc).date()
        if isinstance(today_val, datetime):
            today_str = today_val.strftime('%Y-%m-%d')
        elif hasattr(today_val, 'isoformat'):
            today_str = today_val.isoformat()
        else:
            today_str = str(today_val)

        super().__init__(
            user_id=user_id,
            date=today_str,
            hours_spent=float(hours_spent),
            topic_studied=topic_studied,
            notes=notes,
            **kwargs
        )

    @property
    def user(self):
        return User.query.get(self.user_id)
