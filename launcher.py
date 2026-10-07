import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

# ========================================================
# [설정] 공유 폴더 경로 및 앱 설정
# ========================================================
# 업데이트 파일이 위치할 서버 경로 (이 안에 version.txt와 main 폴더가 있어야 함)
SERVER_PATH = r"\\cox_biz\생산-영업\ProductionManager_Update"

# [핵심 수정] 실행 파일(exe)의 진짜 위치를 찾는 코드
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 실행 파일(.exe) 상태일 때
    LOCAL_PATH = os.path.dirname(sys.executable)
else:
    # 파이썬 스크립트(.py)로 실행할 때
    LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))

# 메인 실행 파일 경로 (런처 하위 main 폴더 안에 있음)
MAIN_APP_EXE = os.path.join(LOCAL_PATH, "main", "main.exe")

# 버전 파일 이름
VERSION_FILE = "version.txt"

class UpdaterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Production Manager Updater")
        self.geometry("400x150")
        self.resizable(False, False)
        
        # 화면 중앙 배치
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 150) // 2
        self.geometry(f"400x150+{x}+{y}")

        self.lbl_status = tk.Label(self, text="업데이트 확인 중...", font=("Malgun Gothic", 12))
        self.lbl_status.pack(pady=30)
        
        self.progress = tk.Label(self, text="", font=("Malgun Gothic", 10), fg="gray")
        self.progress.pack(pady=5)

        # 작업을 별도 스레드에서 실행
        threading.Thread(target=self.check_and_update, daemon=True).start()

    def check_and_update(self):
        try:
            # 1. 서버 접근 확인
            if not os.path.exists(SERVER_PATH):
                self.launch_app("서버 경로에 접근할 수 없습니다. (오프라인 모드)")
                return

            server_ver_path = os.path.join(SERVER_PATH, VERSION_FILE)
            local_ver_path = os.path.join(LOCAL_PATH, "main", VERSION_FILE)

            # 2. 버전 비교
            server_ver = self.read_version(server_ver_path)
            local_ver = self.read_version(local_ver_path)

            if server_ver and local_ver and server_ver > local_ver:
                self.update_ui("새로운 버전을 발견했습니다. 업데이트 중...", "잠시만 기다려주세요.")
                success = self.do_update()
                if success:
                    self.launch_app(f"업데이트 완료! (v{server_ver})")
                else:
                    self.launch_app("업데이트 실패. 구버전으로 실행합니다.")
            else:
                self.launch_app(None) # 최신 버전임

        except Exception as e:
            self.launch_app(f"오류 발생: {e}")

    def read_version(self, path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except:
                return "0.0.0"
        return "0.0.0"

    def update_ui(self, status, sub_status=""):
        self.lbl_status.config(text=status)
        self.progress.config(text=sub_status)
        self.update()

    def do_update(self):
        """서버의 'main' 폴더 내용을 로컬 'main' 폴더로 복사"""
        try:
            src_dir = os.path.join(SERVER_PATH, "main")
            dst_dir = os.path.join(LOCAL_PATH, "main")

            if not os.path.exists(src_dir):
                return False
            
            for root, dirs, files in os.walk(src_dir):
                # 상대 경로 계산
                rel_path = os.path.relpath(root, src_dir)
                target_root = os.path.join(dst_dir, rel_path)
                
                if not os.path.exists(target_root):
                    os.makedirs(target_root)
                
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_root, file)
                    
                    try:
                        shutil.copy2(src_file, dst_file)
                    except PermissionError:
                        pass
            
            # [핵심 수정] .env 파일 명시적 복사 (숨김 파일 등 문제 방지)
            src_env = os.path.join(src_dir, ".env")
            dst_env = os.path.join(dst_dir, ".env")
            if os.path.exists(src_env):
                try:
                    shutil.copy2(src_env, dst_env)
                except Exception as e:
                    print(f".env copy failed: {e}")

            return True
        except Exception as e:
            print(f"Update Error: {e}")
            return False

    def launch_app(self, msg):
        if msg:
            time.sleep(1)

        # [수정] 파일 존재 여부 및 경로 확인 디버깅 강화
        if not os.path.exists(MAIN_APP_EXE):
            messagebox.showerror(
                "치명적 오류", 
                f"실행 파일(main.exe)을 찾을 수 없습니다.\n\n"
                f"현재 런처 위치: {LOCAL_PATH}\n"
                f"찾는 파일 경로: {MAIN_APP_EXE}"
            )
            self.quit()
            return

        try:
            subprocess.Popen([MAIN_APP_EXE])
        except Exception as e:
            messagebox.showerror(
                "실행 오류", 
                f"프로그램을 실행하는 도중 오류가 발생했습니다.\n\n"
                f"대상 경로: {MAIN_APP_EXE}\n"
                f"에러 메시지: {e}"
            )
        
        self.quit()

if __name__ == "__main__":
    app = UpdaterApp()
    app.mainloop()