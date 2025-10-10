# 动物房管理系统

一个基于 Flask 和 Vue.js 开发的本地实验动物管理系统，专为生物医学研究设计，提供完整的动物管理、数据分析和可视化功能，造福广大有实验动物需求的朋友。可以直接在 windows 上使用，而在 mac 上也可以根据开发教程安装。

介绍和[教学视频](https://b23.tv/5fQetkk)

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

👉 [立即下载最新版本](https://github.com/lanternx/animal_lab/releases/tag/V2.1)

也可通过[百度网盘](https://pan.baidu.com/s/1UyzEXAiVZlK72dOMXtXZFA?pwd=2333)下载


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

5. 构建生产版本：

```cmd
npm run build
```

6. 将编译后的 `dist` 文件夹移动到 `backend` 中：

7. 运行后端：

```bash
cd backend
python main.py
```

### 安装完成后的运行：

```cmd
cd backend
venv\Scripts\activate.bat
python main.py
```

8. 打包为可执行文件：

```cmd
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

6. 构建生产版本：

```bash
npm run build
```

7. 将编译后的 `dist` 文件夹移动到 `backend` 中：

```bash
mv -i dist ../backend/
```

8. 运行后端：

```bash
cd backend
python3 main.py
```

我一般在 `localhost:5000` 上直接访问，不会使用桌面程序。也可以编译为可执行文件：

打包为可执行文件(打包不要使用mac自带的python)：

```bash
python3 build_mac.py --create-dmg --app-name "AL_V2.2"
```

### 安装完成后的运行：

```bash
source ~/.python/sglang/bin/activate
cd backend
python3 main.py
```

## 项目结构

```
animal-lab-management/
├── backend/           # Flask后端应用
│   ├── dist/         # Vue前端编译产物
│   ├── main.py       # 桌面应用入口
│   ├── app.py        # 主应用文件
│   ├── models.py     # 数据模型
│   ├── pyinstaller.spec
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
