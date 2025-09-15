import webview
import threading
from app import app

def run_flask():
    app.run(port=5000)

# 使用闭包创建保存函数
def create_save_file_dialog(window):
    def save_file_dialog(data, filename):
        """显示保存文件对话框并保存文件"""
        try:
            # 使用窗口实例创建文件对话框
            save_paths = window.create_file_dialog(
                webview.FileDialog.SAVE,
                directory='/',
                save_filename=filename
            )
            if save_paths and len(save_paths) > 0:
                # 取第一个路径
                save_path = save_paths[0]
                byte_data = bytes(data)
                # 写入文件
                with open(save_path, 'wb') as f:
                    f.write(byte_data)
                return True
            return False
        except Exception as e:
            print(f"保存文件失败: {str(e)}")
            return False
    
    return save_file_dialog
    
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
