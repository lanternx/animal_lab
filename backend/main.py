import webview
import threading
from app import app

def run_flask():
    app.run(port=5000)

# 使用闭包创建保存函数
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
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # 创建本地窗口应用
    window = webview.create_window(
        "小鼠管理系统", 
        "http://localhost:5000", 
        width=1200, 
        height=800,
        resizable=True
    )
    # 创建保存函数
    save_file_dialog = create_save_file_dialog(window)

    # 暴露API
    window.expose(save_file_dialog)
    webview.start()
