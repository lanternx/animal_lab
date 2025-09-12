# 动物房管理系统

一个基于Flask和Vue.js开发的本地实验动物管理系统，专为生物医学研究设计，提供完整的动物管理、数据分析和可视化功能，造福广大有实验动物需求的朋友。

## 特性

- 🐭 完整的实验动物生命周期管理
- 📊 丰富的图表和数据分析功能（体重曲线、生存曲线）
- 🖥️ 跨平台桌面应用（基于pywebview）
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
- Openpyxl - Excel文件操作

### 前端
- Vue 3 - 渐进式JavaScript框架
- Vue Router - 路由管理
- Vuex - 状态管理
- Axios - HTTP客户端
- Chart.js - 图表可视化
- D3.js - 数据可视化
- Material Design Icons - 图标库

### 桌面应用
- PyWebView - 轻量级Web UI库
- PyInstaller - 应用打包工具

## 安装与运行

### 前提条件
- Python 3.8+
- Node.js 14+
- npm或yarn

### 后端设置

1. 克隆项目并安装Python依赖：
```bash
pip install flask flask_sqlalchemy flask_cors pandas openpyxl pywebview pyinstaller
```

2. 运行Flask服务器：
```bash
python app.py
```

### 前端设置

1. 进入前端目录并安装依赖：
```bash
cd frontend
npm install
```

2. 运行开发服务器：
```bash
npm run serve
```

3. 构建生产版本：
```bash
npm run build
```

### 桌面应用

1. 运行主程序启动桌面应用：
```bash
python main.py
```

2. 打包为可执行文件：
```bash
pyinstaller --onefile --windowed main.py
```

## 项目结构

```
animal-lab-management/
├── backend/           # Flask后端应用
│   ├── main.py       # 桌面应用入口
│   ├── app.py        # 主应用文件
│   ├── models.py     # 数据模型
│   └── requirements.txt
├── frontend/         # Vue前端应用
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── router/
│   │   └── store/
│   ├── app.vue
│   ├── package.json
│   └── vue.config.js
└── README.md
```

## 主要功能

- **笼位视图** - 可视化动物笼位安排和管理
- **小鼠详细页** - 动物个体信息追踪
- **小鼠列表** - 详细的动物信息管理和搜索
- **体重曲线** - 动物体重变化追踪和分析
- **生存曲线** - 生存率统计和可视化
- **系统设置** - 应用程序配置和管理

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
  - - **Vue.js框架** - 构建现代化的响应式用户界面
  - **PyWebView团队** - 实现轻量级桌面应用封装
  - **Material Design Icons** - 提供美观的图标资源
  - **Chart.js & D3.js** - 强大的数据可视化能力
  - **SQLAlchemy** - ORM数据库管理解决方案
- 感谢所有贡献者和用户

## 支持

如果您遇到问题或有疑问，请通过以下方式联系我们：
- 提交GitHub Issue
- 发送邮件至项目维护团队

## 版本历史

- 0.1.0 - 初始版本发布
- 详细更新日志请查看CHANGELOG.md

---

**注意**: 本项目仍在积极开发中，API和功能可能会有变动。
