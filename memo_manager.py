import getpass
import os
import platform
from datetime import datetime

import pandas as pd

from config import Config
from utils.slack_sender import SlackSender

class MemoManager:
    def __init__(self, data_manager):
        self.dm = data_manager

    def get_memos(self, req_no):
        if self.dm.memo_df.empty: return []
        mask = self.dm.memo_df["번호"].astype(str) == str(req_no)
        target_memos = self.dm.memo_df[mask].copy()
        if target_memos.empty: return []
        target_memos = target_memos.sort_values(by="일시", ascending=True)
        return target_memos.to_dict('records')

    def get_unchecked_memo_count(self, req_no):
        if self.dm.memo_df.empty: return 0
        mask = (self.dm.memo_df["번호"].astype(str) == str(req_no)) & (self.dm.memo_df["확인"] == "N")
        return len(self.dm.memo_df[mask])

    def add_memo(self, req_no, content):
        def logic(dfs):
            try: user = getpass.getuser()
            except: user = "Unknown"
            try: pc_info = platform.node()
            except: pc_info = "Unknown"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            new_memo = {"번호": str(req_no), "일시": timestamp, "작업자": user, "PC정보": pc_info, "내용": content, "확인": "N"}
            dfs["memo"] = pd.concat([dfs["memo"], pd.DataFrame([new_memo])], ignore_index=True)
            
            new_log = {"일시": timestamp, "작업자": user, "구분": "추가", "요청번호": str(req_no), "내용": content}
            dfs["memo_log"] = pd.concat([dfs["memo_log"], pd.DataFrame([new_log])], ignore_index=True)
            
            # [신규] 슬랙 알림 전송
            try:
                # 업체명 조회
                company_name = "Unknown"
                mask = dfs["df"]["번호"].astype(str) == str(req_no)
                if mask.any():
                    company_name = dfs["df"].loc[mask, "업체명"].iloc[0]
                
                slack_msg = f"[주문번호: {req_no}] {company_name}\n{content}"
                SlackSender.send_message(slack_msg)
            except Exception as e:
                print(f"Slack notification failed: {e}")

            return True, ""
        return self.dm._execute_transaction(logic)

    def update_memo_check(self, req_no, timestamp, content, new_status):
        def logic(dfs):
            mask = ((dfs["memo"]["번호"].astype(str) == str(req_no)) & (dfs["memo"]["일시"] == timestamp) & (dfs["memo"]["내용"] == content))
            if mask.any():
                dfs["memo"].loc[mask, "확인"] = new_status
                return True, ""
            return False, "메모를 찾을 수 없습니다."
        return self.dm._execute_transaction(logic)

    def delete_memo(self, req_no, timestamp, content):
        def logic(dfs):
            mask = ((dfs["memo"]["번호"].astype(str) == str(req_no)) & (dfs["memo"]["일시"] == timestamp) & (dfs["memo"]["내용"] == content))
            if mask.any():
                if "[파일첨부]" in content and "(경로:" in content:
                    try:
                        for line in content.split('\n'):
                            line = line.strip()
                            if line.startswith("(경로:") and line.endswith(")"):
                                file_path = line[5:-1].strip()
                                if file_path and os.path.exists(file_path): os.remove(file_path)
                                break
                    except: pass
                
                dfs["memo"] = dfs["memo"][~mask]
                new_log = {"일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "작업자": getpass.getuser(), "구분": "삭제", "요청번호": str(req_no), "내용": content}
                dfs["memo_log"] = pd.concat([dfs["memo_log"], pd.DataFrame([new_log])], ignore_index=True)
                return True, ""
            return False, "삭제할 메모를 찾을 수 없습니다."
        return self.dm._execute_transaction(logic)
