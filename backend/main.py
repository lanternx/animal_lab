import webview
import threading
import time
import requests
from app import app

def run_flask():
    app.run(port=5000, debug=False)

def wait_for_flask():
    """等待Flask应用完全启动"""
    print("等待Flask应用启动...")
    time.sleep(5)  # 给Flask应用更多时间启动
    
    max_attempts = 8  # 增加尝试次数
    for i in range(max_attempts):
        try:
            response = requests.get('http://localhost:5000', timeout=2)
            if response.status_code == 200:
                print("Flask应用已启动，数据库已准备就绪")
                
                # 自动发送一个POST请求来触发API活动
                try:
                    test_location_data = {
                        "identifier": f"启动测试区_{int(time.time())}",
                        "description": f"Flask启动时自动创建的测试位置 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                    post_response = requests.post('http://localhost:5000/api/locations', 
                                                json=test_location_data, 
                                                timeout=2)
                    if post_response.status_code == 201:
                        print("已自动发送POST请求创建测试位置")
                    else:
                        print(f"POST请求响应状态: {post_response.status_code}")
                except Exception as e:
                    print(f"发送POST请求失败: {e}")
                
                return True
        except requests.exceptions.RequestException as e:
            print(f"连接失败 ({i+1}/{max_attempts}): {e}")
        time.sleep(2)
    
    # 如果检测失败，但Flask可能已经启动，尝试强制发送POST请求
    print("检测失败，但尝试强制发送POST请求...")
    try:
        test_location_data = {
            "identifier": f"强制启动测试区_{int(time.time())}",
            "description": f"强制创建的测试位置 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
        post_response = requests.post('http://localhost:5000/api/locations', 
                                    json=test_location_data, 
                                    timeout=3)
        print(f"强制POST请求状态: {post_response.status_code}")
        if post_response.status_code == 201:
            print("强制POST请求成功！")
    except Exception as e:
        print(f"强制POST请求也失败: {e}")
    
    print("继续启动桌面应用...")
    return True

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
    print("正在启动Flask应用...")
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # 等待Flask应用启动
    wait_for_flask()
    
    print("正在创建桌面窗口...")
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
    print("启动桌面应用...")
    webview.start()
