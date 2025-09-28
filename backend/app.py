from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from datetime import datetime, date
from models import db, Mouse, Cage, WeightRecord, StatusRecord, Pedigree, Genotype, Location, ExperimentType, FieldDefinition, Experiment, ExperimentClass, ExperimentValue
import os
import sys
from pathlib import Path
import pandas as pd
from io import BytesIO
from sqlalchemy import text
from sqlalchemy.orm import joinedload

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

# 确定基础目录
base_dir = get_base_dir()
db_path = base_dir / 'mice.db'
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
        # 轻量迁移：为缺失字段添加列
        def column_exists(table, col):
            try:
                res = db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()
                return any(row[1] == col for row in res)
            except Exception:
                return False

        # Mouse 表新增列
        mouse_new_columns = [
            ("strain", "TEXT"),
            ("tests_done", "TEXT"),
            ("tests_planned", "TEXT")
        ]
        for col, coltype in mouse_new_columns:
            if not column_exists('mouse', col):
                try:
                    db.session.execute(text(f"ALTER TABLE mouse ADD COLUMN {col} {coltype}"))
                    db.session.commit()
                    print(f"已添加列 mouse.{col}")
                except Exception as e:
                    db.session.rollback()
                    print(f"添加列 mouse.{col} 失败: {e}")

        # Cage 表新增列
        cage_new_columns = [
            ("mice_birth_date", "DATE"),
            ("mice_count", "INTEGER"),
            ("mice_sex", "TEXT"),
            ("mice_genotype", "TEXT")
        ]
        for col, coltype in cage_new_columns:
            if not column_exists('cage', col):
                try:
                    db.session.execute(text(f"ALTER TABLE cage ADD COLUMN {col} {coltype}"))
                    db.session.commit()
                    print(f"已添加列 cage.{col}")
                except Exception as e:
                    db.session.rollback()
                    print(f"添加列 cage.{col} 失败: {e}")
        
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
            print("默认位置已存在")
            
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
            mouse_dict = {
                'tid': m.tid,
                'id': m.id,
                'genotype': m.genotype,
                'sex': m.sex,
                'birth_date': m.birth_date.strftime('%Y-%m-%d') if m.birth_date else None,
                'death_date': m.death_date.strftime('%Y-%m-%d') if m.death_date else None,
                'cage_id': m.cage_id,
                'live_status': m.live_status,
                'father': father,
                'mother': mother,
                'strain': m.strain,
                'tests_done': m.tests_done,
                'tests_planned': m.tests_planned
            }
            mice_data.append(mouse_dict)

        mice_data.sort(key=lambda x: x['tid'], reverse=True)
        return jsonify(mice_data)
    except Exception as e:
        app.logger.error(f"获取小鼠列表失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500

@app.route('/api/mice', methods=['POST'])
def add_mouse():
    data = request.json
    try:
        mouse = Mouse()
        if data['id']:
            mouse.id = data['id']
        else:
            return jsonify({'error': 'Mouse ID is required'}), 400
        if data['genotype']:
            mouse.genotype = data['genotype']
        if data['sex']:
            mouse.sex = data['sex']
        if data['birth_date']:
            mouse.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        mouse.live_status = 1  # 默认新添加的小鼠状态为'活'
        mouse.cage_id = '-1'
        # 新增字段
        mouse.strain = data.get('strain')
        mouse.tests_done = data.get('tests_done')
        mouse.tests_planned = data.get('tests_planned')
        db.session.add(mouse)
        if data['father']:
            for t in data['father']:
                parent = Pedigree()
                parent.mouse_id = mouse.tid
                parent.parent_id = t
                parent.parent_type = 'father'
                db.session.add(parent)
        if data['mother']:
            for t in data['mother']:
                parent = Pedigree()
                parent.mouse_id = mouse.tid
                parent.parent_id = t
                parent.parent_type = 'mother'
                db.session.add(parent)
        db.session.commit()
        return jsonify({
            'id': mouse.id,
            'genotype': mouse.genotype,
            'sex': mouse.sex,
            'birth_date': mouse.birth_date.strftime('%Y-%m-%d') if mouse.birth_date else None,
            'live_status': mouse.live_status,
            'cage_id': mouse.cage_id,
            'strain': mouse.strain,
            'tests_done': mouse.tests_done,
            'tests_planned': mouse.tests_planned
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/mice/<mouse_tid>', methods=['PUT'])
def update_mouse(mouse_tid):
    data = request.json
    mouse = Mouse.query.get(mouse_tid)
    if not mouse:
        return jsonify({'error': 'Mouse not found'}), 404
    
    try:
        mouse.genotype = data.get('genotype', mouse.genotype)
        mouse.sex = data.get('sex', mouse.sex)
        mouse.live_status = data.get('live_status', mouse.live_status)
        if data['birth_date']:
            mouse.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        if data['death_date']:
            mouse.death_date = datetime.strptime(data['death_date'], '%Y-%m-%d').date()
        # 新增字段
        if 'strain' in data:
            mouse.strain = data.get('strain')
        if 'tests_done' in data:
            mouse.tests_done = data.get('tests_done')
        if 'tests_planned' in data:
            mouse.tests_planned = data.get('tests_planned')
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
        return jsonify({
            'tid': mouse.tid,
            'id': mouse.id,
            'genotype': mouse.genotype,
            'sex': mouse.sex,
            'birth_date': mouse.birth_date.strftime('%Y-%m-%d') if mouse.birth_date else None,
            'father': data.get('father'),
            'mother': data.get('mother'),
            'strain': mouse.strain,
            'tests_done': mouse.tests_done,
            'tests_planned': mouse.tests_planned
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/mice/<mouse_tid>', methods=['DELETE'])
def delete_mouse(mouse_tid):
    mouse = Mouse.query.get(mouse_tid)
    if not mouse:
        return jsonify({'error': 'Mouse not found'}), 404
    try:
        db.session.delete(mouse)
        StatusRecord.query.filter_by(mouse_id=mouse_tid).delete()
        Pedigree.query.filter_by(mouse_id=mouse_tid).delete()
        Pedigree.query.filter_by(parent_id=mouse_tid).delete()
        WeightRecord.query.filter_by(mouse_id=mouse_tid).delete()
        ExperimentClass.query.filter_by(mouse_id=mouse_tid).delete()
        db.session.commit()
        return jsonify({'message': 'Mouse deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 批量添加小鼠
@app.route('/api/mice/<mouse_tid>', methods=['POST'])
def add_mice_from_template(mouse_tid):
    data = request.json
    try:
        template_mouse = Mouse.query.get(mouse_tid)
        template_mouse_parent = Pedigree.query.filter_by(mouse_id=mouse_tid).all()
        for m in data:
            new_mouse_data = template_mouse.to_dict()
            # 移除不需要继承的字段（如主键、创建时间等）
            excluded_fields = ['id', 'tid', 'sex']
            for field in excluded_fields:
                new_mouse_data.pop(field, None)
            new_mouse_data['death_date'] = date.fromisoformat(new_mouse_data['death_date']) if new_mouse_data['death_date'] else None
            new_mouse_data['birth_date'] = date.fromisoformat(new_mouse_data['birth_date']) if new_mouse_data['birth_date'] else None
            new_mouse_data['id'] = m['id']
            new_mouse_data['sex'] = m['sex']
            new_mouse = Mouse(**new_mouse_data)
            db.session.add(new_mouse)
            db.session.flush()
            for p in template_mouse_parent:
                new_parent = Pedigree(
                    mouse_id=new_mouse.tid,
                    parent_id=p.parent_id,
                    parent_type=p.parent_type)
                db.session.add(new_parent)
        db.session.commit()
        return jsonify(), 201
    except Exception as e:
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
                m = Mouse.query.get(mtid)
                if not m:
                    continue
                m.tests_done = test_ids
        elif operation == "计划实验":
            for mtid in mice_ids:
                m = Mouse.query.get(mtid)
                if not m:
                    continue
                m.tests_planned = test_ids
        db.session.commit()
        return jsonify(), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


##笼位视图
@app.route('/api/cages', methods=['GET'])
def get_all_cages():
    # 使用预加载一次性获取所有笼子及其小鼠
    cages = Cage.query.options(joinedload(Cage.mice)).order_by(Cage.order.asc()).all()
    cage_data = []
    for cage in cages:
        mice_info = []
        for mouse in cage.mice:
            if mouse.live_status == 1:
                mice_info.append({
                    'tid': mouse.tid,
                    'id': mouse.id,
                    'genotype': mouse.genotype,
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

@app.route('/api/cages/-1', methods=['GET'])
def get_undetermined_mice():
    # 查找未分配笼子的小鼠
    undetermined_mice = []
    undetermined_mice_query = Mouse.query.filter(Mouse.cage_id == '-1').all()
    for mouse in undetermined_mice_query:
        if mouse.live_status == 1:
            undetermined_mice.append({
                'tid': mouse.tid,
                'id': mouse.id,
                'genotype': mouse.genotype,
                'sex': mouse.sex,
                'days': (datetime.now().date() - mouse.birth_date).days if mouse.birth_date else None
            })
    return jsonify(undetermined_mice)

@app.route('/api/cages', methods=['POST'])
def add_cage():
    data = request.json
    now = datetime.now()
    # 随机ID格式: 年月日时分秒 - 例如: 2024年06月03日15时30分45秒 -> 240603153045
    timestamp = now.strftime("%y%m%d%H%M%S")
    try:
        # 获取当前最大的 order 值
        max_order = db.session.query(db.func.max(Cage.order)).scalar()
        
        # 如果没有记录，max_order 会是 None
        new_order = max_order + 1 if max_order is not None else 0
        cage = Cage(
            id=timestamp,
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
        return jsonify({'message': 'Cage added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/cage/<cage_id>', methods=['PUT'])
def move_mouse(cage_id):
    data = request.json
    mouse = Mouse.query.get(data['mouse_id'])
    if not mouse:
        return jsonify({'error': 'Mouse not found'}), 404
    try:
        mouse.cage_id = cage_id
        db.session.commit()
        return jsonify({'message': f'Mouse {data["mouse_id"]} moved to cage {cage_id}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 删除笼位API
@app.route('/api/cages/<cage_id>', methods=['DELETE'])
def delete_cage(cage_id):
    cage = Cage.query.get(cage_id)
    if not cage:
        return jsonify({'error': 'Cage not found'}), 404
    try:
        # 将该笼位中的所有小鼠移动到临时区
        mice = Mouse.query.filter_by(cage_id=cage_id).all()
        for mouse in mice:
            mouse.cage_id = '-1'
        db.session.delete(cage)
        db.session.commit()
        return jsonify({'message': f'Cage {cage_id} deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 更新笼位API
@app.route('/api/cages/<cage_id>', methods=['PUT'])
def update_cage(cage_id):
    cage = Cage.query.get(cage_id)
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
        return jsonify({'error': str(e)}), 500

# 更新笼位排序
@app.route('/api/cages/order', methods=['PUT'])
def update_cage_order():
    id_from = request.json['id_from']
    id_to = request.json['id_to']
    cage_from = Cage.query.get(id_from)
    cage_to = Cage.query.get(id_to)
    temporary = cage_from.order
    cage_from.order = cage_to.order
    cage_to.order = temporary
    db.session.commit()
    return jsonify({'message': 'successfully'})



#小鼠视图
#显示谱系图、体重变化图、状态记录
@app.route('/api/mice/<mouse_tid>', methods=['GET'])
def get_mice_info(mouse_tid):
    content = {}
    mouse = Mouse.query.get(mouse_tid)
    if mouse.cage_id == '-1' or mouse.cage_id is None:
        c_cage = None
    else:
        c_cage = Cage.query.get(mouse.cage_id)
    if mouse:
        content['id'] = mouse.id
        content['genotype'] = mouse.genotype
        content['sex'] = mouse.sex
        content['live_status'] = mouse.live_status
        if c_cage:
            content['cage_id'] = c_cage.cage_id
            content['cage_section'] = c_cage.section
        if mouse.birth_date:
            content['birth_date'] = mouse.birth_date.strftime('%Y-%m-%d')
    else:
        return jsonify({'error': 'Mouse not found'}), 404
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

#删除小鼠状态记录
@app.route('/api/status_records/<record_id>', methods=['DELETE'])
def delete_status_record(record_id):
    record = StatusRecord.query.get(record_id)
    if not record:
        return jsonify({'error': 'Status record not found'}), 404
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Status record deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#添加小鼠状态记录
@app.route('/api/status_records', methods=['POST'])
def add_status_record():
    data = request.json
    if not data or 'mouse_tid' not in data or 'status' not in data:
        return jsonify({'error': 'Invalid request format. Expected mouse_tid, status and birth_date.'}), 400
    try:
        birth_date = Mouse.query.get(data['mouse_tid']).birth_date
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
            'mouse_tid': record.mouse_tid,
            'record_livingdays': record.record_livingdays,
            'status': record.status
        }), 201
    except Exception as e:
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
                app.logger.warning(f"Mouse {record_data['mouse_id']} not found, skipping record.")
                continue
                
            # 计算活着的天数（record_date减去出生日期）
            record_date = datetime.strptime(record_data['record_date'], '%Y-%m-%d').date()

            if mouse.birth_date:
                living_days = (record_date - mouse.birth_date).days
            else:
                living_days = 0
                app.logger.warning(f"Mouse {mouse.id} has no birth date, setting living_days to None.")

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
        app.logger.error(f"Error adding weight records: {str(e)}")
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
        # 使用JOIN获取笼位信息并排序
        mice = db.session.query(
            Mouse.tid,
            Mouse.id,
            Mouse.genotype,
            Mouse.sex,
            Mouse.cage_id,
            Cage.section,
            Cage.cage_id.label('cage_name'),
            Cage.order.label('cage_order')
        ).outerjoin(
            Cage, Mouse.cage_id == Cage.id
        ).filter(
            Mouse.live_status == 1
        ).order_by(
            db.case(
                (Cage.section.is_(None), 2),  # 没有区域的放最后
                (Mouse.cage_id == '-1', 1),   # 临时区放中间
                else_=0
            ),
            Cage.section.asc(),     # 区域升序排序
            Cage.order.asc(),        # 笼位排序值升序
            Mouse.id.asc()           # 小鼠ID升序
        ).all()

        mice_data = []
        for mouse in mice:
            # 处理临时区小鼠
            if mouse.cage_id == '-1' or mouse.cage_id is None:
                section = "临时区"
                cage_name = None
            else:
                section = mouse.section
                cage_name = mouse.cage_name
            
            mice_data.append({
                'tid': mouse.tid,
                'id': mouse.id,
                'genotype': mouse.genotype,
                'sex': mouse.sex,
                'cage_name': cage_name,
                'section': section
            })
            
        return jsonify(mice_data)
    except Exception as e:
        app.logger.error(f"获取存活小鼠列表失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500
    


#生存视图
@app.route('/api/survival', methods=['GET'])
def get_survival_data():
    try:
        mice = Mouse.query.filter((Mouse.live_status == 0) | (Mouse.live_status == 1)).all()
        survival_data = []
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
            survival_data.append({
                'mouse_id': mouse.id,
                'sex': mouse.sex,
                'genotype': mouse.genotype,
                'living_days': living_days,
                'status': status
            })
        return jsonify(survival_data), 200
    except Exception as e:
        app.logger.error(f"获取生存数据失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500

# 基因型管理API
@app.route('/api/genotypes', methods=['GET'])
def get_genotypes():
    genotypes = Genotype.query.all()
    return jsonify([g.to_dict() for g in genotypes])

@app.route('/api/genotypes', methods=['POST'])
def add_genotype():
    data = request.json
    if not data.get('name'):
        return jsonify({'error': '基因型名称不能为空'}), 400
    
    genotype = Genotype(name=data['name'], description=data.get('description', ''))
    db.session.add(genotype)
    db.session.commit()
    return jsonify(genotype.to_dict()), 201

@app.route('/api/genotypes/<int:id>', methods=['PUT'])
def update_genotype(id):
    data = request.json
    genotype = Genotype.query.get_or_404(id)
    
    if 'name' in data:
        genotype.name = data['name']
    if 'description' in data:
        genotype.description = data['description']
    
    db.session.commit()
    return jsonify(genotype.to_dict())

@app.route('/api/genotypes/<int:id>', methods=['DELETE'])
def delete_genotype(id):
    genotype = Genotype.query.get_or_404(id)
    db.session.delete(genotype)
    db.session.commit()
    return '', 204

# 位置管理API
@app.route('/api/locations', methods=['GET'])
def get_locations():
    locations = Location.query.order_by(Location.order.asc()).all()
    return jsonify([l.to_dict() for l in locations])

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
        return jsonify({'error': f'添加位置失败: {str(e)}'}), 500

@app.route('/api/locations/<int:id>', methods=['PUT'])
def update_location(id):
    data = request.json
    location = Location.query.get_or_404(id)
    
    if 'identifier' in data:
        location.identifier = data['identifier']
    if 'description' in data:
        location.description = data['description']
    
    db.session.commit()
    return jsonify(location.to_dict())

@app.route('/api/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    location = Location.query.get_or_404(id)
    cages = Cage.query.filter_by(section=location.identifier).all()
    db.session.delete(location)
    for cage in cages:
        # 将该笼位中的所有小鼠移动到临时区
        mice = Mouse.query.filter_by(cage_id=cage.id).all()
        for mouse in mice:
            mouse.cage_id = '-1'
        db.session.delete(cage)
    db.session.commit()
    return '', 204

# 数据导出API
@app.route('/api/export/<export_type>', methods=['GET'])
def export_data(export_type):
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    export_format = request.args.get('format', 'xlsx')
    
    # 根据导出类型准备数据
    if export_type == 'mice':
        query = Mouse.query
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
            if m.live_status == 0:
                data.append({
                    'mouse_id': m.id,
                    'genotype': m.genotype,
                    'birth_date': m.birth_date,
                    'death_date': m.death_date,
                    'live_status': m.live_status,
                    'survival_days': (m.death_date - m.birth_date).days if m.death_date else None
                })
            elif m.live_status == 1:
                data.append({
                    'mouse_id': m.id,
                    'genotype': m.genotype,
                    'birth_date': m.birth_date,
                    'death_date': m.death_date,
                    'live_status': m.live_status,
                    'survival_days': (m.death_date - m.birth_date).days if m.death_date else (now - m.birth_date).days
                })
        df = pd.DataFrame(data)
        return create_export_file(df, export_format, filename='survival_export')
    else:
        return jsonify({'error': '无效的导出类型'}), 400
    
    # 应用日期过滤
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if export_type == 'mice':
                query = query.filter(Mouse.birth_date.between(start_dt, end_dt))
            elif export_type == 'weights':
                query = query.filter(WeightRecord.record_date.between(start_dt, end_dt))
        except ValueError:
            return jsonify({'error': '无效的日期格式'}), 400
    
    # 获取数据并转换为DataFrame
    data = [row.to_dict() for row in query.all()]
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
    for index, row in df.iterrows():
        try:
            # 转换出生日期格式
            birth_date = datetime.strptime(str(row['birth_date'].date()), '%Y-%m-%d').date()
            
            existing = Mouse.query.filter_by(id=row['id']).filter_by(birth_date=birth_date).first()
            if existing:
                if conflict_resolution == 'skip':
                    result['skippedCount'] += 1
                    continue
                elif conflict_resolution == 'overwrite':
                    update_existing_mouse(existing, row, result)
                    continue
            # 处理基因型
            genotype = str(row['genotype']).strip() if pd.notna(row['genotype']) else None

            # 检查并创建新基因型
            if genotype and genotype != "":
                existing_genotype = Genotype.query.filter_by(name=genotype).first()
                if not existing_genotype:
                    db.session.add(Genotype(name=genotype))
            if pd.notna(row['id']):
                # 创建新小鼠
                mouse = Mouse(
                    id=row['id'],
                    genotype=genotype,
                    sex=str(row['sex']).upper()[0],  # 只取第一个字母
                    birth_date=birth_date,
                    live_status=int(row.get('live_status', 1))
                )
            else:
                continue
            # 可选字段
            if 'death_date' in df.columns and pd.notna(row['death_date']) and mouse.live_status != 1:
                mouse.death_date = datetime.strptime(str(row['death_date'].date()), '%Y-%m-%d').date()
            
            if 'cage_id' in df.columns and pd.notna(row['cage_id']):
                mouse.cage_id = str(row['cage_id'])
            else:
                mouse.cage_id = '-1'
            
            db.session.add(mouse)
            db.session.commit()
            result['successCount'] += 1
            
        except Exception as e:
            result['errors'].append({
                'row': index + 2,  # Excel行号从1开始，标题行+1
                'message': f'导入失败: {str(e)}'
            })

def update_existing_mouse(existing, row, result):
    """更新现有小鼠记录"""
    try:
        # 更新基本字段
        existing.genotype = str(row['genotype']).strip() if pd.notna(row['genotype']) else None
        existing.sex = str(row['sex']).upper()[0]
        existing.live_status = int(row.get('live_status', 1))
        
        # 处理可选字段
        if 'death_date' in row and pd.notna(row['death_date']):
            existing.death_date = datetime.strptime(str(row['death_date'].date()), '%Y-%m-%d').date()
        
        if 'cage_id' in row and pd.notna(row['cage_id']):
            existing.cage_id = str(row['cage_id'])
        
        # 更新基因型关联
        if existing.genotype:
            existing_genotype = Genotype.query.filter_by(name=existing.genotype).first()
            if not existing_genotype:
                db.session.add(Genotype(name=existing.genotype))
        
        db.session.commit()
        result['successCount'] += 1
        return True
    except Exception as e:
        result['errors'].append({
            'row': index + 2,
            'message': f'更新失败: {str(e)}'
        })
        return False
    
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
            
            # 检查小鼠是否存在
            mouse = Mouse.query.filter_by(id=mouse_id).filter_by(birth_date=datetime.strptime(str(row['birth_date'].date()), '%Y-%m-%d').date()).first()
            if not mouse:
                result['errors'].append({
                    'row': index + 2,
                    'message': f'小鼠ID {mouse_id} 不存在'
                })
                continue

            record_date = datetime.strptime(str(row['record_date'].date()), '%Y-%m-%d').date()

            # 计算生存天数
            birth_date = mouse.birth_date
            living_days = (record_date - birth_date).days
            
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
            result['errors'].append({
                'row': index + 2,
                'message': f'导入失败: {str(e)}'
            })

# 添加获取小鼠简要信息的API
@app.route('/api/mice/<mouse_tid>/brief', methods=['GET'])
def get_mouse_brief(mouse_tid):
    mouse = Mouse.query.get(mouse_tid)
    if not mouse:
        return jsonify({'error': 'Mouse not found'}), 404
    
    return jsonify({
        'id': mouse.id,
        'birth_date': mouse.birth_date,
        'genotype': mouse.genotype,
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
                    'genotype': mouse.genotype,
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
        app.logger.error(f"获取体重记录失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500

# 添加体重记录
@app.route('/api/weight_records', methods=['POST'])
def add_weight_record():
    data = request.json
    try:
        # 验证小鼠是否存在
        mouse = Mouse.query.get(data['mouse_id'])
        if not mouse:
            return jsonify({'error': '小鼠不存在'}), 400
            
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
        app.logger.error(f"添加体重记录失败: {str(e)}")
        return jsonify({'error': '添加记录失败'}), 500

# 更新体重记录
@app.route('/api/weight_records/<int:id>', methods=['PUT'])
def update_weight_record(id):
    data = request.json
    try:
        record = WeightRecord.query.get(id)
        if not record:
            return jsonify({'error': '记录不存在'}), 404
            
        # 更新字段
        if 'weight' in data:
            record.weight = data['weight']
        if 'record_date' in data:
            record.record_date = datetime.strptime(data['record_date'], '%Y-%m-%d')
            
            # 重新计算生存天数
            mouse = Mouse.query.get(record.mouse_id)
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
        app.logger.error(f"更新体重记录失败: {str(e)}")
        return jsonify({'error': '更新记录失败'}), 500

# 删除体重记录
@app.route('/api/weight_records/<int:id>', methods=['DELETE'])
def delete_weight_record(id):
    try:
        record = WeightRecord.query.get(id)
        if not record:
            return jsonify({'error': '记录不存在'}), 404
            
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({'message': '记录删除成功'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"删除体重记录失败: {str(e)}")
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
            description=data.get('description', '')
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
        
        # 更新实验类型基本信息
        experiment_type.name = data['name']
        experiment_type.description = data.get('description', '')
        
        # 更新字段定义
        field_ids = []
        for field_data in data.get('fields', []):
            if 'id' in field_data:
                # 更新现有字段
                field = FieldDefinition.query.get(field_data['id'])
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
        return jsonify({'error': str(e)}), 500

# 预设实验类型
@app.route('/api/experiment-types/presets', methods=['GET'])
def get_experiment_presets():
    presets = {
        "xenograft": {
            "name": "异种移植肿瘤测量",
            "description": "裸鼠肿瘤生长测量实验",
            "fields": [
                {"field_name": "肿瘤长径", "data_type": "REAL", "unit": "mm", "is_required": True, "display_order": 1},
                {"field_name": "肿瘤短径", "data_type": "REAL", "unit": "mm", "is_required": True, "display_order": 2},
                {"field_name": "肿瘤体积", "data_type": "REAL", "unit": "mm³", "is_required": False, "display_order": 3},
                {"field_name": "照片路径", "data_type": "TEXT", "is_required": False, "display_order": 4}
            ]
        },
        "rotarod": {
            "name": "转棒实验",
            "description": "小鼠运动协调能力测试",
            "fields": [
                {"field_name": "潜伏期", "data_type": "REAL", "unit": "s", "is_required": True, "display_order": 1},
                {"field_name": "跌落速度", "data_type": "REAL", "unit": "rpm", "is_required": True, "display_order": 2},
                {"field_name": "跌落次数", "data_type": "INTEGER", "unit": "次", "is_required": False, "display_order": 3},
                {"field_name": "最大速度", "data_type": "REAL", "unit": "rpm", "is_required": False, "display_order": 4}
            ]
        },
        "open_field": {
            "name": "旷场实验",
            "description": "小鼠焦虑和探索行为测试",
            "fields": [
                {"field_name": "总活动距离", "data_type": "REAL", "unit": "cm", "is_required": True, "display_order": 1},
                {"field_name": "中央区域时间", "data_type": "REAL", "unit": "s", "is_required": True, "display_order": 2},
                {"field_name": "站立次数", "data_type": "INTEGER", "unit": "次", "is_required": True, "display_order": 3},
                {"field_name": "粪便粒数", "data_type": "INTEGER", "unit": "粒", "is_required": False, "display_order": 4}
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
    """获取实验数据，以字段为列的形式返回"""
    try:
        # 获取实验记录
        experiments = Experiment.query.filter_by(experiment_type_id=experiment_id).all()
        results = []
        for expr in experiments:
            # 获取所有相关值
            values = ExperimentValue.query.filter_by(experiment_id=expr.id).all()
            # 构建结果字典
            result = {
                'id': expr.id,
                'mouse_id': expr.mouse_id,
                'experiment_type_id': expr.experiment_type_id,
                'researcher': expr.researcher,
                'date': expr.date.isoformat() if expr.date else None,
                'notes': expr.notes
            }
            # 添加字段值
            for value in values:
                field_name = value.field_definition.field_name
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
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/experiment/<int:experiment_id>/candidate_mice', methods=['GET'])
def get_candidate_mice(experiment_id):
    """获取候选池小鼠 - 基于tests_done字段筛选"""
    try:
        # 获取实验信息
        experiment = ExperimentType.query.get_or_404(experiment_id)
        
        query = Mouse.query.filter_by(live_status=1).filter(Mouse.tests_done.contains([experiment.id]))  # 只选择存活的小鼠
        
        candidate_mice = query.all()
        
        # 排除已经在分组中的小鼠
        existing_mice_ids = [ec.mouse_id for ec in 
                            ExperimentClass.query.filter_by(experiment_id=experiment_id).all()]
        
        candidate_mice = [mouse for mouse in candidate_mice if mouse.tid not in existing_mice_ids]
        
        return jsonify([mouse.to_dict() for mouse in candidate_mice])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiment/<int:experiment_id>/groups', methods=['GET'])
def get_experiment_groups(experiment_id):
    """获取实验的所有分组"""
    try:
        # 验证实验是否存在
        ExperimentType.query.get_or_404(experiment_id)
        
        # 获取所有分组
        groups = {}
        experiment_classes = ExperimentClass.query.filter_by(experiment_id=experiment_id).options(
            joinedload(ExperimentClass.mouse)
        ).all()
        
        for ec in experiment_classes:
            if ec.class_id not in groups:
                groups[ec.class_id] = []
            groups[ec.class_id].append(ec.to_dict())
        
        return jsonify(groups)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/experiment/<int:experiment_id>/groups/<oldGroupId>', methods=['PUT'])
def rename_experiment_group(experiment_id, oldGroupId):
    """实验分组改名"""
    new_id = request.get_json()['newGroupId']
    try:
        # 验证实验是否存在
        ExperimentType.query.get_or_404(experiment_id)
        experiment_classes = ExperimentClass.query.filter_by(experiment_id=experiment_id).filter_by(class_id=oldGroupId).all()
        for ec in experiment_classes:
            ec.class_id = new_id
        db.session.commit()
        return jsonify({'message': f'分组 {oldGroupId} 已重命名为 {new_id}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiment/<int:experiment_id>/class_change', methods=['POST'])
def add_mouse_to_group(experiment_id):
    """改变小鼠分组"""
    try:
        data = request.get_json()
        mouse_id = data.get('mouse_id')
        from_class_id = data.get('class_id')
        to_class_id = data.get('class_new_id')
        
        if not mouse_id or (from_class_id and to_class_id):
            return jsonify({'error': 'mouse_id是必需的'}), 400
        
        # 验证实验和小鼠是否存在
        ExperimentType.query.get_or_404(experiment_id)
        Mouse.query.get_or_404(mouse_id)

        if from_class_id:
            # 检查小鼠是否已在分组中
            existing = ExperimentClass.query.filter_by(
                experiment_id=experiment_id, 
                mouse_id=mouse_id,
                class_id=from_class_id
            ).first()
            
            if not existing:
                return jsonify({'error': '该小鼠不在分组中'}), 400
            
            if to_class_id:
                existing.class_id = to_class_id
            else:
                db.session.delete(existing)
        else:
            # 创建新的分组记录
            experiment_class = ExperimentClass(
                mouse_id=mouse_id,
                experiment_id=experiment_id,
                class_id=to_class_id
            )
            db.session.add(experiment_class)
        db.session.commit()
        return jsonify({'message': '小鼠已成功添加到分组', 'id': experiment_class.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiment/<int:experiment_id>/groups/<int:class_id>', methods=['DELETE'])
def delete_group(experiment_id, class_id):
    """删除整个分组"""
    try:
        # 查找并删除该分组的所有记录
        experiment_classes = ExperimentClass.query.filter_by(
            experiment_id=experiment_id,
            class_id=class_id
        ).all()
        
        for ec in experiment_classes:
            db.session.delete(ec)
        
        db.session.commit()
        
        return jsonify({'message': f'分组 {class_id} 已删除', 'deleted_count': len(experiment_classes)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/experiment/<int:experiment_id>/groups/clear', methods=['DELETE'])
def clear_all_groups(experiment_id):
    """清除实验的所有分组"""
    try:
        # 查找并删除该实验的所有分组记录
        experiment_classes = ExperimentClass.query.filter_by(
            experiment_id=experiment_id
        ).all()
        
        for ec in experiment_classes:
            db.session.delete(ec)
        
        db.session.commit()
        
        return jsonify({'message': '所有分组已清除', 'deleted_count': len(experiment_classes)})
    except Exception as e:
        db.session.rollback()
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
                    exp_value.value_int = int(value) if value is not None else None
                elif field_def.data_type == 'REAL':
                    exp_value.value_real = float(value) if value is not None else None
                elif field_def.data_type == 'TEXT':
                    exp_value.value_text = str(value) if value is not None else None
                elif field_def.data_type == 'BOOLEAN':
                    exp_value.value_bool = bool(value) if value is not None else None
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
        experiment = Experiment.query.get(experiment_id)
        if not experiment:
            return jsonify({'error': '实验记录未找到'}), 404
        
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
            field_def = FieldDefinition.query.get(fdi)
            if not field_def:
                return jsonify({'error': f'字段定义 {fdi} 不存在'}), 400
            
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
        # 提交更改
        db.session.commit()
        return jsonify({
            'message': '记录更新成功',
            'data': experiment.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 删除实验记录
@app.route('/api/experiments/<int:experiment_id>', methods=['DELETE'])
def delete_experiment(experiment_id):
    try:
        # 获取实验记录
        experiment = Experiment.query.get(experiment_id)
        if not experiment:
            return jsonify({'error': '实验记录未找到'}), 404
        
        # 删除实验记录（关联的实验值会自动删除，因为有 cascade='all, delete-orphan'）
        db.session.delete(experiment)
        db.session.commit()
        
        return jsonify({
            'message': '实验记录删除成功',
            'deleted_id': experiment_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
