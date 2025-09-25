from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Mouse(db.Model):
    __tablename__ = 'mouse'

    tid = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(10), nullable=False)
    genotype = db.Column(db.String(50))
    sex = db.Column(db.String(1))  # 'M' or 'F'
    live_status = db.Column(db.Integer, default=1)  # 1 for '活', 0 for '死', 2 for '解剖', 3 for '意外消失', 4 for '丢弃'
    birth_date = db.Column(db.Date)
    death_date = db.Column(db.Date)
    cage_id = db.Column(db.String(20), db.ForeignKey('cage.id'))
    strain = db.Column(db.String(50))
    tests_done = db.Column(db.JSON)     #储存实验id的列表
    tests_planned = db.Column(db.JSON)  #储存实验id的列表

    # 关系
    cage = db.relationship('Cage', backref=db.backref('mice', lazy=True))
    
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
    __tablename__ = 'pedigree'

    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'))
    parent_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'))
    parent_type = db.Column(db.String(10))  # 'father' or 'mother'

    # 关系
    mouse = db.relationship('Mouse', foreign_keys=[mouse_id], backref=db.backref('pedigree_records', lazy=True))
    parent = db.relationship('Mouse', foreign_keys=[parent_id], backref=db.backref('offspring', lazy=True))


class Cage(db.Model):
    __tablename__ = 'cage'
    
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
    
class WeightRecord(db.Model):
    __tablename__ = 'weight_record'
    
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
    
# 实验类型表
class ExperimentType(db.Model):
    __tablename__ = 'experiment_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 实验类型名称
    description = db.Column(db.Text)  # 实验类型描述
    is_show = db.Column(db.Boolean, default=False)
    
    # 与字段定义的关系
    field_definitions = db.relationship('FieldDefinition', backref='experiment_type', lazy=True)
    
    def to_dict(self):
        # 获取按display_order排序的字段定义
        sorted_fields = sorted(
            [fd.to_dict() for fd in self.field_definitions],
            key=lambda x: x['display_order']
        )
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description, 
            'fields': sorted_fields
        }

# 字段定义表
class FieldDefinition(db.Model):
    __tablename__ = 'field_definition'
    
    id = db.Column(db.Integer, primary_key=True)
    experiment_type_id = db.Column(db.Integer, db.ForeignKey('experiment_type.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)  # 字段名称
    data_type = db.Column(db.String(20), nullable=False)  # 数据类型: INTEGER, REAL, TEXT, BOOLEAN, DATE
    unit = db.Column(db.String(20))  # 单位
    is_required = db.Column(db.Boolean, default=False)  # 是否为必填字段
    visualize_type = db.Column(db.String(20))  # 可视化中的类型：x, y, column
    display_order = db.Column(db.Integer, default=0)  # 显示顺序
    
    def to_dict(self):
        return {
            'id': self.id,
            'experiment_type_id': self.experiment_type_id,
            'field_name': self.field_name,
            'data_type': self.data_type,
            'unit': self.unit,
            'is_required': self.is_required,
            'visualize_type': self.visualize_type,
            'display_order': self.display_order
        }

# 实验记录表
class Experiment(db.Model):
    __tablename__ = 'experiment'
    
    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'), nullable=False)
    experiment_type_id = db.Column(db.Integer, db.ForeignKey('experiment_type.id'), nullable=False)
    researcher = db.Column(db.String(50))  # 实验人员
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)  # 备注
    
    # 与小鼠的关系
    mouse = db.relationship('Mouse', backref=db.backref('experiments', lazy=True))
    
    # 与实验类型的关系
    experiment_type = db.relationship('ExperimentType', backref=db.backref('experiments', lazy=True))
    
    # 与实验数据值的关系
    values = db.relationship('ExperimentValue', backref='experiment', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'mouse_id': self.mouse_id,
            'experiment_type_id': self.experiment_type_id,
            'researcher': self.researcher,
            'date': self.date.isoformat() if self.date else None,
            'notes': self.notes,
            'values': [value.to_dict() for value in self.values]
        }

# 实验数据值表 (EAV模式)
class ExperimentValue(db.Model):
    __tablename__ = 'experiment_value'
    
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    field_definition_id = db.Column(db.Integer, db.ForeignKey('field_definition.id'), nullable=False)
    
    # 根据不同数据类型存储的值
    value_int = db.Column(db.Integer)
    value_real = db.Column(db.Float)
    value_text = db.Column(db.Text)
    value_bool = db.Column(db.Boolean)
    value_date = db.Column(db.Date)
    
    # 与字段定义的关系
    field_definition = db.relationship('FieldDefinition', backref=db.backref('values', lazy=True))

#实验分组表
class ExperimentClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    moues_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'), nullable=False)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    class_id = db.Column(db.Integer, nullable=False)

        # 关系
    mouse = db.relationship('Mouse', backref=db.backref('experiment_classes', lazy=True))
    experiment = db.relationship('Experiment', backref=db.backref('experiment_classes', lazy=True))
    
    def to_dict(self):
        return {
            'class_id': self.class_id,
            'mouse_id': self.mouse_id,
            'experiment_id': self.experiment_id,
            'mouse_info': self.mouse.to_dict() if self.mouse else None
        }