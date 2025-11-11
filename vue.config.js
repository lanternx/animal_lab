const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // 开发服务器配置
  devServer: {
    port: 8080, // 前端开发服务器端口
    host: 'localhost', // 主机名
    open: true, // 启动后自动打开浏览器
    hot: true, // 启用热模块替换 (HMR)
    
    // 代理配置 - 将 API 请求转发到 Flask 后端
    proxy: {
      '/api': {
        target: 'http://localhost:5000', // Flask 后端地址
        changeOrigin: true, // 允许跨域
        secure: false, // 如果是 https 接口，需要配置为 true
        logLevel: 'debug', // 显示代理日志
        pathRewrite: {
          '^/api': '/api' // 保持 API 路径不变
        }
      }
    },
    
    // 启用 gzip 压缩
    compress: true,
    
    // 客户端日志级别
    client: {
      logging: 'info',
      overlay: {
        errors: true,
        warnings: false
      }
    }
  },
  
  // 生产环境配置
  publicPath: './',
  
  // 构建输出目录
  outputDir: 'dist',
  
  // 是否生成 source map
  productionSourceMap: process.env.NODE_ENV !== 'production',
  
  // CSS 相关配置
  css: {
    // 是否将组件中的 CSS 提取至独立的 CSS 文件
    extract: process.env.NODE_ENV === 'production',
    // 是否为 CSS 开启 source map
    sourceMap: process.env.NODE_ENV !== 'production'
  }
})