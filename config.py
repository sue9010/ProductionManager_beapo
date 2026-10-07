import os
import sys


# ==========================================
# [Config] 상수 및 기본 설정값 관리
# ==========================================
class Config:
    # ---------------------------------------------------------
    # [앱 설정 파일 경로] 
    # ---------------------------------------------------------
    USER_HOME = os.path.expanduser("~")
    APP_DIR_NAME = ".ProductionManager"
    APP_DIR = os.path.join(USER_HOME, APP_DIR_NAME)
    
    if not os.path.exists(APP_DIR):
        try:
            os.makedirs(APP_DIR)
        except OSError as e:
            print(f"설정 폴더 생성 실패: {e}")

    # [수정된 경로 설정 로직]
    if getattr(sys, 'frozen', False):
        # 1. 실행 경로 (EXEC_DIR): main.exe가 있는 폴더
        # config.json, DB 파일 등 사용자가 접근하거나 수정해야 하는 파일용
        EXEC_DIR = os.path.dirname(sys.executable)
        
        # 2. 리소스 경로 (BASE_DIR): _internal 폴더 (또는 임시 폴더)
        # style.qss, 아이콘 등 내장 리소스용 (PyInstaller가 푼 곳)
        if hasattr(sys, '_MEIPASS'):
            BASE_DIR = sys._MEIPASS
        else:
            # _internal 폴더가 있으면 그곳을, 없으면 실행 경로를 사용
            internal_path = os.path.join(EXEC_DIR, "_internal")
            if os.path.exists(internal_path):
                BASE_DIR = internal_path
            else:
                BASE_DIR = EXEC_DIR
    else:
        # 개발 모드 (python main.py 실행 시)
        EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = EXEC_DIR

    # [중요] config.json은 실행 파일 옆(EXEC_DIR)에 위치시킴
    CONFIG_FILENAME = os.path.join(EXEC_DIR, "config.json")

    # 사용자 설정이 아직 없는 최초 실행 시 사용할 기본 데이터 경로
    DEFAULT_EXCEL_PATH = os.path.join(EXEC_DIR, "생산요청.xlsx")
    DEFAULT_ATTACHMENT_DIR = os.path.join(EXEC_DIR, "attachments")

    # [DB 설정]
    DB_PATH = os.path.join(EXEC_DIR, "scripts", "data.db")

    # [색상 팔레트]
    COLORS = {
        "primary": "#2196F3",
        "secondary": "#E0E0E0",
        "success": "#2CC985",
        "warning": "#FF9800",
        "danger": "#EF5350",
        "info": "#90CAF9",
        "text_primary": "#FFFFFF",
        "text_secondary": "#E0E0E0",
        "bg_main": "#202020"
    }
    
    APP_VERSION = "1.4.9"
    
    DEV_PASSWORD = "admin" 

    SHEET_DATA = "Data"
    SHEET_LOG = "Log"
    SHEET_MEMO = "Memos"
    SHEET_MEMO_LOG = "Memo Log"
    SHEET_SERIAL = "Serial_Data" 

    # 엑셀 헤더 정의 (Data 시트)
    # DB Field -> GUI Header Mapping (Source: scripts/data_migration.py)
    COLUMN_MAP = {
        "request_no": "번호",
        "client": "업체명",
        "model": "모델명",
        "details": "상세",
        "quantity": "수량",
        "other_requests": "기타요청사항",
        "special_notes": "업체별 특이사항",
        "request_date": "출고요청일",
        "expected_date": "출고예정일",
        "out_date": "출고일",
        "serial_no": "시리얼번호",
        "lens_supplier": "렌즈업체",
        "memo": "생산팀 메모",
        "status": "Status",
        "file_path": "파일경로",
        "hold_reason": "대기사유"
    }

    COLUMNS = list(COLUMN_MAP.values())

    # Column Widths
    COLUMN_WIDTHS = {
        "번호": 120,
        "업체명": 200,
        "모델명": 150,
        "상세": 100,
        "수량": 60,
        "기타요청사항": 100,
        "업체별 특이사항": 100,
        "출고요청일": 100,
        "출고예정일": 100,
        "출고일": 100,
        "시리얼번호": 100,
        "렌즈업체": 100,
        "생산팀 메모": 100,
        "Status": 100,
        "파일경로": 100,
        "대기사유": 100
    }
    
    # 시리얼 데이터 시트 헤더
    SERIAL_COLUMNS = ["요청번호", "순번", "모델명", "시리얼번호", "렌즈업체", "비고", "품목순번"]

    # 로그 관련
    LOG_COLUMNS = ["일시", "작업자", "구분", "상세내용"]
    MEMO_COLUMNS = ["번호", "일시", "작업자", "PC정보", "내용", "확인"]
    MEMO_LOG_COLUMNS = ["일시", "작업자", "구분", "요청번호", "내용"]

    # 화면 표시 설정
    DISPLAY_COLUMNS = [
        "번호", "업체명", "모델명", "상세", "수량", 
        "출고요청일", "출고예정일", "Status"
    ]
    
    SEARCH_TARGET_COLS = ["번호", "업체명", "모델명", "상세", "시리얼번호"]
    
    # Team Mapping for Colors
    PERSON_TEAMS = {
        "조덕상": "management", "안보배": "management",
        "이남승": "sales", "김홍모": "sales", "하수민": "sales",
        "김은석": "dev", "최성일": "dev", "고상욱": "dev", "이현석": "dev", "송봉택": "dev",
        "백진우": "production", "박남준": "production"
    }
    # ==========================================================
    # [Chip Colors] 상태/카테고리/팀별 칩 배경색
    # ==========================================================
    CHIP_COLORS = {
        "chart_production": "#2eaadc",
        "chart_waiting": "#f1c40f",
        "chart_hold": "#e74c3c",
        "chart_completed": "#2ecc71",
        "status_준비": "#F5F5F5",
        "status_진행": "#BBDEFB",
        "status_대기": "#FFE0B2",
        "status_중지": "#EF9A9A",
        "status_취소": "#E0E0E0",
        "status_완료": "#C8E6C9",
        "status_생산중": "#90CAF9",
        "status_생산 접수": "#EEEEEE",
        "category_과제": "#E1BEE7",
        "category_영업": "#A5D6A7",
        "category_개발": "#90CAF9",
        "category_이슈": "#C62828",
        "team_management": "#E1BEE7",
        "team_sales": "#A5D6A7",
        "team_dev": "#90CAF9",
        "team_production": "#FFE082",
        "team_default": "#BDBDBD",
        "TEXT_CHIP": "#2d2d2d",
        "CHIP_FALLBACK": "#555555",
    }
