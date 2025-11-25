from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from datetime import datetime, date
from models import db, Mouse, Cage, WeightRecord, StatusRecord, Pedigree, GeneLocus, Allele, Genotype, Location, ExperimentType, FieldDefinition, Experiment, ExperimentClass, ExperimentValue, PredefinedGroup
import os
import sys
from pathlib import Path
import pandas as pd
from io import BytesIO
from sqlalchemy import text, inspect, or_, and_
from sqlalchemy.orm import joinedload
import re
from migration_script import DatabaseMigrator

import socket

# 首先应用猴子补丁 - 必须在创建 Flask 应用之前
def apply_socket_patch():
    """应用安全的 socket 函数补丁"""
    # 保存原始函数
    _original_getfqdn = socket.getfqdn
    _original_gethostname = socket.gethostname
    
    def safe_gethostname():
        try:
            name = _original_gethostname()
            if isinstance(name, bytes):
                # 尝试常见编码
                for encoding in ['utf-8', 'gbk', 'latin-1']:
                    try:
                        return name.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                # 所有编码失败则替换无效字节
                return name.decode('utf-8', errors='replace')
            return name
        except Exception:
            return 'localhost'
    
    def safe_getfqdn(name=''):
        try:
            # 使用我们安全的主机名函数
            hostname = safe_gethostname()
            return f"{hostname}.local" if hostname else "localhost"
        except Exception:
            return "localhost"
    
    # 应用补丁
    socket.gethostname = safe_gethostname
    socket.getfqdn = safe_getfqdn

# 应用补丁
apply_socket_patch()

import logging
# 获取主日志记录器
logger = logging.getLogger("Main")


app = Flask(__name__, static_folder='dist', static_url_path='')
CORS(app)  # 允许跨域请求


# 配置数据库 - 修改部分开始
def get_base_dir():
    """获取应用程序的基础目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的情况
        return Path(sys.executable).parent
    else:
        # 开发环境
        return Path(__file__).parent

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")
import json
# 读取配置
if not os.path.exists(config_path):
    # 创建默认配置文件
    default_config = {
        "db": {
            "default_db": "mice.db",
            "db_list": {'mice.db': {'projectName': '默认数据库', 'startAt':None, 'endAt':None, 'readOnly': False} }
        }
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4)

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

def get_db_file():
    """获取数据库文件名"""
    current_db = config['db'].get('default_db', '')
    if current_db:
        return current_db
    else:
        config['db']['default_db'] = 'mice.db'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return 'mice.db'

# 确定基础目录
base_dir = get_base_dir()
db_path = base_dir / get_db_file()
default_db = config['db']['default_db']
db_list = config['db']['db_list']
# 确保目录存在
base_dir.mkdir(parents=True, exist_ok=True)
if not os.path.exists(db_path):
    open(db_path, "w").close()
    
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# 确保数据库初始化完成
with app.app_context():
    try:
        db.create_all()
        print("数据库初始化完成")
        # 测试数据库连接
        db.session.execute(text('SELECT 1'))
        print("数据库连接测试成功")

        # 自动创建默认位置（如果不存在）
        if not db.session.query(Location).first():
            new_location = Location(
                identifier="默认区域",
                description=f"系统启动时自动创建 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                order=0
            )
            db.session.add(new_location)
            db.session.commit()
            print("已自动创建默认位置")
        else:
            print("位置已存在")

        if not db.session.query(GeneLocus).first():
            new_gene_locus = GeneLocus(
                symbol = "WT",
                description = "")
            db.session.add(new_gene_locus)
            db.session.commit()
            print("已自动创建默认基因型")
        else:
            print("基因型已存在")

            
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        raise


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_files(path):
    return app.send_static_file(path)


@app.before_request
def block_non_read_requests():
    if app.config.get('READ_ONLY_MODE', False):
        if request.method not in ['GET', 'HEAD']:
            return jsonify({
                "error": "Database is in read-only mode",
                "message": "写操作被禁止，因为数据库处于只读模式。"
            }), 403
            

##列表视图
@app.route('/api/mice', methods=['GET'])
def get_all_mice():
    try:
        mice = Mouse.query.all()
        # 计算日龄和周龄
        mice_data = []
        for m in mice:
            parents = Pedigree.query.filter_by(mouse_id=m.tid).all()
            if parents and len(parents) > 0:
                father = [p.parent_id for p in parents if p.parent_type == 'father']
                mother = [p.parent_id for p in parents if p.parent_type == 'mother']
            else:
                father = None
                mother = None
            if m.birth_date:
                birth_date = m.birth_date.strftime('%Y-%m-%d')
                if m.live_status != 1 and m.death_date:
                    days = (m.death_date - m.birth_date).days
                    weeks = days // 7
                else:
                    days = (datetime.now().date() - m.birth_date).days
                    weeks = days // 7
            else:
                birth_date = None
                days = None
                weeks = None
            mouse_dict = {
                'tid': m.tid,
                'id': m.id,
                'genotype': m.get_genotypes(),
                'sex': m.sex,
                'birth_date': birth_date,
                'death_date': m.death_date.strftime('%Y-%m-%d') if m.death_date else None,
                'cage_id': m.cage_id,
                'live_status': m.live_status,
                'father': father,
                'mother': mother,
                'strain': m.strain,
                'tests_done': [t.experiment_id for t in m.tests_done] if m.tests_done else [],
                'tests_planned': m.tests_planned,
                'days_old': days,
                'weeks_old': weeks
            }
            mice_data.append(mouse_dict)
        return jsonify(mice_data)
    except Exception as e:
        logger.error(f"获取小鼠列表失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500

@app.route('/api/mice', methods=['POST'])
def add_mouse():
    """添加新小鼠"""
    data = request.json
    try:
        mouse = Mouse()
        if data['id']:
            mouse.id = data['id']
        else:
            return jsonify({'error': 'Mouse ID is required'}), 400
        if data['sex']:
            mouse.sex = data['sex']
        if data['birth_date']:
            mouse.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        else:
            mouse.birth_date = None
        if mouse.birth_date:
            birth_date = mouse.birth_date.strftime('%Y-%m-%d')
            days = (datetime.now().date() - mouse.birth_date).days
            weeks = days // 7
        else:
            birth_date = None
            days = None
            weeks = None
        mouse.live_status = 1  # 默认新添加的小鼠状态为'活'
        mouse.cage_id = data.get('cage_id', None)
        # 新增字段
        mouse.strain = data.get('strain')
        mouse.tests_planned = data.get('tests_planned')
        db.session.add(mouse)
        db.session.flush()
        if data['genotype']:
            genotypes = data['genotype']
            for g in genotypes:
                locus = GeneLocus.query.filter_by(symbol=g["locus"]).first()
                if locus:
                    gene = Genotype(
                        mouse_id = mouse.tid,
                        locus_id = locus.id,
                        allele1_id = g["allele1"],
                        allele2_id = g["allele2"])
                    db.session.add(gene)
        if data['father']:
            for t in data['father']:
                parent = Pedigree(
                    mouse_id = mouse.tid,
                    parent_id = t,
                    parent_type = 'father')
                db.session.add(parent)
        if data['mother']:
            for t in data['mother']:
                parent = Pedigree(
                    mouse_id = mouse.tid,
                    parent_id = t,
                    parent_type = 'mother')
                db.session.add(parent)
        if 'tests_done' in data and data['tests_done']:
            for t in data['tests_done']:
                exp = ExperimentClass(
                    mouse_id=mouse.tid,
                    experiment_id=t
                )
                db.session.add(exp)
        db.session.commit()
        return jsonify({
            'tid': mouse.tid,
            'id': mouse.id,
            'genotype': mouse.get_genotypes(),
            'sex': mouse.sex,
            'birth_date': birth_date,
            'death_date': None,
            'live_status': mouse.live_status,
            'father': data['father'] if data['father'] else [],
            'mother': data['mother'] if data['mother'] else [],
            'cage_id': mouse.cage_id,
            'strain': mouse.strain,
            'tests_done': [t.experiment_id for t in mouse.tests_done] if mouse.tests_done else [],
            'tests_planned': mouse.tests_planned,
            'days_old': days,
            'weeks_old': weeks
        }), 201
    except Exception as e:
        logger.error(f"添加小鼠失败: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/mice/<int:mouse_tid>', methods=['PUT'])
def update_mouse(mouse_tid):
    """更新小鼠信息"""
    data = request.json
    mouse = Mouse.query.get_or_404(mouse_tid)
    try:
        if data['genotype']:
            Genotype.query.filter_by(mouse_id=mouse.tid).delete()
            genotypes = data['genotype']
            for g in genotypes:
                locus = GeneLocus.query.filter_by(symbol=g["locus"]).first()
                if locus:
                    gene = Genotype(
                        mouse_id = mouse.tid,
                        locus_id = locus.id,
                        allele1_id = g["allele1"],
                        allele2_id = g["allele2"])
                    db.session.add(gene)
        mouse.sex = data.get('sex', mouse.sex)
        mouse.live_status = data.get('live_status', mouse.live_status)
        if data['birth_date']:
            mouse.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if data['death_date']:
            if mouse.live_status == 1:
                mouse.death_date = None
            else:
                mouse.death_date = datetime.strptime(data['death_date'], '%Y-%m-%d').date()
        if 'strain' in data:
            mouse.strain = data.get('strain')
        if 'tests_done' in data:
            tests_done = set(data.get('tests_done'))
            experiments = set([t.experiment_id for t in mouse.tests_done])
            if tests_done != experiments:
                ExperimentClass.query.filter_by(mouse_id=mouse.tid).delete()
                for t in tests_done:
                    exp = ExperimentClass(
                        mouse_id=mouse.tid,
                        experiment_id=t
                    )
                    db.session.add(exp)
        if 'tests_planned' in data:
            mouse.tests_planned = data.get('tests_planned')
        if 'cage_id' in data:
            mouse.cage_id = data.get('cage_id')
        Pedigree.query.filter_by(mouse_id=mouse.tid, parent_type='father').delete()
        if data['father']:
            for t in data['father']:
                parent = Pedigree(
                    mouse_id=mouse.tid,
                    parent_id=t,
                    parent_type='father'
                )
                db.session.add(parent)
        Pedigree.query.filter_by(mouse_id=mouse.tid, parent_type='mother').delete()
        if data['mother']:
            for t in data['mother']:
                parent = Pedigree(
                    mouse_id=mouse.tid,
                    parent_id=t,
                    parent_type='mother'
                )
                db.session.add(parent)
        db.session.commit()
        return jsonify(), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新小鼠失败: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/mice/<int:mouse_tid>', methods=['DELETE'])
def delete_mouse(mouse_tid):
    """删除小鼠及其相关记录"""
    mouse = Mouse.query.get_or_404(mouse_tid)
    try:
        Genotype.query.filter_by(mouse_id=mouse_tid).delete()
        StatusRecord.query.filter_by(mouse_id=mouse_tid).delete()
        Pedigree.query.filter_by(mouse_id=mouse_tid).delete()
        Pedigree.query.filter_by(parent_id=mouse_tid).delete()
        WeightRecord.query.filter_by(mouse_id=mouse_tid).delete()
        ExperimentClass.query.filter_by(mouse_id=mouse_tid).delete()
        db.session.delete(mouse)
        db.session.commit()
        return jsonify({'message': 'Mouse deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除小鼠失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mice', methods=['DELETE'])
def delete_batch_mice():
    """批量删除小鼠及其相关记录"""
    mice_ids_param = request.args.getlist('miceIds[]')
    mice_ids = [int(id.strip()) for id in mice_ids_param] if mice_ids_param else []
    try:
        for mouse_tid in mice_ids:
            mouse = Mouse.query.get_or_404(mouse_tid)
            Genotype.query.filter_by(mouse_id=mouse_tid).delete()
            StatusRecord.query.filter_by(mouse_id=mouse_tid).delete()
            Pedigree.query.filter_by(mouse_id=mouse_tid).delete()
            Pedigree.query.filter_by(parent_id=mouse_tid).delete()
            WeightRecord.query.filter_by(mouse_id=mouse_tid).delete()
            ExperimentClass.query.filter_by(mouse_id=mouse_tid).delete()
            db.session.delete(mouse)
        db.session.commit()
        return jsonify({'message': 'Mouse deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除小鼠失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mice/<int:mouse_tid>', methods=['POST'])
def add_mice_from_template(mouse_tid):
    """基于模板小鼠批量添加新小鼠"""
    data = request.json
    try:
        template_mouse = Mouse.query.get_or_404(mouse_tid)
        template_mouse_parent = Pedigree.query.filter_by(mouse_id=mouse_tid).all()
        genes = Genotype.query.filter_by(mouse_id=mouse_tid).all()
        for m in data:
            new_mouse_data = template_mouse.to_dict()
            # 移除不需要继承的字段（如主键、创建时间等）
            excluded_fields = ['id', 'tid', 'sex', 'genotype']
            for field in excluded_fields:
                new_mouse_data.pop(field, None)
            new_mouse_data['death_date'] = date.fromisoformat(new_mouse_data['death_date']) if new_mouse_data['death_date'] else None
            new_mouse_data['birth_date'] = date.fromisoformat(new_mouse_data['birth_date']) if new_mouse_data['birth_date'] else None
            new_mouse_data['id'] = m['id']
            new_mouse_data['sex'] = m['sex']
            new_mouse = Mouse(**new_mouse_data)
            db.session.add(new_mouse)
            db.session.flush()
            for g in genes:
                new_gene = Genotype(
                    mouse_id=new_mouse.tid,
                    locus_id=g.locus_id,
                    allele1_id=g.allele1_id,
                    allele2_id=g.allele2_id
                )
                db.session.add(new_gene)
            for p in template_mouse_parent:
                new_parent = Pedigree(
                    mouse_id=new_mouse.tid,
                    parent_id=p.parent_id,
                    parent_type=p.parent_type)
                db.session.add(new_parent)
        db.session.commit()
        return jsonify(), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量添加小鼠失败: {str(e)}")
        return jsonify({'error': str(e)}), 400

# 批量修改实验小鼠
@app.route('/api/mice/experiments', methods=['PUT'])
def batch_experiments_change():
    try:
        data = request.json
        mice_ids = data.get("miceIds", [])
        test_ids = data.get("testIds", [])
        operation = data.get("batchTest", "")
        if operation == "完成实验":
            for mtid in mice_ids:
                m = Mouse.query.get_or_404(mtid)
                if not m:
                    continue
                if m.tests_done:
                    m.tests_done.delete()
                for test_id in test_ids:
                    enter_experiment = ExperimentClass(
                        mouse_id = m.tid,
                        experiment_id = test_id
                    )
                    db.session.add(enter_experiment)
        elif operation == "计划实验":
            for mtid in mice_ids:
                m = Mouse.query.get_or_404(mtid)
                if not m:
                    continue
                m.tests_planned = test_ids
        db.session.commit()
        return jsonify(), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量修改小鼠任务状态失败: {str(e)}")
        return jsonify({'error': str(e)}), 400



##笼位视图
@app.route('/api/cages', methods=['GET'])
def get_all_cages():
    """使用预加载一次性获取所有笼子及其小鼠"""
    try:
        cages = Cage.query.options(joinedload(Cage.mice)).order_by(Cage.order.asc()).all()
        cage_data = []
        for cage in cages:
            mice_info = []
            for mouse in cage.mice:
                if mouse.live_status == 1:
                    mice_info.append({
                        'tid': mouse.tid,
                        'id': mouse.id,
                        'genotype': mouse.get_full_genotype(),
                        'sex': mouse.sex,
                        'days': (datetime.now().date() - mouse.birth_date).days if mouse.birth_date else None
                    })
            cage_data.append({
                'id': cage.id,
                'cage_id': cage.cage_id,
                'section': cage.section,
                'location': cage.location,
                'cage_type': cage.cage_type,
                'mice': mice_info,
                'mice_birth_date': cage.mice_birth_date.strftime('%Y-%m-%d') if cage.mice_birth_date else None,
                'mice_count': cage.mice_count,
                'mice_sex': cage.mice_sex,
                'mice_genotype': cage.mice_genotype
            })
        return jsonify(cage_data)
    except Exception as e:
        logger.error(f"获取笼位失败: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/cages/-1', methods=['GET'])
def get_undetermined_mice():
    """查找未分配笼子的小鼠"""
    try:
        undetermined_mice = []
        undetermined_mice_query = Mouse.query.filter(Mouse.cage_id == None).all()
        for mouse in undetermined_mice_query:
            if mouse.live_status == 1:
                undetermined_mice.append({
                    'tid': mouse.tid,
                    'id': mouse.id,
                    'genotype': mouse.get_full_genotype(),
                    'sex': mouse.sex,
                    'days': (datetime.now().date() - mouse.birth_date).days if mouse.birth_date else None
                })
        return jsonify(undetermined_mice)
    except Exception as e:
        logger.error(f"获取无笼位小鼠失败: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/cages', methods=['POST'])
def add_cage():
    data = request.json
    try:
        # 获取当前最大的 order 值
        max_order = db.session.query(db.func.max(Cage.order)).scalar()
        
        # 如果没有记录，max_order 会是 None
        new_order = max_order + 1 if max_order is not None else 0
        cage = Cage(
            cage_id=data['cage_id'],
            section=data['section'],
            location=data.get('location'),
            cage_type=data.get('cage_type', 'normal'),
            order=new_order,
            mice_birth_date=datetime.strptime(data['mice_birth_date'], '%Y-%m-%d').date() if data.get('mice_birth_date') else None,
            mice_count=int(data['mice_count']) if data.get('mice_count') not in (None, "") else None,
            mice_sex=data.get('mice_sex'),
            mice_genotype=data.get('mice_genotype')
        )
        db.session.add(cage)
        db.session.commit()
        return jsonify({'id': cage.id}), 201
    except Exception as e:
        logger.error(f"添加笼位失败: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/cage', methods=['PUT'])
def move_mouse():
    data = request.json
    mouse = Mouse.query.get_or_404(data['mouse_id'])
    try:
        if data['cage_id'] == -1:
            mouse.cage_id = None
        else:
            mouse.cage_id = data['cage_id']
        db.session.commit()
        return jsonify({'message': f'Mouse {data["mouse_id"]} moved to cage {data["cage_id"]}'})
    except Exception as e:
        logger.error(f"调整小鼠笼位失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 删除笼位API
@app.route('/api/cages/<int:cage_id>', methods=['DELETE'])
def delete_cage(cage_id):
    cage = Cage.query.get_or_404(cage_id)
    try:
        # 将该笼位中的所有小鼠移动到临时区
        mice = Mouse.query.filter_by(cage_id=cage_id).all()
        for mouse in mice:
            mouse.cage_id = None
        db.session.delete(cage)
        db.session.commit()
        return jsonify({'message': f'Cage {cage_id} deleted successfully'})
    except Exception as e:
        logger.error(f"删除笼位失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 更新笼位API
@app.route('/api/cages/<int:cage_id>', methods=['PUT'])
def update_cage(cage_id):
    cage = Cage.query.get_or_404(cage_id)
    if not cage:
        return jsonify({'error': 'Cage not found'}), 404
    data = request.json
    try:
        cage.cage_id = data.get('cage_id')
        cage.location = data.get('location')
        cage.section = data.get('section')
        cage.cage_type = data.get('cage_type')
        if 'mice_birth_date' in data:
            cage.mice_birth_date = datetime.strptime(data['mice_birth_date'], '%Y-%m-%d').date() if data.get('mice_birth_date') else None
        if 'mice_count' in data:
            cage.mice_count = int(data['mice_count']) if data.get('mice_count') not in (None, "") else None
        if 'mice_sex' in data:
            cage.mice_sex = data.get('mice_sex')
        if 'mice_genotype' in data:
            cage.mice_genotype = data.get('mice_genotype')
        db.session.commit()
        return jsonify({
            'id': cage.id,
            'cage_id': cage.cage_id,
            'section': cage.section,
            'location': cage.location,
            'cage_type': cage.cage_type,
            'mice_birth_date': cage.mice_birth_date.strftime('%Y-%m-%d') if cage.mice_birth_date else None,
            'mice_count': cage.mice_count,
            'mice_sex': cage.mice_sex,
            'mice_genotype': cage.mice_genotype
        })
    except Exception as e:
        logger.error(f"更新笼位失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 更新笼位排序
@app.route('/api/cages/order', methods=['PUT'])
def update_cage_order():
    try:
        id_from = request.json['id_from']
        id_to = request.json['id_to']
        cage_from = Cage.query.get_or_404(id_from)
        cage_to = Cage.query.get_or_404(id_to)
        temporary = cage_from.order
        cage_from.order = cage_to.order
        cage_to.order = temporary
        db.session.commit()
        return jsonify({'message': 'successfully'})
    except Exception as e:
        logger.error(f"调整笼位排序失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



#小鼠详细视图
#显示谱系图、体重变化图、状态记录
@app.route('/api/mice/<int:mouse_tid>', methods=['GET'])
def get_mice_info(mouse_tid):
    content = {}
    try:
        mouse = Mouse.query.get_or_404(mouse_tid)
        if mouse.cage_id is None:
            c_cage = None
        else:
            c_cage = Cage.query.get_or_404(mouse.cage_id)
        content['id'] = mouse.id
        content['genotype'] = mouse.get_full_genotype()
        content['sex'] = mouse.sex
        content['live_status'] = mouse.live_status
        if c_cage:
            content['cage_id'] = c_cage.cage_id
            content['cage_section'] = c_cage.section
        if mouse.birth_date:
            content['birth_date'] = mouse.birth_date.strftime('%Y-%m-%d')
        if mouse.tests_done:
            tests = []
            for t in mouse.tests_done:
                et = ExperimentType.query.get(t.experiment_id)
                if et:
                    tests.append(et.name)
            content['tests_done'] = tests
        else:
            content['tests_done'] = []
        mid, father, mother, offspring = None, None, None, None
        pedigree = Pedigree.query.filter_by(mouse_id=mouse.tid).all()
        if pedigree:
            mid = pedigree[0].mouse_id
            father = [p.parent_id for p in pedigree if p.parent_type == 'father']
            mother = [p.parent_id for p in pedigree if p.parent_type == 'mother']
        after = Pedigree.query.filter_by(parent_id = mouse.tid).all()
        if after:
            offspring = [a.mouse_id for a in after]
        content['pedigree'] = {
            'mouse_id': mid,
            'father_id': father,
            'mother_id': mother,
            'offspring': offspring
        }
        # 按日期排序体重记录
        weight_records = WeightRecord.query.filter_by(
            mouse_id=mouse.tid
        ).order_by(WeightRecord.record_livingdays).all()
        # 按日期排序状态记录
        status_records = StatusRecord.query.filter_by(
            mouse_id=mouse.tid
        ).order_by(StatusRecord.record_livingdays.desc()).all()
        content['weight_records'] = [{
            'id': w.id,
            'weight': w.weight,
            'record_livingdays': w.record_livingdays
        } for w in weight_records]
        content['status_records'] = [{
            'id': s.id,
            'status': s.status,
            'record_livingdays': s.record_livingdays
        } for s in status_records]
        return jsonify(content)
    except Exception as e:
        logger.error(f"获取小鼠详细信息失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

#删除小鼠状态记录
@app.route('/api/status_records/<int:record_id>', methods=['DELETE'])
def delete_status_record(record_id):
    record = StatusRecord.query.get_or_404(record_id)
    if not record:
        return jsonify({'error': 'Status record not found'}), 404
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Status record deleted successfully'})
    except Exception as e:
        logger.error(f"删除小鼠状态失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

#添加小鼠状态记录
@app.route('/api/status_records', methods=['POST'])
def add_status_record():
    data = request.json
    if not data or 'mouse_tid' not in data or 'status' not in data:
        return jsonify({'error': 'Invalid request format. Expected mouse_tid, status and birth_date.'}), 400
    try:
        birth_date = Mouse.query.get_or_404(data['mouse_tid']).birth_date
        record_date = datetime.strptime(data['record_date'], '%Y-%m-%d').date()
        record_livingdays = (record_date - birth_date).days if birth_date else 0
        record = StatusRecord(
            mouse_id=data['mouse_tid'],
            record_date=record_date,
            record_livingdays=record_livingdays,
            status=data['status']
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({
            'mouse_tid': record.mouse_id,
            'record_livingdays': record.record_livingdays,
            'status': record.status
        }), 201
    except Exception as e:
        logger.error(f"添加小鼠状态失败: {str(e)}")
        return jsonify({'error': str(e)}), 500



#体重表录入视图
@app.route('/api/weight', methods=['POST'])
def add_weight_records():
    data = request.json
    if not data or 'records' not in data:
        return jsonify({'error': 'Invalid request format. Expected a "records" array.'}), 400
    
    records = data['records']
    if not isinstance(records, list) or len(records) == 0:
        return jsonify({'error': 'Records must be a non-empty array.'}), 400
    
    try:
        # 批量创建记录
        for record_data in records:
            mouse = Mouse.query.get(record_data['mouse_id'])
            if not mouse:
                logger.warning(f"Mouse {record_data['mouse_id']} not found, skipping record.")
                continue
                
            # 计算活着的天数（record_date减去出生日期）
            record_date = datetime.strptime(record_data['record_date'], '%Y-%m-%d').date()

            if mouse.birth_date:
                living_days = (record_date - mouse.birth_date).days
            else:
                living_days = 0
                logger.warning(f"Mouse {mouse.id} has no birth date, setting living_days to None.")

            record = WeightRecord(
                mouse_id=record_data['mouse_id'],
                weight=record_data['weight'],
                record_date=record_date,
                record_livingdays=living_days
            )
            db.session.add(record)
        
        db.session.commit()
        return jsonify({'message': f'Successfully added {len(records)} weight records'}), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"体重录入失败: {str(e)}")
        return jsonify({'error': 'Failed to add weight records', 'details': str(e)}), 500

@app.route('/api/weight', methods=['GET'])
def get_weight_records():
    records = WeightRecord.query.all()
    return jsonify([{
        'mouse_id': r.mouse_id,
        'weight': r.weight,
        'record_livingdays': r.record_livingdays
    } for r in records])

@app.route('/api/lived_mice', methods=['GET'])
def get_lived_mice():
    try:
        mice = Mouse.query.outerjoin(Cage).filter(Mouse.live_status == 1).filter(Mouse.birth_date).order_by(
                db.case((Cage.section.is_(None), 1), else_=0),
                Cage.section.asc(),
                Cage.order.asc(),
                Mouse.id.asc()
            ).all()

        mice_data = []
        for mouse in mice:
            # 处理临时区小鼠
            if mouse.cage_id is None:
                section = "临时区"
                cage_name = None
            else:
                section = mouse.cage.section
                cage_name = mouse.cage.cage_id
            
            mice_data.append({
                'tid': mouse.tid,
                'id': mouse.id,
                'genotype': mouse.get_full_genotype(),
                'sex': mouse.sex,
                'cage_name': cage_name,
                'section': section
            })
            
        return jsonify(mice_data)
    except Exception as e:
        logger.error(f"获取存活小鼠列表失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500
    


#生存视图
@app.route('/api/survival-analysis', methods=['POST'])
def get_survival_data():
    data = request.json
    try:
        mice = Mouse.query.filter((Mouse.live_status == 0) | (Mouse.live_status == 1)).all()
        survival_data = [[] for _ in data['groups']]
        for mouse in mice:
            if mouse.live_status == 0:
                if mouse.birth_date and mouse.death_date:
                    living_days = (mouse.death_date - mouse.birth_date).days
                    status = 1
                else:
                    continue  # 如果没有出生或死亡日期，跳过该记录
            else:
                if mouse.birth_date:
                    living_days = (datetime.now().date() - mouse.birth_date).days
                    status = 0
                else:
                    continue
            for index, g in enumerate(data['groups']):
                if mouse.tid in g:
                    survival_data[index].append({
                        'tid': mouse.tid,
                        'mouse_id': mouse.id,
                        'sex': mouse.sex,
                        'genotype': mouse.get_full_genotype(),
                        'living_days': living_days,
                        'status': status
                    })
        # 计算生存分析结果
        analysis_result = calculate_survival_analysis(survival_data)
        
        return jsonify(analysis_result), 200
    except Exception as e:
        logger.error(f"获取生存数据失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500

def calculate_survival_analysis(mice_data):
    """
    计算生存分析结果
    """
    # 初始化分组结果
    group_results = []

    # 为每个分组初始化统计数据
    for i, group in enumerate(mice_data):
        group_results.append({
            'mice': group,
            'allMice': len(group),
            'deadMice': sum(1 for mouse in group if mouse['status'] == 1),
            'censoredMice': sum(1 for mouse in group if mouse['status'] == 0),
            'maxDays': max((mouse['living_days'] for mouse in group), default=0),
            'ls50': 0,
            'survivalData': [],
            'censoredPoints': []
        })
    
    # 为每个分组计算生存曲线
    for group in group_results:
        if group['allMice'] > 0:
            # 按生存时间排序
            sorted_data = sorted(group['mice'], key=lambda x: x['living_days'])
            
            cumulative_survival = 1.0
            at_risk = len(sorted_data)
            ls50_found = False
            
            # 添加起始点
            group['survivalData'].append({
                'x': 0, 
                'y': 1.0, 
                'mouseIds': [],
                'at_risk': at_risk
            })
            
            i = 0
            while i < len(sorted_data):
                mouse = sorted_data[i]
                
                # 处理删失事件
                if mouse['status'] == 0:
                    if len(group['censoredPoints']) == 0:
                        group['censoredPoints'].append({
                            'x': mouse['living_days'],
                            'y': cumulative_survival,
                            'mouseIds': [mouse['mouse_id']],
                            'at_risk': at_risk
                        })
                    elif cumulative_survival == group['censoredPoints'][-1]['y'] and mouse['living_days'] == group['censoredPoints'][-1]['x']:
                        group['censoredPoints'][-1]['mouseIds'].append(mouse['mouse_id'])
                    else:
                        group['censoredPoints'].append({
                            'x': mouse['living_days'],
                            'y': cumulative_survival,
                            'mouseIds': [mouse['mouse_id']],
                            'at_risk': at_risk
                        })
                    at_risk -= 1
                    i += 1
                    continue
                
                # 查找同一时间点的所有死亡事件
                current_time = mouse['living_days']
                deaths_at_time = []
                j = i
                while j < len(sorted_data) and sorted_data[j]['living_days'] == current_time:
                    if sorted_data[j]['status'] == 1:
                        deaths_at_time.append(sorted_data[j])
                    j += 1
                
                # 计算生存率
                if at_risk > 0:
                    survival_rate = 1 - (len(deaths_at_time) / at_risk)
                    cumulative_survival *= survival_rate
                    
                    # 添加数据点
                    group['survivalData'].append({
                        'x': current_time,
                        'y': cumulative_survival,
                        'mouseIds': [m['mouse_id'] for m in deaths_at_time],
                        'at_risk': at_risk,
                        'deaths': len(deaths_at_time)
                    })
                    
                    # 记录中位生存时间
                    if not ls50_found and cumulative_survival <= 0.5:
                        group['ls50'] = current_time
                        ls50_found = True
                    
                    at_risk -= len(deaths_at_time)
                    i += len(deaths_at_time)
                else:
                    break

            # 添加终点 - 确保曲线延伸到最长观察时间
            if sorted_data:
                max_time = max(mouse['living_days'] for mouse in sorted_data)
                last_point = group['survivalData'][-1]
                
                # 如果最后一个点的时间小于最大观察时间，添加终点
                if last_point['x'] < max_time:
                    group['survivalData'].append({
                        'x': max_time,
                        'y': last_point['y'],  # 保持相同的生存率
                        'mouseIds': [],
                        'at_risk': at_risk
                    })    
                # 如果没有找到中位生存时间
                if not ls50_found:
                    group['ls50'] = ">{}".format(group['maxDays'])
        else:
            group['error'] = "所选组别无小鼠"
    
    # 构建返回结果
    result = {
        'success': True,
        'group_results': group_results
    }
    return result



# 基因型管理API
@app.route('/api/gene', methods=['GET'])
def get_genes():
    try:
        genotypes = GeneLocus.query.all()
        return jsonify([g.to_dict() for g in genotypes])
    except Exception as e:
        logger.error(f"获取基因型失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500

@app.route('/api/gene', methods=['POST'])
def add_gene():
    try:
        data = request.json
        if not data.get('symbol'):
            return jsonify({'error': '基因位点名称不能为空'}), 400
        
        locus = GeneLocus(symbol=data['symbol'], description=data.get('description', ''))
        db.session.add(locus)
        db.session.flush()
        a_l = Allele(symbol = "+", locus_id = locus.id, description = "野生型，未修饰", is_wildtype = True)
        db.session.add(a_l)
        db.session.commit()
        return jsonify(locus.to_dict()), 201
    except Exception as e:
        logger.error(f"创建基因位点失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '创建基因位点失败'}), 500

@app.route('/api/<int:id>/gene_allele', methods=['POST'])
def add_allele(id):
    data = request.json
    if not data.get('symbol'):
        return jsonify({'error': '基因修饰名称不能为空'}), 400
    locus = GeneLocus.query.get_or_404(id)

    a_l = Allele(symbol = data['symbol'], locus_id = locus.id, description = data.get('description', ''), is_wildtype = data.get('is_wildtype', False))
    db.session.add(a_l)
    db.session.commit()
    return jsonify(a_l.to_dict()), 201

@app.route('/api/gene/<int:id>', methods=['PUT'])
def update_gene(id):
    data = request.json
    gene = GeneLocus.query.get_or_404(id)
    
    if 'symbol' in data:
        gene.symbol = data['symbol']
    if 'description' in data:
        gene.description = data['description']
    
    db.session.commit()
    return jsonify(gene.to_dict())

@app.route('/api/gene_allele/<int:allele_id>', methods=['PUT'])
def update_allele(allele_id):
    data = request.json
    try:
        gene = Allele.query.get_or_404(allele_id)
        
        if 'symbol' in data:
            gene.symbol = data['symbol']
        if 'description' in data:
            gene.description = data['description']
        if 'is_wildtype' in data:
            gene.is_wildtype = data['is_wildtype']
        db.session.commit()
        return jsonify(gene.to_dict())
    except:
        logger.error(f"更新基因位点失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '获取数据失败'}), 404

@app.route('/api/gene/<int:id>', methods=['DELETE'])
def delete_gene(id):
    try:
        gene = GeneLocus.query.get_or_404(id)
        Genotype.query.filter_by(locus_id=gene.id).delete()
        Allele.query.filter_by(locus_id=gene.id).delete()
        db.session.delete(gene)
        db.session.commit()
        return '', 204
    except:
        logger.error(f"删除基因位点失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '获取数据失败'}), 404
    
@app.route('/api/gene_allele/<int:id>', methods=['DELETE'])
def delete_allele(id):
    try:
        allele = Allele.query.get_or_404(id)
        genotypes = Genotype.query.all()
        for genotype in genotypes:
            if genotype.contains_allele(allele.id):
                db.session.delete(genotype)
        db.session.delete(allele)
        db.session.commit()
        return '', 204
    except:
        logger.error(f"删除等位基因失败: {str(e)}")
        db.session.rollback()
        return 404

# 位置管理API
@app.route('/api/locations', methods=['GET'])
def get_locations():
    try:
        locations = Location.query.order_by(Location.order.asc()).all()
        return jsonify([l.to_dict() for l in locations]), 200
    except Exception as e:
        logger.error(f"获取区域失败: {str(e)}")
        return jsonify({'error': f'获取位置失败: {str(e)}'}), 404

@app.route('/api/locations', methods=['POST'])
def add_location():
    data = request.json
    if not data.get('identifier'):
        return jsonify({'error': '位置标识不能为空'}), 400
    try:
        # 获取当前最大的 order 值
        max_order = db.session.query(db.func.max(Location.order)).scalar()
        
        # 如果没有记录，max_order 会是 None
        new_order = max_order + 1 if max_order is not None else 0
        
        # 创建新位置，设置 order
        location = Location(
            identifier=data['identifier'],
            description=data.get('description', ''),
            order=new_order
        )
        db.session.add(location)
        db.session.commit()
        return jsonify(location.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加区域失败: {str(e)}")
        return jsonify({'error': f'添加位置失败: {str(e)}'}), 500

@app.route('/api/locations/<int:id>', methods=['PUT'])
def update_location(id):
    data = request.json
    try:
        location = Location.query.get_or_404(id)
        
        if 'identifier' in data:
            cages = Cage.query.filter(Cage.section == location.identifier).all()
            location.identifier = data['identifier']
            for cage in cages:
                cage.section = location.identifier
        if 'description' in data:
            location.description = data['description']
        
        db.session.commit()
        return jsonify(location.to_dict())
    except Exception as e:
        logger.error(f"更新区域失败: {str(e)}")
        return jsonify({'error': f'更新位置失败: {str(e)}'}), 500

@app.route('/api/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    try:
        location = Location.query.get_or_404(id)
        cages = Cage.query.filter_by(section=location.identifier).all()
        db.session.delete(location)
        for cage in cages:
            # 将该笼位中的所有小鼠移动到临时区
            mice = Mouse.query.filter_by(cage_id=cage.id).all()
            for mouse in mice:
                mouse.cage_id = None
            db.session.delete(cage)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加区域失败: {str(e)}")
        return jsonify({'error': f'添加位置失败: {str(e)}'}), 500

# 数据导出API
@app.route('/api/export/<export_type>', methods=['GET'])
def export_data(export_type):
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    export_format = request.args.get('format', 'xlsx')
    
    # 根据导出类型准备数据
    if export_type == 'mice':
        query = Mouse.query.order_by(
            Mouse.birth_date.is_(None),
            Mouse.birth_date.asc()
        )
        filename = 'mice_export'
    elif export_type == 'weights':
        query = WeightRecord.query
        filename = 'weights_export'
    elif export_type == 'records':
        query = StatusRecord.query
        filename = 'records_export'
    elif export_type == 'survival':
        # 生存表需要特殊处理
        mice = Mouse.query.all()
        now = datetime.now().date()
        data = []
        for m in mice:
            if m.birth_date is None:
                continue
            if m.live_status == 0:
                data.append({
                    'mouse_id': m.id,
                    'genotype': m.get_genotype_str(),
                    'birth_date': m.birth_date,
                    'death_date': m.death_date,
                    'live_status': m.live_status,
                    'survival_days': (m.death_date - m.birth_date).days if m.death_date else None
                })
            elif m.live_status == 1:
                data.append({
                    'mouse_id': m.id,
                    'genotype': m.get_genotype_str(),
                    'birth_date': m.birth_date,
                    'death_date': m.death_date,
                    'live_status': m.live_status,
                    'survival_days': (m.death_date - m.birth_date).days if m.death_date else (now - m.birth_date).days
                })
        df = pd.DataFrame(data)
        return create_export_file(df, export_format, filename='survival_export')
    elif export_type == 'experiment':
        ids = request.args.getlist('experiment_ids[]')
        ids = [int(id) for id in ids] if ids else []
        return export_experiments_to_excel(ids)
    else:
        return jsonify({'error': '无效的导出类型'}), 400

    # 应用日期过滤
    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        if not end_date:
            end_dt = datetime.max.date()
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        if not start_date:
            start_dt = datetime.min.date()
    if start_date or end_date:
        try:
            if export_type == 'mice':
                query = query.filter(Mouse.birth_date.between(start_dt, end_dt))
            elif export_type == 'weights':
                query = query.filter(WeightRecord.record_date.between(start_dt, end_dt))
            elif export_type == 'records':
                query = query.filter(StatusRecord.record_date.between(start_dt, end_dt))
        except ValueError:
            return jsonify({'error': '无效的日期格式'}), 400
    
    data = [row.to_dict() for row in query.all()]
    if export_type == 'mice':
        for index in range(len(data)):
            tid = data[index]['cage_id']
            if not tid:
                data[index]['cage_id'] = ""
                data[index]['location'] = ""
            else:
                cage = Cage.query.get_or_404(tid)
                data[index]['cage_id'] = cage.cage_id
                data[index]['location'] = cage.section
        for index in range(len(data)):
            genotype_str = ""
            mouse = Mouse.query.get_or_404(data[index]['tid'])
            if mouse:
                genotype_str = mouse.get_genotype_str()
            data[index]['genotype_description'] = data[index]['genotype']
            data[index]['genotype'] = genotype_str
        df = pd.DataFrame(data)
        if data:
            base_columns = ['id', 'sex', 'genotype_description', 'live_status', 'birth_date', 'death_date', 'location', 'cage_id', 'strain']
            info_columns = ["tid", "genotype", "tests_done", "tests_planned"]
            df = df[base_columns + info_columns]
    else:
        df = pd.DataFrame(data)
    
    return create_export_file(df, export_format, filename)

def create_export_file(df, export_format, filename):
    """创建导出文件并返回给客户端"""
    if export_format == 'csv':
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f'{filename}.csv', mimetype='text/csv')
    
    elif export_format == 'xlsx':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f'{filename}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    else:
        return jsonify({'error': '不支持的导出格式'}), 400

# 数据导入API
@app.route('/api/import', methods=['POST'])
def import_data():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    # 保存上传的文件
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # 获取导入参数
    import_type = request.form.get('type', 'mice')
    conflict_resolution = request.form.get('conflict_resolution', 'skip')
    
    # 解析Excel文件
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        return jsonify({'error': f'解析Excel文件失败: {str(e)}'}), 400
    
    # 根据导入类型处理数据
    result = {
        'successCount': 0,
        'skippedCount': 0,
        'errors': []
    }
    
    if import_type == 'mice':
        import_mice_data(df, result, conflict_resolution)
    elif import_type == 'weights':
        import_weights_data(df, result, conflict_resolution)
    elif import_type == 'pedigree':
        import_pedigree_data(df, result, conflict_resolution)
    elif import_type == 'record':
        import_record_data(df, result, conflict_resolution)
    else:
        return jsonify({'error': '不支持的导入类型'}), 400
    
    # 清理上传的文件
    os.remove(filepath)
    
    return jsonify(result)

def import_mice_data(df, result, conflict_resolution):
    """导入小鼠数据"""
    required_columns = ['id', 'genotype', 'sex', 'birth_date', 'live_status']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        result['errors'].append({'row': 0, 'message': f'缺少必要列: {", ".join(missing_cols)}'})
        return
    def deal_with_genotype(genotype_str, mouse_tid):
        # 删除旧的基因型记录
        Genotype.query.filter_by(mouse_id=mouse_tid).delete()
        
        if not genotype_str:
            return

        #解析基因型字符串，格式为：{位点1}[等位基因1]/[等位基因2]&{位点2}[等位基因3]/[等位基因4]
        loci = genotype_str.split('&')
        parsed_loci = []
        for locus in loci:
            locus = locus.strip()
            if not locus:
                continue
                
            # 使用正则表达式匹配
            match = re.match(r'\{([^}]+)\}\[([^]]+)\]\/\[([^]]+)\]', locus)
            if match:
                locus_symbol = match.group(1).strip()
                allele1 = match.group(2).strip()
                allele2 = match.group(3).strip()
                parsed_loci.append((locus_symbol, allele1, allele2))
            else:
                match = re.match(r'\{([^}]+)\}', locus)
                if match:
                    locus_symbol = match.group(1).strip()
                    parsed_loci.append((locus_symbol, None, None))
                else:
                    raise ValueError(f"无法解析基因型格式: {locus}")

        for locus_symbol, allele1_sym, allele2_sym in parsed_loci:
            # 查找或创建基因位点
            locus = GeneLocus.query.filter_by(symbol=locus_symbol).first()
            if not locus:
                locus = GeneLocus(symbol=locus_symbol)
                db.session.add(locus)
                db.session.flush()
            if allele1_sym and allele2_sym:
                # 查找或创建等位基因1
                allele1 = Allele.query.filter_by(symbol=allele1_sym, locus_id=locus.id).first()
                if not allele1:
                    allele1 = Allele(symbol=allele1_sym, locus_id=locus.id)
                    db.session.add(allele1)
                    db.session.flush()
                # 查找或创建等位基因2
                allele2 = Allele.query.filter_by(symbol=allele2_sym, locus_id=locus.id).first()
                if not allele2:
                    allele2 = Allele(symbol=allele2_sym, locus_id=locus.id)
                    db.session.add(allele2)
                    db.session.flush()
                # 创建基因型记录
                genotype = Genotype(
                    mouse_id=mouse.tid,
                    locus_id=locus.id,
                    allele1_id=allele1.id,
                    allele2_id=allele2.id
                )
            else:
                # 创建基因型记录
                genotype = Genotype(
                    mouse_id=mouse.tid,
                    locus_id=locus.id
                )
            db.session.add(genotype)

    max_location_order = db.session.query(db.func.max(Location.order)).scalar()
    new_location_order = max_location_order + 1 if max_location_order is not None else 0
    new_location = Location.query.filter_by(identifier=str(datetime.now().date())).first()
    if not new_location:
        new_location = Location(identifier=str(datetime.now().date()), order=new_location_order)
    location_key = True
    for index, row in df.iterrows():
        try:
            # 转换出生日期格式
            if pd.notna(row['birth_date']):
                birth_date = pd.to_datetime(row['birth_date']).date()
            else:
                birth_date = None
            
            # 处理基因型
            genotype_str = str(row['genotype']).strip() if pd.notna(row['genotype']) else None

            mouse = Mouse.query.filter_by(id=row['id']).filter_by(birth_date=birth_date).first()
            if mouse:
                if conflict_resolution == 'skip':
                    result['skippedCount'] += 1
                    continue
                elif conflict_resolution == 'overwrite':
                    # 更新基本字段
                    mouse.sex = str(row['sex']).upper()[0]
                    mouse.live_status = int(row.get('live_status', 1))

                    deal_with_genotype(genotype_str, mouse.tid)
            else:
                # 创建新小鼠
                mouse = Mouse(
                    id=row['id'],
                    sex=str(row['sex']).upper()[0],  # 只取第一个字母
                    birth_date=birth_date,
                    live_status=int(row.get('live_status', 1)),
                    tests_planned = []
                )
                db.session.add(mouse)
                db.session.flush()
                deal_with_genotype(genotype_str, mouse.tid)
            
            # 可选字段
            if 'death_date' in df.columns and pd.notna(row['death_date']) and mouse.live_status != 1:
                mouse.death_date = pd.to_datetime(row['death_date']).date()
            if 'cage_id' in df.columns and pd.notna(row['cage_id']):
                if 'location' in df.columns and pd.notna(row['location']):
                    location = str(row['location'].strip())
                    if location and location != "":
                        existing_location = Location.query.filter_by(identifier=location).first()
                        if not existing_location:
                            max_location_order = db.session.query(db.func.max(Location.order)).scalar()
                            new_location_order = max_location_order + 1 if max_location_order is not None else 0
                            existing_location = Location(identifier=location, order=new_location_order)
                            db.session.add(existing_location)
                            db.session.flush()
                    else:
                        if location_key:
                            location_key = False
                            db.session.add(new_location)
                            db.session.flush()
                        existing_location = new_location
                else:
                    if location_key:
                        location_key = False
                        db.session.add(new_location)
                        db.session.flush()
                    existing_location = new_location
                cage_id = str(row['cage_id'].strip())
                if cage_id and cage_id != "":
                    existing_cage = Cage.query.filter_by(cage_id=cage_id).filter_by(section=existing_location.identifier).first()
                    if not existing_cage:
                        max_order = db.session.query(db.func.max(Cage.order)).scalar()
                        new_order = max_order + 1 if max_order is not None else 0
                        existing_cage = Cage(section=existing_location.identifier, cage_id=cage_id, order=new_order)
                        db.session.add(existing_cage)
                        db.session.flush()
                    mouse.cage_id = existing_cage.id
            else:
                mouse.cage_id = None

            db.session.commit()
            result['successCount'] += 1
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"导入小鼠失败: {str(e)}")
            result['errors'].append({
                'row': index + 2,  # Excel行号从1开始，标题行+1
                'message': f'导入失败: {str(e)}'
            })
    
def import_weights_data(df, result, conflict_resolution):
    """导入体重数据"""
    required_columns = ['id', 'birth_date', 'weight', 'record_date']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        result['errors'].append({'row': 0, 'message': f'缺少必要列: {", ".join(missing_cols)}'})
        return
    
    for index, row in df.iterrows():
        try:
            mouse_id = str(row['id'])
            if pd.notna(row['birth_date']):
                birth_date = pd.to_datetime(row['birth_date']).date()
            else:
                birth_date = None
            # 检查小鼠是否存在
            mouse = Mouse.query.filter_by(id=mouse_id).filter_by(birth_date=birth_date).first()
            if not mouse:
                result['errors'].append({
                    'row': index + 2,
                    'message': f'小鼠ID {mouse_id} 不存在'
                })
                continue
            if pd.notna(row['record_date']):
                record_date = pd.to_datetime(row['record_date']).date()
            else:
                record_date = None
        
            # 计算生存天数
            birth_date = mouse.birth_date
            living_days = (record_date - birth_date).days
            existing = WeightRecord.query.filter(WeightRecord.mouse_id==mouse.tid, WeightRecord.record_livingdays==living_days).first()
            if existing:
                if conflict_resolution == 'skip':
                    result['skippedCount'] += 1
                    continue
                elif conflict_resolution == 'overwrite':
                    existing.weight = float(row['weight'])
                    result['successCount'] += 1
                    continue
            else:
                # 创建体重记录
                weight_record = WeightRecord(
                    mouse_id=mouse.tid,
                    weight=float(row['weight']),
                    record_date=record_date,
                    record_livingdays=living_days
                )
                
                db.session.add(weight_record)
            db.session.commit()
            result['successCount'] += 1
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"导入体重失败: {str(e)}")
            result['errors'].append({
                'row': index + 2,
                'message': f'导入失败: {str(e)}'
            })

def import_record_data(df, result, conflict_resolution):
    """导入记录数据"""
    required_columns = ['id', 'birth_date', 'record', 'record_date']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        result['errors'].append({'row': 0, 'message': f'缺少必要列: {", ".join(missing_cols)}'})
        return
    
    for index, row in df.iterrows():
        try:
            mouse_id = str(row['id'])
            if pd.notna(row['birth_date']):
                birth_date = pd.to_datetime(row['birth_date']).date()
            else:
                birth_date = None
            # 检查小鼠是否存在
            mouse = Mouse.query.filter_by(id=mouse_id).filter_by(birth_date=birth_date).first()
            if not mouse:
                result['errors'].append({
                    'row': index + 2,
                    'message': f'小鼠ID {mouse_id} 不存在'
                })
                continue
            if pd.notna(row['record_date']):
                record_date = pd.to_datetime(row['record_date']).date()
            else:
                record_date = None

            # 计算生存天数
            living_days = (record_date - birth_date).days
            existing = StatusRecord.query.filter(StatusRecord.mouse_id==mouse.tid, StatusRecord.record_livingdays==living_days).first()
            if existing:
                if conflict_resolution == 'skip':
                    result['skippedCount'] += 1
                    continue
                elif conflict_resolution == 'overwrite':
                    existing.status = str(row['record']).strip() if pd.notna(row['record']) else "无"
                    result['successCount'] += 1
                    continue
            else:
                # 创建记录
                status_record = StatusRecord(
                    mouse_id=mouse.tid,
                    status=str(row['record']).strip() if pd.notna(row['record']) else "无", 
                    record_date=record_date,
                    record_livingdays=living_days
                )
                
                db.session.add(status_record)
            db.session.commit()
            result['successCount'] += 1
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"导入小鼠状态失败: {str(e)}")
            result['errors'].append({
                'row': index + 2,
                'message': f'导入失败: {str(e)}'
            })

def import_pedigree_data(df, result, conflict_resolution):
    """导入血统关系数据，逻辑存在明显漏洞！"""
    required_columns = ['mouse_id', 'birth_date', 'father_id', 'mother_id']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        result['errors'].append({'row': 0, 'message': f'缺少必要列: {", ".join(missing_cols)}'})
        return
    
    for index, row in df.iterrows():
        try:
            mouse_id = str(row['mouse_id'])
            birth_date = datetime.strptime(str(row['birth_date'].date()), '%Y-%m-%d').date()
            father_id = str(row['father_id'])
            mother_id = str(row['mother_id'])
            
            # 检查小鼠是否存在
            mouse = Mouse.query.filter_by(id=mouse_id).filter_by(birth_date=birth_date).first()
            if not mouse:
                result['errors'].append({
                    'row': index + 2,
                    'message': f'小鼠ID {mouse_id} 不存在'
                })
                continue
            
            # 检查父母是否存在
            if father_id != 'None' and not Mouse.query.get(father_id):
                result['errors'].append({
                    'row': index + 2,
                    'message': f'父鼠ID {father_id} 不存在'
                })
                continue
                
            if mother_id != 'None' and not Mouse.query.get(mother_id):
                result['errors'].append({
                    'row': index + 2,
                    'message': f'母鼠ID {mother_id} 不存在'
                })
                continue
            
            # 创建或更新血统关系
            pedigree = Pedigree.query.get(mouse_id)
            if pedigree:
                if conflict_resolution == 'skip':
                    result['skippedCount'] += 1
                    continue
                elif conflict_resolution == 'overwrite':
                    pedigree.father_id = father_id if father_id != 'None' else None
                    pedigree.mother_id = mother_id if mother_id != 'None' else None
            else:
                pedigree = Pedigree(
                    mouse_id=mouse_id,
                    father_id=father_id if father_id != 'None' else None,
                    mother_id=mother_id if mother_id != 'None' else None
                )
                db.session.add(pedigree)
            
            db.session.commit()
            result['successCount'] += 1
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"导入小鼠血统关系失败: {str(e)}")
            result['errors'].append({
                'row': index + 2,
                'message': f'导入失败: {str(e)}'
            })

# 添加获取小鼠简要信息的API
@app.route('/api/mice/<int:mouse_tid>/brief', methods=['GET'])
def get_mouse_brief(mouse_tid):
    mouse = Mouse.query.get_or_404(mouse_tid)
    if not mouse:
        return jsonify({'error': 'Mouse not found'}), 404
    
    return jsonify({
        'id': mouse.id,
        'birth_date': mouse.birth_date,
        'genotype': mouse.get_full_genotype(),
        'sex': mouse.sex
    })

# 更新部分顺序
@app.route('/api/locations/order', methods=['PUT'])
def update_sections_order():
    data = request.json
    order_data = data.get('order')
    
    if not order_data:
        return jsonify({'error': '缺少顺序数据'}), 400
    
    try:
        # 批量更新顺序
        for item in order_data:
            section = Location.query.get(item['id'])
            if section:
                section.order = item['order']
        
        db.session.commit()
        return jsonify({'message': '部分顺序已更新'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"调整区域顺序失败: {str(e)}")
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


# 获取体重记录（带筛选和分页）
@app.route('/api/weight_records', methods=['GET'])
def get_weight_record_with_filter():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        mouse_id = request.args.get('mouse_id', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # 构建基础查询
        query = db.session.query(
            WeightRecord, 
            Mouse
        ).join(
            Mouse, WeightRecord.mouse_id == Mouse.tid
        )
        
        # 应用筛选条件
        if mouse_id:
            query = query.filter(Mouse.id.ilike(f'%{mouse_id}%'))
        if start_date:
            query = query.filter(WeightRecord.record_date >= start_date)
        if end_date:
            query = query.filter(WeightRecord.record_date <= end_date)
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        records = query.order_by(WeightRecord.record_date.desc()).offset((page - 1) * limit).limit(limit).all()
        
        # 格式化结果
        result = []
        for record in records:
            weight_record, mouse = record
            result.append({
                'id': weight_record.id,
                'mouse_id': weight_record.mouse_id,
                'weight': weight_record.weight,
                'record_date': weight_record.record_date.isoformat() if weight_record.record_date else None,
                'record_livingdays': weight_record.record_livingdays,
                'mouse_info': {
                    'id': mouse.id,
                    'genotype': mouse.get_full_genotype(),
                    'sex': mouse.sex,
                    'birth_date': mouse.birth_date.isoformat() if mouse.birth_date else None
                }
            })
        
        return jsonify({
            'records': result,
            'total': total,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        logger.error(f"获取体重记录失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500

# 添加体重记录
@app.route('/api/weight_records', methods=['POST'])
def add_weight_record():
    data = request.json
    try:
        # 验证小鼠是否存在
        mouse = Mouse.query.get_or_404(data['mouse_id'])
            
        # 计算生存天数
        record_date = datetime.strptime(data['record_date'], '%Y-%m-%d')
        if mouse.birth_date:
            living_days = (record_date.date() - mouse.birth_date).days
        else:
            living_days = 0
            
        # 创建记录
        record = WeightRecord(
            mouse_id=data['mouse_id'],
            weight=data['weight'],
            record_date=record_date,
            record_livingdays=living_days
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'id': record.id,
            'mouse_id': record.mouse_id,
            'weight': record.weight,
            'record_date': record.record_date.isoformat(),
            'record_livingdays': record.record_livingdays
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加体重记录失败: {str(e)}")
        return jsonify({'error': '添加记录失败'}), 500

# 更新体重记录
@app.route('/api/weight_records/<int:id>', methods=['PUT'])
def update_weight_record(id):
    data = request.json
    try:
        record = WeightRecord.query.get_or_404(id)
            
        # 更新字段
        if 'weight' in data:
            record.weight = data['weight']
        if 'record_date' in data:
            record.record_date = datetime.strptime(data['record_date'], '%Y-%m-%d')
            
            # 重新计算生存天数
            mouse = Mouse.query.get_or_404(record.mouse_id)
            if mouse and mouse.birth_date:
                record.record_livingdays = (record.record_date.date() - mouse.birth_date).days
        
        db.session.commit()
        
        return jsonify({
            'id': record.id,
            'mouse_id': record.mouse_id,
            'weight': record.weight,
            'record_date': record.record_date.isoformat(),
            'record_livingdays': record.record_livingdays
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新体重记录失败: {str(e)}")
        return jsonify({'error': '更新记录失败'}), 500

# 删除体重记录
@app.route('/api/weight_records/<int:id>', methods=['DELETE'])
def delete_weight_record(id):
    try:
        record = WeightRecord.query.get_or_404(id)
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({'message': '记录删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除体重记录失败: {str(e)}")
        return jsonify({'error': '删除记录失败'}), 500
    



# 实验类型相关API
@app.route('/api/experiment-types', methods=['GET'])
def get_experiment_types():
    '''获取所有实验信息'''
    try:
        experiment_types = ExperimentType.query.all()
        return jsonify([et.to_dict() for et in experiment_types])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiment-types', methods=['POST'])
def create_experiment_type():
    try:
        data = request.get_json()
        
        # 检查是否已存在同名实验类型
        existing = ExperimentType.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': '已存在同名实验类型'}), 400
        
        # 创建实验类型
        experiment_type = ExperimentType(
            name=data['name'],
            description=data.get('description', ''),
            is_show=data.get('is_show', False)
        )
        db.session.add(experiment_type)
        db.session.flush()  # 获取ID但不提交
        
        # 创建字段定义
        for field_data in data.get('fields', []):
            field = FieldDefinition(
                experiment_type_id=experiment_type.id,
                field_name=field_data['field_name'],
                data_type=field_data['data_type'],
                unit=field_data.get('unit', ''),
                is_required=field_data.get('is_required', False),
                visualize_type=field_data.get('visualize_type', None),
                display_order=field_data.get('display_order', 0)
            )
            db.session.add(field)
        
        db.session.commit()
        return jsonify(experiment_type.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建实验失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiment-types/<int:id>', methods=['PUT'])
def update_experiment_type(id):
    try:
        data = request.get_json()
        experiment_type = ExperimentType.query.get_or_404(id)
        
        # 检查是否已存在同名实验类型（排除自己）
        existing = ExperimentType.query.filter(
            ExperimentType.name == data['name'],
            ExperimentType.id != id
        ).first()
        if existing:
            return jsonify({'error': '已存在同名实验类型'}), 400
        
        # 清除存在的实验数据
        Experiment.query.filter_by(experiment_type_id = id).delete()

        # 更新实验类型基本信息
        experiment_type.name = data['name']
        experiment_type.description = data.get('description', '')
        experiment_type.is_show = data.get('is_show', False)
        
        # 更新字段定义
        field_ids = []
        for field_data in data.get('fields', []):
            if 'id' in field_data:
                # 更新现有字段
                field = FieldDefinition.query.get_or_404(field_data['id'])
                if field:
                    field.field_name = field_data['field_name']
                    field.data_type = field_data['data_type']
                    field.unit = field_data.get('unit', '')
                    field.is_required = field_data.get('is_required', False)
                    field.visualize_type = field_data.get('visualize_type', None)
                    field.display_order = field_data.get('display_order', 0)
                    field_ids.append(field.id)
            else:
                # 添加新字段
                field = FieldDefinition(
                    experiment_type_id=id,
                    field_name=field_data['field_name'],
                    data_type=field_data['data_type'],
                    unit=field_data.get('unit', ''),
                    is_required=field_data.get('is_required', False),
                    visualize_type = field_data.get('visualize_type', None),
                    display_order=field_data.get('display_order', 0)
                )
                db.session.add(field)
                db.session.flush()
                field_ids.append(field.id)
        
        # 删除不存在的字段
        FieldDefinition.query.filter(
            FieldDefinition.experiment_type_id == id,
            ~FieldDefinition.id.in_(field_ids)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify(experiment_type.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新实验失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiment-types/<int:id>', methods=['DELETE'])
def delete_experiment_type(id):
    try:
        experiment_type = ExperimentType.query.get_or_404(id)
        
        # 检查是否有实验记录使用此类型
        experiment_count = Experiment.query.filter_by(experiment_type_id=id).count()
        if experiment_count > 0:
            return jsonify({'error': '无法删除：已有实验记录使用此类型'}), 400
        
        # 删除字段定义
        FieldDefinition.query.filter_by(experiment_type_id=id).delete()
        
        # 删除实验类型
        db.session.delete(experiment_type)
        db.session.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除实验失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 预设实验类型
@app.route('/api/experiment-types/presets', methods=['GET'])
def get_experiment_presets():
    presets = {
        "xenograft": {
            "name": "异种移植肿瘤测量",
            "description": "裸鼠肿瘤生长测量实验",
            "is_show": True,
            "fields": [
                {"field_name": "肿瘤长径", "data_type": "REAL", "unit": "mm", "is_required": True, "display_order": 1, "visualize_type":"y"},
                {"field_name": "肿瘤短径", "data_type": "REAL", "unit": "mm", "is_required": True, "display_order": 2, "visualize_type":"y"},
                {"field_name": "肿瘤体积", "data_type": "REAL", "unit": "mm³", "is_required": False, "display_order": 3, "visualize_type":"y"},
                {"field_name": "照片路径", "data_type": "TEXT", "is_required": False, "display_order": 4, "visualize_type":""}
            ]
        },
        "rotarod": {
            "name": "转棒实验",
            "description": "小鼠运动协调能力测试",
            "is_show": True,
            "fields": [
                {"field_name": "潜伏期", "data_type": "REAL", "unit": "s", "is_required": True, "display_order": 1, "visualize_type":"y"},
                {"field_name": "跌落速度", "data_type": "REAL", "unit": "rpm", "is_required": True, "display_order": 2, "visualize_type":"y"},
                {"field_name": "跌落次数", "data_type": "INTEGER", "unit": "次", "is_required": False, "display_order": 3, "visualize_type":"y"},
                {"field_name": "最大速度", "data_type": "REAL", "unit": "rpm", "is_required": False, "display_order": 4,  "visualize_type":"x"}
            ]
        },
        "open_field": {
            "name": "旷场实验",
            "description": "小鼠焦虑和探索行为测试",
            "is_show": True,
            "fields": [
                {"field_name": "总活动距离", "data_type": "REAL", "unit": "cm", "is_required": True, "display_order": 1, "visualize_type":"y"},
                {"field_name": "中央区域时间", "data_type": "REAL", "unit": "s", "is_required": True, "display_order": 2, "visualize_type":"y"},
                {"field_name": "站立次数", "data_type": "INTEGER", "unit": "次", "is_required": True, "display_order": 3, "visualize_type":""},
                {"field_name": "粪便粒数", "data_type": "INTEGER", "unit": "粒", "is_required": False, "display_order": 4, "visualize_type":""}
            ]
        },
        "weight_tracking": {
            "name": "体重追踪",
            "description": "用于小鼠体重变化记录分组",
            "is_show": False,
            "fields": [
                {"field_name": "体重", "data_type": "REAL", "unit": "g", "is_required": True, "display_order": 1, "visualize_type":"y"}
            ]
        }
    }
    return jsonify(presets)



#实验视图
@app.route('/api/experiment/<int:experiment_id>', methods=['GET'])
def get_experiment(experiment_id):
    try:
        expr_info = ExperimentType.query.get_or_404(experiment_id)
        return jsonify(expr_info.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/experiment/<int:experiment_id>/data', methods=['GET'])
def get_experiment_data(experiment_id):
    """获取实验数据，并在后端完全处理"""
    try:
        candidate_mice = [ex.mouse_id for ex in ExperimentClass.query.filter_by(experiment_id=experiment_id).all()]
        groups = PredefinedGroup.query.filter_by(experiment_id=experiment_id).first().rules
        mouse_to_group = {}
        for g in groups:
            for m in g['mouseId']:
                if m in candidate_mice:
                    if m in mouse_to_group.keys():
                        mouse_to_group[m].append([g['name'], g['color']])
                    else:
                        mouse_to_group[m] = [[g['name'], g['color']]]
        # 获取实验记录
        experiments = Experiment.query.filter_by(experiment_type_id=experiment_id).all()
        results = []
        for expr in experiments:
            # 获取所有相关值
            values = ExperimentValue.query.filter_by(experiment_id=expr.id).all()
            mid = expr.mouse_id
            # 构建结果字典
            for g in mouse_to_group[mid]:
                result = {
                    '__experimentId': expr.id,
                    'id': mid,
                    'group': g[0],
                    'color': g[1],
                    'researcher': expr.researcher,
                    'field_date': expr.date.isoformat() if expr.date else None,
                    'notes': expr.notes
                }
                # 添加字段值
                for value in values:
                    field_name = "field_" + str(value.field_definition.id)
                    # 根据数据类型获取值
                    if value.field_definition.data_type == 'INTEGER':
                        result[field_name] = value.value_int
                    elif value.field_definition.data_type == 'REAL':
                        result[field_name] = value.value_real
                    elif value.field_definition.data_type == 'TEXT':
                        result[field_name] = value.value_text
                    elif value.field_definition.data_type == 'BOOLEAN':
                        result[field_name] = value.value_bool
                    elif value.field_definition.data_type == 'DATE':
                        result[field_name] = value.value_date.isoformat() if value.value_date else None
                results.append(result)
        return jsonify(results)
    except Exception as e:
        logger.error(f"获取实验数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiments', methods=['POST'])
def input_experiment_records():
    """录入实验数据"""
    try:
        data = request.get_json()
        experiment_type_id = data.get('experiment_type_id')
        records = data.get('records', [])
        
        if not experiment_type_id:
            return jsonify({'error': 'experiment_type_id是必需的'}), 400
        
        # 验证实验类型存在
        experiment_type = ExperimentType.query.get_or_404(experiment_type_id)
        
        # 获取字段定义
        field_definitions = {fd.id: fd for fd in experiment_type.field_definitions}
        
        # 处理每条记录
        for record_data in records:
            mouse_id = record_data.get('mouse_id')
            researcher = record_data.get('researcher', '')
            date_str = record_data.get('date')
            notes = record_data.get('notes', '')
            values = record_data.get('values', {})
            
            if not mouse_id:
                return jsonify({'error': '每条记录必须包含mouse_id'}), 400
            
            # 验证小鼠存在
            Mouse.query.get_or_404(mouse_id)
            
            # 解析日期
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
            except ValueError:
                return jsonify({'error': f'日期格式无效: {date_str}'}), 400
            
            # 创建实验记录
            experiment = Experiment(
                mouse_id=mouse_id,
                experiment_type_id=experiment_type_id,
                researcher=researcher,
                date=date,
                notes=notes
            )
            db.session.add(experiment)
            db.session.flush()  # 获取experiment.id
            
            # 处理字段值
            for field_def_id, value in values.items():
                field_def_id = int(field_def_id)
                if field_def_id not in field_definitions:
                    continue
                
                field_def = field_definitions[field_def_id]
                
                # 创建实验值记录
                exp_value = ExperimentValue(
                    experiment_id=experiment.id,
                    field_definition_id=field_def_id
                )
                
                # 根据数据类型设置值
                if field_def.data_type == 'INTEGER':
                    exp_value.value_int = int(value) if value else None
                elif field_def.data_type == 'REAL':
                    exp_value.value_real = float(value) if value else None
                elif field_def.data_type == 'TEXT':
                    exp_value.value_text = str(value) if value else None
                elif field_def.data_type == 'BOOLEAN':
                    exp_value.value_bool = bool(value) if value else None
                elif field_def.data_type == 'DATE':
                    try:
                        exp_value.value_date = datetime.strptime(value, '%Y-%m-%d').date() if value else None
                    except ValueError:
                        exp_value.value_date = None
                
                db.session.add(exp_value)
        
        db.session.commit()
        return jsonify({'message': '实验记录保存成功', 'count': len(records)})
    except Exception as e:
        db.session.rollback()
        logger.error(f"录入实验数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 部分更新实验记录
@app.route('/api/experiments/<int:experiment_id>', methods=['PATCH'])
def update_experiment(experiment_id):
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '没有提供更新数据'}), 400
        
        # 获取实验记录
        experiment = Experiment.query.get_or_404(experiment_id)
        # 更新基本字段
        if 'researcher' in data:
            experiment.researcher = data['researcher']
        if 'date' in data:
            try:
                experiment.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '无效的日期格式，请使用 YYYY-MM-DD'}), 400
        if 'notes' in data:
            experiment.notes = data['notes']

        # 更新实验值字段
        if 'value' in data:
            value_update = data['value'].get('field_value')
            fdi = data['value'].get('field_definition_id')
            # 验证字段定义是否存在
            field_def = FieldDefinition.query.get_or_404(fdi)
            
            # 查找或创建实验值记录
            experiment_value = ExperimentValue.query.filter_by(
                experiment_id=experiment_id,
                field_definition_id=fdi
            ).first()
            if not experiment_value:
                experiment_value = ExperimentValue(
                    experiment_id=experiment_id,
                    field_definition_id=fdi
                )
                db.session.add(experiment_value)

            # 根据字段类型设置值
            if field_def.data_type == 'INTEGER':
                try:
                    experiment_value.value_int = int(value_update)
                except ValueError:
                    return jsonify({'error': f'字段 {field_def.field_name} 需要整数值'}), 400
            elif field_def.data_type == 'REAL':
                try:
                    experiment_value.value_real = float(value_update)
                except ValueError:
                    return jsonify({'error': f'字段 {field_def.field_name} 需要数值'}), 400
            elif field_def.data_type == 'TEXT':
                experiment_value.value_text = str(value_update)
            elif field_def.data_type == 'BOOLEAN':
                if isinstance(value_update, bool):
                    experiment_value.value_bool = value_update
                elif isinstance(value_update, str):
                    if value_update.lower() in ['true', '1', 'yes']:
                        experiment_value.value_bool = True
                    elif value_update.lower() in ['false', '0', 'no']:
                        experiment_value.value_bool = False
                    else:
                        return jsonify({'error': f'字段 {field_def.field_name} 需要布尔值'}), 400
                else:
                    return jsonify({'error': f'字段 {field_def.field_name} 需要布尔值'}), 400
            elif field_def.data_type == 'DATE':
                try:
                    experiment_value.value_date = datetime.strptime(value_update, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': f'字段 {field_def.field_name} 需要日期值 (YYYY-MM-DD)'}), 400
            else:
                return jsonify({'error': f'未知的数据类型 {field_def.data_type}'}), 400
        db.session.commit()
        return jsonify({
            'message': '记录更新成功',
            'data': experiment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新实验数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 删除实验记录
@app.route('/api/experiments/<int:experiment_id>', methods=['DELETE'])
def delete_experiment(experiment_id):
    try:
        # 获取实验记录
        experiment = Experiment.query.get_or_404(experiment_id)
        
        # 删除实验记录（关联的实验值会自动删除，因为有 cascade='all, delete-orphan'）
        db.session.delete(experiment)
        db.session.commit()
        
        return jsonify({
            'message': '实验记录删除成功',
            'deleted_id': experiment_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除实验数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_experiment_data_by_type(experiment_ids):
    '''获取某些实验类型的所有实验数据，返回DataFrame形式'''
    exp_types = []
    for t in experiment_ids:
        exp_types.append(ExperimentType.query.get_or_404(t))
        
    # 存储每种实验类型的数据
    experiment_dfs = {}
    for exp_type in exp_types:
        experiment_id = exp_type.id
        # 获取该实验类型的所有字段定义（按显示顺序排序）
        field_defs = (db.session.query(FieldDefinition)
                        .filter(FieldDefinition.experiment_type_id == experiment_id)
                        .order_by(FieldDefinition.display_order)
                        .all())
        
        # 获取该类型的所有实验记录
        experiments = Experiment.query.filter(Experiment.experiment_type_id == experiment_id).all()
        
        # 准备数据容器
        data_rows = []
        candidate_mice = [ex.mouse_id for ex in ExperimentClass.query.filter_by(experiment_id=experiment_id).all()]
        groups = PredefinedGroup.query.filter_by(experiment_id=experiment_id).first().rules
        mouse_to_group = {}
        for g in groups:
            for m in g['mouseId']:
                if m in candidate_mice:
                    if m in mouse_to_group.keys():
                        mouse_to_group[m].append(g['name'])
                    else:
                        mouse_to_group[m] = [g['name']]
        for exp in experiments:
            # 获取实验的基本信息
            row_data = {
                'experiment_id': exp.id,
                'mouse_id': Mouse.query.get_or_404(exp.mouse_id).id,
                'group_name': mouse_to_group[exp.mouse_id][0] if len(mouse_to_group[exp.mouse_id])==1 else str(mouse_to_group[exp.mouse_id]),
                'researcher': exp.researcher,
                'date': exp.date,
                'notes': exp.notes
            }
            
            # 获取该实验的所有值
            values = ExperimentValue.query.filter_by(experiment_id = exp.id).all()
            
            # 将值添加到行数据中
            for value in values:
                # 获取字段定义
                field_def = value.field_definition
                
                # 根据数据类型获取正确的值
                if field_def.data_type == 'INTEGER':
                    val = value.value_int
                elif field_def.data_type == 'REAL':
                    val = value.value_real
                elif field_def.data_type == 'TEXT':
                    val = value.value_text
                elif field_def.data_type == 'BOOLEAN':
                    val = value.value_bool
                elif field_def.data_type == 'DATE':
                    val = value.value_date
                else:
                    val = None
                
                # 添加单位信息到列名
                col_name = field_def.field_name
                if field_def.unit:
                    col_name = f"{col_name} ({field_def.unit})"
                
                row_data[col_name] = val
            data_rows.append(row_data)
        
        # 创建DataFrame
        if data_rows:
            df = pd.DataFrame(data_rows)
            
            # 确保所有字段都有列（即使某些实验没有该字段的值）
            for field_def in field_defs:
                col_name = field_def.field_name
                if field_def.unit:
                    col_name = f"{col_name} ({field_def.unit})"
            
            # 重新排序列
            base_columns = ['experiment_id', 'group_name', 'mouse_id', 'researcher', 'date', 'notes']
            field_columns = [f"{fd.field_name} ({fd.unit})" if fd.unit else fd.field_name 
                            for fd in field_defs]
            df = df[base_columns + field_columns]
            
            experiment_dfs[exp_type.name] = df
    
    return experiment_dfs

def export_experiments_to_excel(ids, filename='experiments_export'):
    try:
        # 获取按实验类型分表的数据
        experiment_dfs = get_experiment_data_by_type(ids)

        output = BytesIO()
        # 创建Excel写入器
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 写入每个实验类型的数据到单独的工作表
            for exp_type_name, df in experiment_dfs.items():
                # 清理工作表名称
                sheet_name = clean_sheet_name(exp_type_name)
                
                # 写入工作表
                df.to_excel(writer, index=False, sheet_name=sheet_name)
                
                # 获取工作表对象进行格式设置
                worksheet = writer.sheets[sheet_name]
                
                # 设置列宽（自动调整）
                auto_adjust_column_widths(worksheet)
                
                # 冻结首行
                worksheet.freeze_panes = 'A2'
            
            # 添加汇总工作表
            add_summary_sheet(writer, experiment_dfs)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f'{filename}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        logger.error(f"实验数据导出失败: {str(e)}")
        return jsonify({'error': '导出失败'}), 500

def clean_sheet_name(name):
    """清理工作表名称以符合Excel要求"""
    # 移除非法字符
    illegal_chars = r':\/?*[]'
    for char in illegal_chars:
        name = name.replace(char, '')
    
    # 截断到31字符
    return name[:31]

def auto_adjust_column_widths(worksheet):
    """自动调整列宽"""
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        
        # 计算列的最大宽度
        for cell in column:
            try:
                cell_value = str(cell.value)
                if len(cell_value) > max_length:
                    max_length = len(cell_value)
            except:
                pass
        
        # 设置列宽（加缓冲空间）
        adjusted_width = max_length + 2
        worksheet.column_dimensions[column_letter].width = adjusted_width

def add_summary_sheet(writer, experiment_dfs):
    """添加汇总工作表"""
    summary_data = []
    
    for exp_type_name, df in experiment_dfs.items():
        # 计算日期范围
        min_date = df['date'].min()
        max_date = df['date'].max()
        
        summary_data.append({
            '实验类型': exp_type_name,
            '记录数量': len(df),
            '字段数量': len(df.columns) - 8,  # 减去基础字段
            '最早日期': min_date.strftime('%Y-%m-%d') if pd.notnull(min_date) else '无',
            '最近日期': max_date.strftime('%Y-%m-%d') if pd.notnull(max_date) else '无',
            '小鼠数量': df['mouse_id'].nunique()
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, index=False, sheet_name='汇总')
    
    # 设置汇总工作表格式
    worksheet = writer.sheets['汇总']
    auto_adjust_column_widths(worksheet)
    worksheet.freeze_panes = 'A2'

@app.route('/api/experiments/<int:experiment_id>/grouped_mice', methods=['GET'])
def get_experiment_grouped_mice(experiment_id):
    """获取实验预设分组的信息和小鼠"""
    try:
        predefined_group = PredefinedGroup.query.filter_by(experiment_id=experiment_id).first()
        if predefined_group and predefined_group.Gtype == 'id':
            return jsonify(predefined_group.to_dict()), 200
        else:
            return jsonify({'error': True})
    except Exception as e:
        logger.error(f"获取预设分组数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiments/<int:experiment_id>/mice', methods=['GET'])
def get_experiment_mice(experiment_id):
    """获取实验预设分组的小鼠"""
    try:
        em = ExperimentClass.query.filter_by(experiment_id=experiment_id).all()
        mid = [m.mouse_id for m in em]
        mice = Mouse.query.filter(Mouse.tid.in_(mid)).all()
        return jsonify([m.to_dict() for m in mice]), 200
    except Exception as e:
        logger.error(f"获取实验小鼠数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
        



@app.route('/api/database/clear', methods=['POST'])
def clear_database():
    """
    清空数据库所有数据
    需要前端确认文字 "DELETE ALL DATA"
    """
    try:
        # 获取清空前的记录数
        total_records_before = get_total_records_count()
        
        # 清空所有表数据但保留表结构
        cleared_tables = clear_all_tables(db)
        
        # 获取清空后的记录数
        total_records_after = get_total_records_count()
        
        # 记录清空操作
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'database_clear',
            'records_before': total_records_before,
            'records_after': total_records_after,
            'tables_cleared': cleared_tables
        }
        
        logger.info(f"数据库清空操作: {log_entry}")

        return jsonify({
            'success': True,
            'message': '数据库清空成功',
            'deleted_records': total_records_before - total_records_after,
            'cleared_tables': cleared_tables,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"清空数据库失败: {str(e)}")
        return jsonify({
            'error': '清空数据库失败',
            'details': str(e)
        }), 500

def get_total_records_count():
    """获取数据库中所有表的记录总数"""
    try:
        # 获取数据库引擎
        engine = db.engine
        
        # 获取所有表名
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # 过滤掉 SQLite 系统表
        user_tables = [table for table in tables if not table.startswith('sqlite_')]
        
        total_count = 0
        
        # 对每个表执行 COUNT 查询
        for table in user_tables:
            # 使用 SQLAlchemy 的 text() 函数执行原始 SQL
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            total_count += count
        
        return total_count
    except Exception as e:
        logger.error(f"获取记录总数失败: {str(e)}")
        return 0

def clear_all_tables(db):
    """清空所有表的数据但保留表结构"""
    try:
        # 获取数据库引擎
        engine = db.engine
        
        # 获取所有表名
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # 过滤掉 SQLite 系统表
        user_tables = [table for table in tables if not table.startswith('sqlite_')]
        
        cleared_tables = []
        try:
            # 禁用外键约束（SQLite 特定）
            db.session.execute(text("PRAGMA foreign_keys = OFF"))
            
            # 清空每个表
            for table in user_tables:
                db.session.execute(text(f"DELETE FROM {table}"))
                cleared_tables.append(table)
                logger.info(f"清空表: {table}")
            # 重新启用外键约束
            db.session.execute(text("PRAGMA foreign_keys = ON"))
            # 提交事务
            db.session.commit()
            
            logger.info(f"成功清空 {len(cleared_tables)} 个表")
            return cleared_tables
            
        except Exception as e:
            # 回滚事务
            db.session.rollback()
            # 确保重新启用外键约束
            db.session.execute(text("PRAGMA foreign_keys = ON"))
            logger.error(f"清空表时出错: {str(e)}")
            raise e
            
    except Exception as e:
        logger.error(f"清空数据库失败: {str(e)}")
        raise e
    
@app.route('/api/database', methods=['GET'])
def get_database():
    """获取数据库列表"""
    return jsonify({'databases': db_list, 'current_database': get_db_file()}), 200

@app.route('/api/database/create', methods=['POST'])
def create_database():
    """创建新数据库"""
    db_item = request.get_json()
    database = {
        'projectName': db_item['projectName'],
        'startAt': db_item['startAt'],
        'endAt': db_item['endAt'],
        'readOnly': db_item['readOnly']
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_list[timestamp+'.db'] = database
    config['db']['db_list'] = db_list
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    return jsonify({'message': '数据库创建成功', 'database': database, 'key': timestamp+'.db'}), 201

@app.route('/api/database/<string:db_key>', methods=['PUT'])
def select_database(db_key):
    """选择数据库"""
    if db_key not in db_list:
        return jsonify({'error': '数据库不存在'}), 404
    config['db']['default_db'] = db_key

    # 获取数据库文件信息
    total_records = get_total_records_count()
    stat = os.stat(db_path)
    file_size = stat.st_size
    last_modified = datetime.fromtimestamp(stat.st_mtime)
    config['db']['db_list'][default_db].update({        
        'fileSize': file_size,
        'lastModified': last_modified.strftime('%Y-%m-%d %H:%M:%S'),
        'totalRecords': total_records
    })

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

    return jsonify({'message': f'已切换到新数据库，重启后生效'}), 200

@app.route('/api/database/<string:db_key>', methods=['DELETE'])
def delete_database(db_key):
    """删除数据库"""
    if db_key not in db_list:
        return jsonify({'error': '数据库不存在'}), 404
    if db_key == default_db:
        return jsonify({'error': '无法删除当前使用的数据库'}), 400
    del db_list[db_key]
    config['db']['db_list'] = db_list
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    if os.path.exists(os.path.join(base_dir, db_key)):
        os.remove(os.path.join(base_dir, db_key))
    return jsonify({'message': '数据库删除成功'}), 200

@app.route('/api/database/<string:db_key>', methods=['POST'])
def modify_database(db_key):
    """修改数据库信息"""
    db_item = request.get_json()
    if db_key not in db_list.keys():
        return jsonify({'error': '数据库不存在'}), 404
    
    database = {
        'projectName': db_item['projectName'],
        'startAt': db_item['startAt'],
        'endAt': db_item['endAt'],
        'readOnly': db_item['readOnly']
    }
    db_list[db_key].update(database)
    config['db']['db_list'] = db_list
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    return jsonify({'message': '数据库信息修改成功', 'database': database}), 200

@app.route('/api/database/info', methods=['GET'])
def get_database_info():
    """获取数据库信息"""
    try:
        if not os.path.exists(db_path):
            return jsonify({
                'fileName': 'mice.db',
                'fileSize': 0,
                'lastModified': '文件不存在',
                'recordCount': 0
            })

        total_records = get_total_records_count()

        # 获取数据库文件信息
        stat = os.stat(db_path)
        file_size = stat.st_size
        last_modified = datetime.fromtimestamp(stat.st_mtime)

        info = {
            'fileSize': file_size,
            'lastModified': last_modified,
            'totalRecords': total_records
        }
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        return jsonify({
            'error': '获取数据库信息失败',
            'details': str(e)
        }), 500

@app.route('/api/database/export/<string:key>', methods=['GET'])
def export_database(key):
    """导出数据库文件"""
    try:
        db_path = os.path.join(base_dir, key)
        if not os.path.exists(db_path):
            return jsonify({'error': '数据库文件不存在'}), 404
        
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f'mice_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db',
            mimetype='application/x-sqlite3'
        )
        
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return jsonify({'error': '导出数据库失败'}), 500

@app.route('/api/database/export-log', methods=['GET'])
def export_log_file():
    """导出日志文件"""
    try:
        log_path = os.path.join(base_dir, 'app.log')
        
        if not os.path.exists(log_path):
            return jsonify({'error': '日志文件不存在'}), 404
        
        return send_file(
            log_path,
            as_attachment=True,
            download_name=f'app_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            mimetype='text/plain'
        )
        
    except Exception as e:
        logger.error(f"导出日志文件失败: {str(e)}")
        return jsonify({'error': '导出日志文件失败'}), 500

@app.route('/api/database/import', methods=['POST'])
def import_database():
    """导入数据库文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not file.filename.endswith('.db'):
            return jsonify({'error': '请选择.db格式的数据库文件'}), 400
        
        db_item = json.loads(request.form.get('project_info'))
        version_change = db_item['databaseUpdate']
        timestamp_name = datetime.now().strftime("%Y%m%d_%H%M%S") + '.db'
        if version_change:
            # 保存上传的文件
            import shutil
            file.save(timestamp_name+timestamp_name)
            new_db_path = base_dir / timestamp_name
            shutil.copy2(db_path, new_db_path)
            new_db_url = f"sqlite:///{new_db_path}"
            app.config['SQLALCHEMY_DATABASE_URI'] = new_db_url
        else:
            file.save(timestamp_name)
        database = {
            'projectName': db_item['projectName'],
            'startAt': db_item['startAt'],
            'endAt': db_item['endAt'],
            'readOnly': db_item['readOnly']
        }
        db_list[timestamp_name] = database
        config['db']['db_list'] = db_list
        config['db']['default_db'] = timestamp_name
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        
        if version_change:
            OLD_DB_URL = f"sqlite:///{base_dir / (timestamp_name + timestamp_name)}"
            NEW_DB_URL = f"sqlite:///{base_dir / timestamp_name}"

            migrator = DatabaseMigrator(OLD_DB_URL, NEW_DB_URL)
            clear_all_tables(migrator.for_clear_new_tables())
            migrator.run_migration()
        return jsonify({
            'success': True,
            'message': '数据库导入成功'
        })
    except Exception as e:
        logging.error(f"导入数据库失败: {str(e)}")
        return jsonify({'error': '导入数据库失败', 'details': str(e)}), 500

@app.route('/api/genotypes', methods=['GET'])
def get_all_genotypes():
    """获取所有基因型组合"""
    try:
        genotypes = {}
        loci = GeneLocus.query.all()
        for locus in loci:
            genotypes[locus.symbol] = locus.get_combination()
        return jsonify(genotypes)
    except Exception as e:
        logger.error(f"获取基因型组合失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/temp', methods=['GET'])
def get_temp_groups():
    """
    根据分组条件筛选小鼠 - 精确基因型匹配版本
    """
    try:
        groups_json = request.args.get('groups')
        if not groups_json:
            return jsonify({'error': '缺少分组参数'}), 400
        
        groups = json.loads(groups_json)
        if not isinstance(groups, list):
            return jsonify({'error': '分组参数格式错误'}), 400
        
        results = []
        
        for group in groups:
            # 性别条件
            sex_conditions = []
            if group.get('sex', {}).get('M'):
                sex_conditions.append(Mouse.sex == 'M')
            if group.get('sex', {}).get('F'):
                sex_conditions.append(Mouse.sex == 'F')
            
            if not sex_conditions:
                # 如果没有选择任何性别，跳过这个分组
                results.append([])
                continue
            
            # 基因型条件
            genotype_list = group.get('genotype', [])
            
            # 构建基础查询
            if genotype_list:
                # 如果有基因型条件，需要先找到符合基因型条件的小鼠
                mouse_subqueries = []
                
                for genotype in genotype_list:
                    match = re.match(r'^([^<]+)<sup>([^/]+)/([^<]+)</sup>$', genotype)
                    if match:
                        locus_symbol = match.group(1)
                        allele1_symbol = match.group(2)
                        allele2_symbol = match.group(3)
                        # 查找匹配的基因型
                        subquery = db.session.query(Genotype.mouse_id).join(
                            Genotype.locus
                        ).filter(
                            GeneLocus.symbol == locus_symbol,
                            or_(
                                and_(
                                    Genotype.allele1.has(Allele.symbol == allele1_symbol),
                                    Genotype.allele2.has(Allele.symbol == allele2_symbol)
                                ),
                                and_(
                                    Genotype.allele1.has(Allele.symbol == allele2_symbol),
                                    Genotype.allele2.has(Allele.symbol == allele1_symbol)
                                )
                            )
                        )
                        mouse_subqueries.append(subquery)
                    else:
                        if GeneLocus.query.filter_by(symbol=genotype).first() is None:
                            continue  # 跳过无效的基因型条件
                        subquery = db.session.query(Genotype.mouse_id).join(Genotype.locus).filter(GeneLocus.symbol == genotype)
                        mouse_subqueries.append(subquery)
                
                # 如果有基因型条件，找到符合所有条件的小鼠ID
                if mouse_subqueries:
                    # 取所有子查询的交集
                    common_mice = mouse_subqueries[0]
                    for subq in mouse_subqueries[1:]:
                        common_mice = common_mice.union(subq)
                    
                    common_mice_ids = [m[0] for m in common_mice.distinct().all()]
                    
                    # 查询这些小鼠的详细信息
                    mice = Mouse.query.filter(
                        Mouse.tid.in_(common_mice_ids),
                        or_(*sex_conditions)
                    ).all()
                else:
                    # 如果没有有效的基因型条件，只按性别筛选
                    mice = Mouse.query.filter(
                        or_(*sex_conditions)
                    ).all()
            else:
                # 如果没有基因型条件，只按性别筛选
                mice = Mouse.query.filter(
                    or_(*sex_conditions)).all()
            results.append([m.tid for m in mice])
        return jsonify(results)
    except json.JSONDecodeError:
        return jsonify({'error': '分组参数JSON格式错误'}), 400
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
@app.route('/api/groups/predefined/<int:groups_id>/mice', methods=['GET'])
def get_predefined_mice(groups_id):
    """获取预设分组的信息和小鼠编号"""
    try:
        predefined_group = PredefinedGroup.query.get_or_404(groups_id)
        if predefined_group.Gtype == 'id':
            return jsonify(predefined_group.to_dict()), 200
        elif predefined_group.Gtype == 'rule':
            group_result = []
            all_mice = Mouse.query.all()
            all_mice_tid = [m.tid for m in all_mice]
            for group in predefined_group.rules:
                group_info = {
                    'name':group.get('name', ''),
                    'color':group.get('color', ''),
                }
                group_mice_ids = set(all_mice_tid)
                for rule in group.get('rules', []):
                    rule_query = analyse_rule(rule)
                    if rule_query is None:
                        continue
                    # 应用规则筛选,取交集（AND逻辑）
                    rule_mice_ids = set(rule_query)
                    group_mice_ids = group_mice_ids.intersection(rule_mice_ids)
                group_info['mice'] = list(group_mice_ids)
                group_result.append(group_info)
            return jsonify(group_result), 200
        else:
            return jsonify(), 403
    except Exception as e:
        logger.error(f"获取预设分组数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

def analyse_rule(rule):
    if rule['Rtype'] == 'genotype':
        gene_set = rule.get('genes', [])
        result = []
        for genes in gene_set:
            query = []
            for gene in genes['gene']:
                if gene["locus"]:
                    locus = GeneLocus.query.filter_by(symbol=gene["locus"]).first()
                else:
                    continue
                a1 = gene['allele1']
                a2 = gene['allele2']
                if a1 and a2:
                    query.append(Genotype.query.filter(
                        Genotype.locus_id == locus.id,
                        or_(
                            and_(Genotype.allele1_id == a1, Genotype.allele2_id == a2),
                            and_(Genotype.allele1_id == a2, Genotype.allele2_id == a1)
                        )
                    ))
                elif a1 and not a2:
                    query.append(Genotype.query.filter(
                        Genotype.locus_id == locus.id,
                        or_(Genotype.allele1_id == a1, Genotype.allele2_id == a1)
                    ))
                elif not a1 and a2:
                    query.append(Genotype.query.filter(
                        Genotype.locus_id == locus.id,
                        or_(Genotype.allele1_id == a2, Genotype.allele2_id == a2)
                    ))
                else:
                    query.append(Genotype.query.filter(
                        Genotype.locus_id == locus.id
                    ))
            common_locus = query[0]
            for subq in query[1:]:
                common_locus = common_locus.intersect(subq)
            result.append(common_locus)
        common_mice = result[0]
        for subq in result[1:]:
            common_mice = common_mice.union(subq)
        return [r.mouse_id for r in common_mice.all()]
    elif rule['Rtype'] == 'sex':
        value = rule.get('value')
        if value in ['M', 'F']:
            return [r.tid for r in Mouse.query.filter(Mouse.sex == value).all()]
    elif rule['Rtype'] == 'strain':
        value = rule.get('value')
        if value:
            return [r.tid for r in Mouse.query.filter(Mouse.strain == value).all()]
    elif rule['Rtype'] == 'cage':
        cages = rule.get('cages')
        if value:
            return [r.tid for r in Mouse.query.filter(Mouse.cage_id.in_(cages)).all()]
    elif rule['Rtype'] == 'live_status':
        value = rule.get('value')
        if value is not None:
            return [r.tid for r in Mouse.query.filter(Mouse.live_status == value).all()]
    elif rule['Rtype'] == 'test_planned':
        value = rule.get('test_planned')
        if value is not None:
            result = []
            for t in value:
                m = Mouse.query.filter(Mouse.tests_planned.contains([t]))
                result.append(m)
            common_mice = result[0]
            for subq in result[1:]:
                common_mice = common_mice.union(subq)
            return [r.tid for r in common_mice.all()]
    else:
        return False
    return False

@app.route('/api/groups/predefined/<int:gIndex>', methods=['PUT'])
def modify_predefined_groups(gIndex):
    try:
        editing = request.json
        group_name = editing.get('name', '')
        group_description = editing.get('description', '')
        group_type = editing.get('Gtype', '')
        rules = editing.get('rules', [])
        experiment_id = editing.get('experiment_id', None)
        if experiment_id:
            ExperimentType.query.get_or_404(experiment_id)
        if not (group_name and group_type):
            return jsonify(), 403
        new_rule = PredefinedGroup.query.get_or_404(gIndex)
        new_rule.name = group_name
        new_rule.description = group_description
        new_rule.Gtype = group_type
        new_rule.rules = rules
        new_rule.experiment_id = experiment_id
        db.session.commit()
        return jsonify(), 200
    except json.JSONDecodeError:
        return jsonify({'error': '分组参数JSON格式错误'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"修改预设分组失败: {str(e)}")
        return jsonify({'error': f'修改预设分组失败: {str(e)}'}), 500

@app.route('/api/groups/predefined', methods=['POST'])
def add_predefined_groups():
    try:
        editing = request.json
        group_name = editing.get('name', '')
        group_description = editing.get('description', '')
        group_type = editing.get('Gtype', '')
        rules = editing.get('rules', [])
        experiment_id = editing.get('experiment_id', None)
        if experiment_id:
            ExperimentType.query.get_or_404(experiment_id)
        if group_name and group_type:
            new_rule = PredefinedGroup(
                name = group_name,
                description = group_description,
                Gtype = group_type,
                rules = rules,
                experiment_id = experiment_id
            )
            db.session.add(new_rule)
            db.session.commit()
            return jsonify(), 200
        else:
            return jsonify(), 403
    except json.JSONDecodeError:
        return jsonify({'error': '分组参数JSON格式错误'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"预设分组失败: {str(e)}")
        return jsonify({'error': f'预设分组失败: {str(e)}'}), 500

@app.route('/api/groups/predefined/review', methods=['POST'])
def review_predefined_groups():
    try:
        editing = request.json.get("editing",{})
        candidate = request.json.get("candidate",[])
        if editing['Gtype'] == 'rule':
            group_result = []
            for group in editing['rules']:
                group_mice_ids = set(candidate)
                for rule in group.get('rules', []):
                    rule_query = analyse_rule(rule)
                    if rule_query is None:
                        continue
                    # 应用规则筛选取交集（AND逻辑）
                    rule_mice_ids = set(rule_query)
                    group_mice_ids = group_mice_ids.intersection(rule_mice_ids)
                group_result.append(list(group_mice_ids))
            return jsonify(group_result), 200
        else:
            return jsonify(), 403
    except Exception as e:
        logger.error(f"解析预设分组失败: {str(e)}")
        return jsonify({'error': f'解析预设分组失败: {str(e)}'}), 404

@app.route('/api/groups/predefined', methods=['GET'])
def get_predefined_groups():
    try:
        groups = PredefinedGroup.query.all()
        return jsonify([group.to_dict() for group in groups]), 200
    except Exception as e:
        logger.error(f"获取预设分组失败: {str(e)}")
        return jsonify({'error': f'获取预设分组失败: {str(e)}'}), 404

@app.route('/api/groups/predefined/<int:g_id>', methods=['DELETE'])
def delete_predefined_groups(g_id):
    try:
        pre_group = PredefinedGroup.query.get_or_404(g_id)
        db.session.delete(pre_group)
        db.session.commit()
        return jsonify(), 200
    except Exception as e:
        logger.error(f"删除预设分组失败: {str(e)}")
        return jsonify({'error': f'删除预设分组失败: {str(e)}'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
