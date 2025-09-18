from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Mouse(db.Model):
    tid = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(10), nullable=False)
    genotype = db.Column(db.String(50))
    sex = db.Column(db.String(1))  # 'M' or 'F'
    live_status = db.Column(db.Integer, default=1)  # 1 for '活', 0 for '死', 2 for '解剖', 3 for '意外消失', 4 for '丢弃'
    birth_date = db.Column(db.Date)
    death_date = db.Column(db.Date)
    cage_id = db.Column(db.String(20), db.ForeignKey('cage.id'))
    # 新增字段：品系、已完成测试、计划测试
    strain = db.Column(db.String(50))
    tests_done = db.Column(db.String(200))
    tests_planned = db.Column(db.String(200))
    def to_dict(self):
        return {
            'tid': self.tid,
            'id': self.id,
            'genotype': self.genotype,
            'sex': self.sex,
            'live_status': self.live_status,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'death_date': self.death_date.isoformat() if self.death_date else None,
            'cage_id': self.cage_id,
            'strain': self.strain,
            'tests_done': self.tests_done,
            'tests_planned': self.tests_planned
        }

class Pedigree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'))
    parent_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'))
    parent_type = db.Column(db.String(10))  # 'father' or 'mother'

class Cage(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    section = db.Column(db.String(50), db.ForeignKey('location.identifier'), nullable=False)
    cage_id = db.Column(db.String(10), nullable=False) #这个就是笼位卡上显示的编号
    location = db.Column(db.String(50)) #可以填写测试项目
    cage_type = db.Column(db.String(20), default='normal')  # 'normal' or 'breeding' or 'testing'
    order = db.Column(db.Integer, nullable=False)
    # 新增字段：笼内小鼠出生日期、数量及性别、基因型
    mice_birth_date = db.Column(db.Date)
    mice_count = db.Column(db.Integer)
    mice_sex = db.Column(db.String(10))  # 'M'/'F'/'Mixed'
    mice_genotype = db.Column(db.String(50))
    # 保持与Mouse的关系定义
    mice = db.relationship('Mouse', backref='cage', lazy=True)
    
class WeightRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    record_livingdays = db.Column(db.Integer, nullable=False)
    def to_dict(self):
        return {
            'weight_id': self.id,
            'mouse_tid': self.mouse_id,
            'weight': self.weight,
            'record_date': self.record_date.isoformat(),
            'record_livingdays': self.record_livingdays
        }

class StatusRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    record_livingdays = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'record_id': self.id,
            'mouse_id': self.mouse_id,
            'record_date': self.record_date,
            'status': self.status
        }

# 基因型模型
class Genotype(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

# 位置模型
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    order = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'order': self.order,
            'identifier': self.identifier,
            'description': self.description
        }