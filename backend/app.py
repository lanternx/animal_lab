from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from datetime import datetime
from models import db, Mouse, Cage, WeightRecord, StatusRecord, Pedigree, Genotype, Location
import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from io import BytesIO


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

with app.app_context():
    db.create_all()


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
                'mother': mother
            }
            mice_data.append(mouse_dict)
            
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
        mouse.cage_id = -1
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
            'cage_id': mouse.cage_id
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
            'father': data['father'],
            'mother': data['mother']
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
        db.session.commit()
        return jsonify({'message': 'Mouse deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


##笼位视图
@app.route('/api/cages', methods=['GET'])
def get_all_cages():
    # 使用预加载一次性获取所有笼子及其小鼠
    cages = Cage.query.options(db.joinedload(Cage.mice)).order_by(Cage.order.asc()).all()
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
            'mice': mice_info
        })
    return jsonify(cage_data)

@app.route('/api/cages/-1', methods=['GET'])
def get_undetermined_mice():
    # 查找未分配笼子的小鼠
    undetermined_mice = []
    undetermined_mice_query = Mouse.query.filter(Mouse.cage_id == -1).all()
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
            order=new_order
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
            mouse.cage_id = -1
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
        db.session.commit()
        return jsonify({
            'id': cage.id,
            'cage_id': cage.cage_id,
            'section': cage.section,
            'location': cage.location,
            'cage_type': cage.cage_type
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
    if mouse.cage_id == -1 or mouse.cage_id is None:
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
            mouse.cage_id = -1
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
    elif export_type == 'survival':
        # 生存表需要特殊处理
        mice = Mouse.query.all()
        data = [{
            'mouse_id': m.id,
            'genotype': m.genotype,
            'birth_date': m.birth_date,
            'death_date': m.death_date,
            'live_status': m.live_status,
            'survival_days': (m.death_date - m.birth_date).days if m.death_date else None
        } for m in mice]
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
            existing = Mouse.query.filter_by(id=row['id']).filter_by(birth_date=datetime.strptime(str(row['birth_date'].date()), '%Y-%m-%d').date()).first()
            if existing:
                if conflict_resolution == 'skip':
                    result['skippedCount'] += 1
                    continue
                elif conflict_resolution == 'overwrite':
                    db.session.delete(existing)
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
                    birth_date=datetime.strptime(str(row['birth_date'].date()), '%Y-%m-%d').date(),
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
                mouse.cage_id = -1
            
            db.session.add(mouse)
            db.session.commit()
            result['successCount'] += 1
            
        except Exception as e:
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
