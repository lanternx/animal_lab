# 动物房管理系统 (Animal Facility Management System)

一个基于 Vue.js 构建的现代化实验室动物房信息管理系统。该系统专注于小鼠 colony 的管理，提供了从笼位视图、个体信息管理到体重监测、生存分析等一系列核心功能，旨在提升科研数据管理的效率和可靠性。

## ✨ 特性

- **直观的笼位管理**: 提供可视化笼位视图，快速浏览和操作笼舍及小鼠信息。
- **详细的小鼠档案**: 集中管理小鼠的基因型、出生日期、实验编号等详细信息。
- **数据可视化分析**: 集成图表功能，用于绘制小鼠体重变化曲线和生存分析曲线。
- **响应式设计**: 适配桌面、平板及移动设备，侧边栏可折叠以节省空间。
- **实时状态监控**: 显示数据库连接状态和数据最后保存时间。

## 🚀 快速开始

### 环境要求

- Node.js (推荐 LTS 版本)
- npm 或 yarn

### 安装与运行

1. **克隆项目**

    ```bash
    git clone <您的项目仓库地址>
    cd al_flask
    ```

2. **安装依赖**

    ```bash
    npm install
    ```

3. **启动开发服务器**

    ```bash
    npm run serve
    ```

    应用将在 `http://localhost:8080` 启动。

4. **构建生产版本**

    ```bash
    npm run build
    ```

    构建后的静态文件将位于 `dist/` 目录。

## 📁 项目结构

al_flask/
├── public/                 # 静态资源
├── src/
│   ├── views/             # 路由页面组件
│   ├── components/        # 可复用组件
│   ├── router/            # 路由配置
│   ├── store/             # Vuex 状态管理
│   ├── assets/            # 图片、样式等资源
│   └── App.vue            # 根组件
├── package.json           # 项目配置和依赖
└── README.md             # 项目说明

## 🛠️ 技术栈

- **前端框架**: Vue.js 3
- **构建工具**: Vue CLI
- **路由**: Vue Router 4
- **状态管理**: Vuex 4
- **图表库**: Chart.js (通过 vue-chartjs 集成)
- **图标**: Material Icons
- **HTTP 客户端**: Axios

## 📊 第三方依赖与许可

本项目遵循所有第三方开源库的许可协议。主要依赖及其许可如下：

| 依赖名称 | 版本 | 许可 | 用途 |
| :--- | :--- | :--- | :--- |
| **vue** | ^3.5.19 | MIT | 核心框架 |
| **vue-router** | ^4.5.1 | MIT | 路由管理 |
| **vuex** | ^4.1.0 | MIT | 状态管理 |
| **chart.js** | ^4.5.0 | MIT | 数据图表 |
| **axios** | ^1.11.0 | MIT | HTTP 请求 |
| **core-js** | ^3.45.1 | MIT | 浏览器兼容性 |
| **@vue/cli-service** | ^5.0.9 | MIT | 构建与开发服务 |
| **sass** | ^1.90.0 | MIT | CSS 预处理器 |
| **webpack** | ^5.101.3 | MIT | 模块打包 |
| **babel** | ^7.26.0 | MIT | JavaScript 编译器 |
| **eslint** | ^7.32.0 | MIT | 代码检查 |
| **prettier** | ^2.8.8 | MIT | 代码格式化 |
| **workbox** | ^6.6.0 | MIT | PWA 支持 |
| **@vue/compiler-sfc** | ^3.5.19 | MIT | 单文件组件编译 |

**完整的依赖树和详细的许可信息**请参阅项目根目录下的 `LICENSES` 文件或运行 `npm run licenses:review`。

> **重要提示**: 本项目是一个前端应用程序，通常需要与后端 API (如 Flask, Django, Express 等) 协同工作以进行数据持久化。当前版本可能配置为与本地 mock 数据或开发服务器交互。

## 🤝 贡献指南

我们欢迎任何形式的贡献！

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

此项目根据 **Apache License, Version 2.0 许可证** 授权 - 查看 LICENSE 文件了解详情。

## 🙏 致谢

感谢所有为此项目做出贡献的开发者以及以下优秀的开源项目：

- Vue.js 团队
- Chart.js 团队
- Webpack 团队
- 以及所有本项目依赖库的维护者们。

---
