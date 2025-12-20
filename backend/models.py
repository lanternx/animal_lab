from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Mouse(db.Model):
    __tablename__ = 'mouse'

    tid = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(10), nullable=False)
    sex = db.Column(db.String(1))  # 'M' or 'F'
    live_status = db.Column(db.Integer, default=1)  # 1 for '活', 0 for '死', 2 for '解剖', 3 for '意外消失', 4 for '丢弃'
    birth_date = db.Column(db.Date)
    death_date = db.Column(db.Date)
    cage_id = db.Column(db.Integer, db.ForeignKey('cage.id'))
    strain = db.Column(db.String(50))
    tests_planned = db.Column(db.JSON)  #储存实验id的列表

    # 关系
    cage = db.relationship('Cage', backref=db.backref('mice', lazy=True))
    genotypes = db.relationship('Genotype', backref='mouse', lazy='dynamic', cascade='all, delete-orphan')
    tests_done = db.relationship('ExperimentClass', backref='mouse', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_genotypes(self):
        genes = []
        gene_en = []
        for g in self.genotypes:
            gd = {"genotypeLocus": g.locus.symbol, "genotypeAllele": g.get_allele(), "genotypeHomo": g.get_zygosis()}
            genes.append(gd)
            ge = {"allele1": g.allele1_id, "allele2": g.allele2_id, "locus": g.locus.symbol}
            gene_en.append(ge)
        return {"symbol": self.get_full_genotype(), "genes": genes, "geneEntity": gene_en}

    def get_full_genotype(self):
        """获取完整的基因型描述"""
        loci = []
        for gt in self.genotypes:
            desc = gt.get_genotype_description()
            loci.append(desc)
        return "; ".join(loci)
    
    def get_genotype_str(self):
        """获取可导入的基因型字符串表示"""
        loci = []
        for gt in self.genotypes:
            if gt.allele1 and gt.allele2:
                locus_str = "{"+gt.locus.symbol+"}["+gt.allele1.symbol+"]/["+gt.allele2.symbol+"]"
            else:
                locus_str = "{"+gt.locus.symbol+"}"
            loci.append(locus_str)
        return "&".join(loci)

    def to_dict(self):
        return {
            'tid': self.tid,
            'id': self.id,
            'genotype': self.get_full_genotype(),
            'sex': self.sex,
            'live_status': self.live_status,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'death_date': self.death_date.isoformat() if self.death_date else None,
            'cage_id': self.cage_id,
            'strain': self.strain,
            'tests_done': [t.experiment_id for t in self.tests_done] if self.tests_done else [],
            'tests_planned': self.tests_planned
        }
    
class Pedigree(db.Model):
    __tablename__ = 'pedigree'

    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid', ondelete='CASCADE'))
    parent_id = db.Column(db.Integer, db.ForeignKey('mouse.tid', ondelete='CASCADE'))
    parent_type = db.Column(db.String(10))  # 'father' or 'mother'

    # 关系
    mouse = db.relationship('Mouse', foreign_keys=[mouse_id], backref=db.backref('pedigree_records', lazy=True))
    parent = db.relationship('Mouse', foreign_keys=[parent_id], backref=db.backref('offspring', lazy=True))

class Cage(db.Model):
    __tablename__ = 'cage'
    
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(50), db.ForeignKey('location.identifier'), nullable=False)
    cage_id = db.Column(db.String(10), nullable=False) #这个就是笼位卡上显示的编号
    location = db.Column(db.String(50))
    cage_type = db.Column(db.String(20), default='normal')  # 'normal' or 'breeding' or 'testing'
    order = db.Column(db.Integer, nullable=False)
    # 新增字段：笼内小鼠出生日期、数量及性别、基因型
    mice_birth_date = db.Column(db.Date)
    mice_count = db.Column(db.Integer)
    mice_sex = db.Column(db.String(10))  # 'M'/'F'/'Mixed'
    mice_genotype = db.Column(db.String(50))

    def display(self):
        return self.section + "-" + self.cage_id
    
class WeightRecord(db.Model):
    __tablename__ = 'weight_record'
    
    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    record_livingdays = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        mouse = Mouse.query.get_or_404(self.mouse_id)
        return {
            'weight_id': self.id,
            'mouse_tid': self.mouse_id,
            'id': mouse.id,
            'birth_date': mouse.birth_date.isoformat() if mouse.birth_date else None,
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
        mouse = Mouse.query.get_or_404(self.mouse_id)
        return {
            'record_id': self.id,
            'mouse_tid': self.mouse_id,
            'id': mouse.id,
            'birth_date': mouse.birth_date.isoformat() if mouse.birth_date else None,
            'record_date': self.record_date,
            'record': self.status,
            'record_livingdays': self.record_livingdays
        }

# 等位基因定义
class Allele(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False)  # 等位基因符号，如 "S46A", "flox", "KO", "+"
    locus_id = db.Column(db.Integer, db.ForeignKey('gene_locus.id'), nullable=False)
    description = db.Column(db.String(200))
    is_wildtype = db.Column(db.Boolean, default=False)  # 标记是否为野生型
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'description': self.description,
            'is_wildtype': self.is_wildtype
        }
    
# 基因位点定义
class GeneLocus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), unique=True, nullable=False)  # 基因符号
    description = db.Column(db.String(200))
    alleles = db.relationship('Allele', backref='locus', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'description': self.description,
            'alleles': [a.to_dict() for a in self.alleles]
        }
    
# 小鼠基因型定义
class Genotype(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid'), nullable=False)
    locus_id = db.Column(db.Integer, db.ForeignKey('gene_locus.id'), nullable=False)
    
    # 精确到等位基因
    allele1_id = db.Column(db.Integer, db.ForeignKey('allele.id'))
    allele2_id = db.Column(db.Integer, db.ForeignKey('allele.id'))
    
    # 关系
    locus = db.relationship('GeneLocus')
    allele1 = db.relationship('Allele', foreign_keys=[allele1_id])
    allele2 = db.relationship('Allele', foreign_keys=[allele2_id])

    def contains_allele(self, al_id):
        if self.allele1_id == al_id or self.allele2_id == al_id:
            return True
        else:
            return False
        
    def get_zygosis(self):
        if not self.allele1_id or not self.allele2_id:
            return None
        if self.allele1_id == self.allele2_id:
            return 'homo'
        else:
            return 'hetero'
        
    def get_allele(self):
        if not self.allele1_id or not self.allele2_id:
            return None
        if self.allele1_id == self.allele2_id:
            return [self.allele1.symbol]
        else:
            return [self.allele1.symbol, self.allele2.symbol]
    
    def get_genotype_description(self):
        """获取详细的基因型描述"""
        if self.locus.symbol == "WT":
            return "WT"
        if self.allele1.symbol == "+":
            alleles = [self.allele2.symbol, self.allele1.symbol]
        elif self.allele2.symbol == "+":
            alleles = [self.allele1.symbol, self.allele2.symbol]
        else:
            alleles = sorted([self.allele1.symbol, self.allele2.symbol])
        return f"{self.locus.symbol}<sup>{alleles[0]}/{alleles[1]}</sup>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'locus': self.locus.symbol,
            'allele1': self.allele1.symbol if self.allele1 else None,
            'allele2': self.allele2.symbol if self.allele2 else None,
            'description': self.get_genotype_description()
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
            'fields': sorted_fields,
            'is_show': self.is_show
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
    def to_dict(self):
        # 根据字段定义的数据类型获取对应的值
        value = None
        if self.field_definition:
            if self.field_definition.data_type == 'INTEGER':
                value = self.value_int
            elif self.field_definition.data_type == 'REAL':
                value = self.value_real
            elif self.field_definition.data_type == 'TEXT':
                value = self.value_text
            elif self.field_definition.data_type == 'BOOLEAN':
                value = self.value_bool
            elif self.field_definition.data_type == 'DATE':
                value = self.value_date.isoformat() if self.value_date else None
        
        return {
            'id': self.id,
            'experiment_id': self.experiment_id,
            'field_definition_id': self.field_definition_id,
            'value': value,
            'field_name': self.field_definition.field_name if self.field_definition else None,
            'data_type': self.field_definition.data_type if self.field_definition else None,
            'unit': self.field_definition.unit if self.field_definition else None
        }
    
#实验分组表
class ExperimentClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey('mouse.tid', ondelete='CASCADE'), nullable=False)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment_type.id'), nullable=False)
    
    def to_dict(self):
        return {
            'class_id': self.class_id,
            'mouse_id': self.mouse_id,
            'experiment_id': self.experiment_id,
            'mouse_info': self.mouse.to_dict() if self.mouse else None
        }
    
class PredefinedGroup(db.Model):
    __tablename__ = 'rule_of_predefined_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment_type.id'), unique=True)
    Gtype = db.Column(db.String(20), nullable=False) #id/rule
    rules = db.Column(db.JSON)  # 存储复杂分组规则
    """ rule[{name:, color:, rules:[]},{...}]
        id[{name:, color:, mouseId:[]},{...}]注意，按id分组显示时需要确定小鼠是否还存在"""

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'experiment_id': self.experiment_id,
            'Gtype': self.Gtype,
            'rules': self.rules or []
        }