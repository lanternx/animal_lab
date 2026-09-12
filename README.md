<div align="center">

<img src="./1.png" alt="Logo" width="100">

# 鼠管家MurisPro

**专业的动物房管理系统**

[![版本](https://img.shields.io/badge/版本-3.0.0-blue)]()
[![状态](https://img.shields.io/badge/状态-活跃-success)]()

</div>
一个基于 Flask 和 Vue.js 开发的本地实验动物管理系统，专为生物医学研究设计，提供完整的动物管理、数据分析和可视化功能，造福广大有实验动物需求的朋友。适配 windows 、mac系统。

介绍和[教学视频](https://www.bilibili.com/video/BV1Q12xB6Ep5)

## 特性

- 🐭 完整的实验动物生命周期管理
- 📊 丰富的图表和数据分析功能（体重曲线、生存曲线）
- 🖥️ 跨平台桌面应用（基于 pywebview）
- 📱 响应式设计，支持移动端和桌面端
- 💾 本地数据库存储，数据安全可靠
- 🔍 强大的搜索和筛选功能
- 📁 数据导入导出功能

## 技术栈

### 后端

- Flask - Python Web框架
- Flask-SQLAlchemy - ORM数据库管理
- Flask-CORS - 跨域请求处理
- Pandas - 数据处理和分析
- Openpyxl - Excel 文件操作

### 前端
- Vue 3 - 渐进式 JavaScript 框架
- Vue Router - 路由管理
- Axios - HTTP 客户端
- Chart.js - 图表可视化
- D3.js - 数据可视化
- Material Design Icons - 图标库

### 桌面应用

- PyWebView - 轻量级 Web UI 库
- nuitka - 应用打包工具（后端打包成二进制文件，相比于pyinstaller开启速度更快，避免idna错误）

## 安装与运行

### 普通用户（推荐）

✅ 已提供打包好的桌面版，**无需安装任何依赖**，下载后直接运行：

👉 [立即下载最新版本](https://github.com/lanternx/animal_lab/releases/tag/V3.1)

也可通过[百度网盘](https://pan.baidu.com/s/1x4IIB-TzQbNMMgnmDWLquQ?pwd=2333)下载（包括Windows版和Mac版（仅限Arm64架构（M系列芯片））

Mac版不能直接在Mac上用网盘下载，应该用windows或者安卓手机下载，然后通过U盘拷到Mac上，这样才能避免隔离！！！！否则会出现文件已损坏的错误！

如果是在Mac上直接下载的软件，需要手动解除隔离：

在terminal中输入
```bash
sudo xattr -cr /Applications/MurisPro_V3.1.app
```


### windows 开发者

1. 克隆源码：

```cmd
git clone https://github.com/lanternx/animal_lab.git
```

2. 进入后端目录

```cmd
cd backend 
```

3. 创建虚拟环境

```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate.bat

# 安装依赖包
pip install -r requirements.txt
```

注意：以后每次运行都需要激活虚拟环境，也即在命令行执行 `venv\Scripts\activate.bat`。

4. 利用 npm 安装前端：

```cmd
cd ..
npm install
```

5. 启动开发服务器：

```cmd
npm run serve
```

6. 运行后端：

```bash
cd backend
python app.py
```
然后可在浏览器中打开本项目（localhost:8080）

8. 打包为可执行文件：

```cmd
npm run build
move dist ..\backend\
python build.py
```

### mac 开发者

1. 克隆源码：

```bash
git clone https://github.com/lanternx/animal_lab.git
```

2. 进入后端目录

```bash
cd backend 
```

3. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv ~/.python/sglang

# 激活虚拟环境
source ~/.python/sglang/bin/activate

# 安装 uv
pip install uv
```

注意：以后每次运行都需要激活虚拟环境，也即在命令行执行 `source ~/.python/sglang/bin/activate`。


4. 安装依赖包

```bash
python3 -m uv pip install -r requirements.txt
```

5. 利用 npm 安装前端：

```bash
cd ..
npm install
```

6. 启动开发服务器：

```bash
npm run serve
```

7. 运行后端：

```bash
cd backend
python3 app.py
```

在 `localhost:8080` 上直接访问

打包为可执行文件(打包不要使用mac自带的python)：

```bash
npm run build
mv -i dist ../backend/
python3 build_mac.py --disable-console --app-name "MurisPro_V3.1"
```


## 项目结构

```
MurisPro/
├── backend/           # Flask后端应用
│   ├── dist/         # Vue前端编译产物
│   ├── main.py       # 桌面应用入口
│   ├── app.py        # 主应用文件
│   ├── models.py     # 数据模型
│   ├── build.py
│   └── requirements.txt
├── src/          # Vue前端应用
│   ├── components/
│   ├── views/
│   ├── router/
│   ├── store/
│   └──app.vue
├── package.json
└── vue.config.js
└── README.md
```

## 主要功能

- **笼位视图** - 可视化动物笼位安排和管理
- **小鼠详细页** - 动物个体信息追踪
- **小鼠列表** - 详细的动物信息管理和搜索
- **体重列表** - 详细的体重信息管理和搜索
- **实验模块** - 根据设定的实验自动产生
- **体重曲线** - 动物体重变化追踪和分析
- **生存曲线** - 生存率统计和可视化
- **系统设置** - 应用程序配置和管理

## 数据验证与防篡改

### 概述

MurisPro 提供完整的数据审计链（Audit Trail）和 PDF 防篡改机制，确保实验数据的完整性和可追溯性。

### 审计链（Audit Trail）

系统在数据库层面维护一条不可篡改的审计链：

- **记录范围**：所有 DELETE、UPDATE、IMPORT 操作均被记录，包括操作类型（SQL 语句）、操作前后的数据库文件 SHA256 哈希。
- **链式结构**：每条审计记录的 `record` 字段为 `SHA256(上一条 record)`，形成链式哈希。任何对历史记录的篡改都会导致链断裂。
- **存储位置**：审计数据存储在数据库的 `audit_log` 表中，与业务数据共存。

```
操作前数据库 SHA256 → old_values
操作后数据库 SHA256 → new_values
审计链哈希 → record = SHA256(prev_record)
```

### PDF 导出与认证

导出 PDF 时，系统自动附加一个认证页（Certification Page），包含：

| 字段 | 说明 |
|------|------|
| DB Hash | 导出时数据库文件的 SHA256 哈希 |
| Audit Chain | 审计链中最新的 record 值 |
| DB Name | 数据库文件名 |
| Certified At | 云函数签名时间 |
| Server Signature | ECDSA-P256 签名（由云函数生成） |

签名流程：
1. 前端调用 `GET /api/audit-info` 获取 DB Hash、Audit Chain、数据库名
2. 前端将 `db_hash|record` 发送到云函数（Cloudflare Worker）进行 ECDSA-P256 签名
3. 云函数返回签名和时间戳，前端将认证信息写入 PDF 最后一页

### PDF 校验

在系统设置 → PDF 验证页面，选择一个导出的 PDF 文件即可验证：

1. 后端使用 pypdf 解析 PDF 最后一页的认证信息
2. 在 `audit_log` 表中查找与 PDF 时间相近的 EXPORT 记录
3. 比对 PDF 中的 DB Hash 与 AuditLog 中记录的 `old_values`
4. 比对 PDF 中的 Audit Chain 与 AuditLog 中的 `record`
5. 计算当前数据库文件哈希，检测数据库自导出后是否被修改

校验结果包括：
- 审计链是否匹配
- DB 哈希是否匹配
- 数据库自导出后是否被修改
- 认证时间、数据库名、哈希值详情

### 安全模型

| 攻击场景 | 防护机制 |
|----------|----------|
| 篡改数据库数据 | DB 哈希与审计链不匹配，下次导出 PDF 时可检测 |
| 篡改 PDF 认证页 | ECDSA 签名验证失败（签名由云函数私钥生成） |
| 插入/删除审计记录 | 审计链断裂（record 哈希不连续） |
| 伪造 PDF（从未授权数据库导出） | AuditLog 中无对应 EXPORT 记录 |

## 贡献指南

我们欢迎社区贡献！请阅读以下指南：

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用Apache License 2.0开源许可证 - 查看 LICENSE 文件了解详情。

## 致谢
- 本项目得益于以下优秀开源项目的支持：
  - **Flask生态系统** - 提供简洁高效的Web服务支持
  - **Vue.js框架** - 构建现代化的响应式用户界面
  - **PyWebView团队** - 实现轻量级桌面应用封装
  - **Material Design Icons** - 提供美观的图标资源
  - **Chart.js & D3.js** - 强大的数据可视化能力
  - **SQLAlchemy** - ORM数据库管理解决方案
- 感谢所有贡献者和用户

## 支持

如果您遇到问题或有疑问，请通过以下方式联系我们：
- 提交GitHub Issue
- 发送邮件至项目维护团队
- 社交平台评论或者私信

## 版本历史

- 2.1 - 增加小鼠实验模块，更换打包方式
- 1.2 - 修复了部分bug，提高程序稳健性
- 1.1.1 - 解决端口占用问题，增加了程序的稳健性
- 1.1 - 改进版本发布
- 1.0 - 初始版本发布

---

**注意**: 本项目仍在积极开发中，API和功能可能会有变动。
