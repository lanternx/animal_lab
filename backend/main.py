from app import app
import webview
import threading
import time
import sys
import os
import socket
from contextlib import closing
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Main")

# 获取屏幕尺寸（使用 tkinter，Python 标准库）
import tkinter as tk
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()

# 计算居中位置
loading_window_width, loading_window_height = 400, 300
loading_window_x = (screen_width - loading_window_width) // 2
loading_window_y = (screen_height - loading_window_height) // 2

# 创建一个简单的加载动画HTML
LOADING_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f5f5f5;
            font-family: Arial, sans-serif;
        }
        .loading-container {
            text-align: center;
        }
        .spinner {
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading-text {
            color: #333;
            font-size: 18px;
        }
        .progress-bar {
            width: 300px;
            height: 10px;
            background-color: #e0e0e0;
            border-radius: 5px;
            margin: 20px auto;
            overflow: hidden;
        }
        .progress {
            height: 100%;
            width: 0%;
            background-color: #3498db;
            border-radius: 5px;
            animation: progress-animation 3s ease-in-out;
        }
        @keyframes progress-animation {
            0% { width: 0%; }
            100% { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="loading-container">
        <div class="spinner"></div>
        <div class="loading-text">小鼠管理系统启动中...</div>
        <div class="progress-bar">
            <div class="progress"></div>
        </div>
    </div>
</body>
</html>
"""

def find_free_port(start_port=5000, max_attempts=20):
    """查找可用端口"""
    port = start_port
    attempts = 0
    while attempts < max_attempts:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex(('localhost', port)) != 0:
                logger.info(f"找到可用端口: {port}")
                return port
        port += 1
        attempts += 1
    logger.error(f"在 {start_port}-{port} 范围内找不到可用端口")
    return None

def run_flask(port):
    """运行Flask应用"""
    try:
        logger.info(f"启动Flask服务器，端口: {port}")
        # 关闭调试模式，提高生产环境稳定性
        app.run(host='localhost', port=port, use_reloader=False)
    except Exception as e:
        logger.exception(f"Flask服务器启动失败: {str(e)}")

def wait_for_server(port, timeout=30):
    """等待服务器启动"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                logger.info(f"服务器在端口 {port} 上已启动")
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
    logger.error(f"服务器在端口 {port} 上启动超时")
    return False

def create_save_file_dialog(window):
    """创建文件保存对话框函数"""
    def save_file_dialog(data, filename):
        """显示保存文件对话框并保存文件"""
        try:
            # 确保数据是字节类型
            if not isinstance(data, bytes):
                try:
                    byte_data = bytes(data)
                except Exception as e:
                    logger.error(f"数据转换失败: {str(e)}")
                    return {"success": False, "message": "数据格式错误"}
            else:
                byte_data = data
            
            # 创建默认保存路径
            default_dir = os.path.join(os.path.expanduser("~"), "Documents")
            if not os.path.exists(default_dir):
                default_dir = os.getcwd()
            
            try:
                # 使用窗口实例创建文件对话框
                save_paths = window.create_file_dialog(
                    webview.FileDialog.SAVE,
                    directory=default_dir,
                    save_filename=filename,
                    file_types=("All files (*.*)",)
                )
                
                if save_paths and len(save_paths) > 0:
                    save_path = save_paths[0]
                    logger.info(f"用户选择保存路径: {save_path}")
                    
                    # 确保目录存在
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    # 写入文件
                    with open(save_path, 'wb') as f:
                        f.write(byte_data)
                    
                    return {"success": True, "path": save_path}
                
                return {"success": False, "message": "用户取消操作"}
            except Exception as e:
                logger.exception(f"文件对话框错误: {str(e)}")
                return {"success": False, "message": f"文件对话框错误: {str(e)}"}
        except Exception as e:
            logger.exception(f"保存文件失败: {str(e)}")
            return {"success": False, "message": f"保存失败: {str(e)}"}
    
    return save_file_dialog

def handle_exception(exctype, value, traceback):
    """全局异常处理"""
    logger.critical(f"未捕获的异常: {exctype.__name__}: {value}")
    logger.exception("异常堆栈:")
    # 可以在这里添加用户友好的错误提示
    sys.__excepthook__(exctype, value, traceback)

# 设置全局异常处理
sys.excepthook = handle_exception

if __name__ == '__main__':
    logger.info("应用程序启动")
    
    # 创建加载窗口
    loading_window = webview.create_window(
        "小鼠管理系统 - 启动中", 
        html=LOADING_HTML,
        width=loading_window_width, 
        height=loading_window_height,
        resizable=False,
        frameless=True,
        easy_drag=False,
        x=loading_window_x,
        y=loading_window_y
    )
    
    # 设置定时器，5秒后自动关闭加载窗口（无论初始化是否完成）
    def close_loading_window():
        try:
            loading_window.destroy()
        except:
            pass
    
    # 启动定时器
    close_timer = threading.Timer(5.0, close_loading_window)
    close_timer.start()
    
    # 在后台线程中执行初始化工作
    def initialize_app():
        # 查找可用端口
        port = find_free_port()
        if port is None:
            logger.error("无法找到可用端口，退出应用")
            # 在界面上显示错误信息
            def show_error():
                loading_window.evaluate_js('document.body.innerHTML = "<div style=\\"text-align: center; padding: 20px;\\"><h3>启动失败</h3><p>找不到可用端口</p></div>";')
                time.sleep(3)
                loading_window.destroy()
            webview.schedule_update(show_error)
            return

        # 启动Flask服务器线程
        flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
        flask_thread.start()

        # 等待服务器启动
        if not wait_for_server(port):
            logger.error("服务器启动失败，退出应用")
            # 在界面上显示错误信息
            def show_error():
                loading_window.evaluate_js('document.body.innerHTML = "<div style=\\"text-align: center; padding: 20px;\\"><h3>启动失败</h3><p>服务器启动超时</p></div>";')
                time.sleep(3)
                loading_window.destroy()
            webview.schedule_update(show_error)
            return
        
        # 创建主窗口
        main_window = webview.create_window(
            "小鼠管理系统", 
            f"http://localhost:{port}",
            width=1200, 
            height=800,
            resizable=True,
            text_select=True,
            confirm_close=True,
            frameless=False
        )
        
        # 创建保存函数并暴露API
        save_file_dialog = create_save_file_dialog(main_window)
        main_window.expose(save_file_dialog)
        
        # 取消定时器（如果初始化成功）
        close_timer.cancel()
        
        # 关闭加载窗口
        loading_window.destroy()
    
    # 在单独的线程中执行初始化
    init_thread = threading.Thread(target=initialize_app)
    init_thread.start()
    
    try:
        # 启动webview
        logger.info("启动Webview窗口")
        webview.start(
            private_mode=False,  # 禁用私有模式以允许文件访问
            http_server=False,   # 禁用内置HTTP服务器
        )
    except Exception as e:
        logger.exception(f"窗口创建失败: {str(e)}")

    logger.info("应用程序正常退出")