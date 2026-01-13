"""
GUI 다이얼로그 모듈
tkinter 기반 진행률 표시, 메시지 박스, 결과 표시
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from typing import Callable, Optional


class ProgressDialog:
    """진행률 표시 다이얼로그"""

    def __init__(self, title: str = "P4V AI Assistant", message: str = "처리 중..."):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x150")
        self.root.resizable(False, False)

        # 화면 중앙에 배치
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 400) // 2
        y = (self.root.winfo_screenheight() - 150) // 2
        self.root.geometry(f"400x150+{x}+{y}")

        # 항상 위에 표시
        self.root.attributes("-topmost", True)

        # 닫기 버튼 비활성화
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        # UI 구성
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        self.label = ttk.Label(frame, text=message, font=("", 10))
        self.label.pack(pady=(0, 15))

        self.progress = ttk.Progressbar(frame, mode="indeterminate", length=350)
        self.progress.pack(pady=(0, 10))
        self.progress.start(10)

        self.status_label = ttk.Label(frame, text="", font=("", 9), foreground="gray")
        self.status_label.pack()

        self._closed = False

    def update_status(self, message: str) -> None:
        """상태 메시지 업데이트"""
        if not self._closed:
            self.root.after(0, lambda: self.status_label.config(text=message))

    def close(self) -> None:
        """다이얼로그 닫기"""
        if not self._closed:
            self._closed = True
            self.root.after(0, self.root.destroy)

    def run(self) -> None:
        """다이얼로그 실행 (메인 루프)"""
        self.root.mainloop()


class ResultDialog:
    """결과 표시 다이얼로그"""

    def __init__(
        self,
        title: str = "결과",
        success: bool = True,
        message: str = "",
        detail: str = ""
    ):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("500x400")
        self.root.resizable(True, True)

        # 화면 중앙에 배치
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 400) // 2
        self.root.geometry(f"500x400+{x}+{y}")

        self.root.attributes("-topmost", True)

        # UI 구성
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # 상태 아이콘/텍스트
        status_text = "성공" if success else "실패"
        status_color = "green" if success else "red"
        status_label = ttk.Label(
            frame,
            text=f"[{status_text}] {message}",
            font=("", 11, "bold"),
            foreground=status_color
        )
        status_label.pack(anchor=tk.W, pady=(0, 10))

        # 상세 내용
        if detail:
            detail_label = ttk.Label(frame, text="상세 내용:", font=("", 9))
            detail_label.pack(anchor=tk.W)

            text_area = scrolledtext.ScrolledText(
                frame,
                wrap=tk.WORD,
                width=60,
                height=15,
                font=("Consolas", 9)
            )
            text_area.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
            text_area.insert(tk.END, detail)
            text_area.config(state=tk.DISABLED)

        # 닫기 버튼
        close_btn = ttk.Button(frame, text="닫기", command=self.root.destroy, width=15)
        close_btn.pack(pady=(5, 0))

        # Enter 키로 닫기
        self.root.bind("<Return>", lambda e: self.root.destroy())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def run(self) -> None:
        """다이얼로그 실행"""
        self.root.mainloop()


class DescriptionDialog:
    """Description 생성 통합 다이얼로그 (진행 + 결과)"""

    def __init__(
        self,
        title: str = "AI Description 생성",
        changelist: int = 0,
        on_apply_callback: Optional[Callable[[int, str], None]] = None
    ):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("500x400")
        self.root.resizable(True, True)

        # 화면 중앙에 배치
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 400) // 2
        self.root.geometry(f"500x400+{x}+{y}")

        self.root.attributes("-topmost", True)

        self.changelist = changelist
        self.on_apply_callback = on_apply_callback
        self.description = ""
        self.applied = False
        self._closed = False

        # 메인 프레임
        self.main_frame = ttk.Frame(self.root, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 초기에는 진행 상태 UI
        self._build_progress_ui()

        # 닫기 버튼 비활성화 (진행 중에는)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

    def _build_progress_ui(self) -> None:
        """진행 상태 UI 구성"""
        # 진행 프레임
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.BOTH, expand=True)

        # 메시지
        self.progress_label = ttk.Label(
            self.progress_frame,
            text=f"Changelist #{self.changelist} 분석 중...",
            font=("", 11)
        )
        self.progress_label.pack(pady=(50, 20))

        # 진행률 바
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="indeterminate",
            length=350
        )
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.start(10)

        # 상태 메시지
        self.status_label = ttk.Label(
            self.progress_frame,
            text="",
            font=("", 9),
            foreground="gray"
        )
        self.status_label.pack()

    def _build_result_ui(self, success: bool, error: str = "") -> None:
        """결과 상태 UI 구성"""
        # 진행 UI 제거
        self.progress_frame.destroy()

        # 닫기 버튼 활성화
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 결과 프레임
        result_frame = ttk.Frame(self.main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)

        # 상태 메시지
        if success:
            status_label = ttk.Label(
                result_frame,
                text="Description이 생성되었습니다.",
                font=("", 11, "bold"),
                foreground="green"
            )
        else:
            status_label = ttk.Label(
                result_frame,
                text="Description 생성에 실패했습니다.",
                font=("", 11, "bold"),
                foreground="red"
            )
        status_label.pack(anchor=tk.W, pady=(0, 10))

        # 상세 내용
        detail_label = ttk.Label(result_frame, text="생성된 Description:", font=("", 9))
        detail_label.pack(anchor=tk.W)

        self.text_area = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            width=60,
            height=12,
            font=("Consolas", 9)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        if success:
            self.text_area.insert(tk.END, self.description)
        else:
            self.text_area.insert(tk.END, f"오류: {error}")
        self.text_area.config(state=tk.DISABLED)

        # 버튼 프레임
        btn_frame = ttk.Frame(result_frame)
        btn_frame.pack(pady=(5, 0))

        if success:
            # 복사하기 버튼
            self.copy_btn = ttk.Button(
                btn_frame,
                text="복사하기",
                command=self._on_copy,
                width=12
            )
            self.copy_btn.pack(side=tk.LEFT, padx=5)

            # 적용하기 버튼
            self.apply_btn = ttk.Button(
                btn_frame,
                text="적용하기",
                command=self._on_apply,
                width=12
            )
            self.apply_btn.pack(side=tk.LEFT, padx=5)

        # 닫기 버튼
        close_btn = ttk.Button(
            btn_frame,
            text="닫기",
            command=self._on_close,
            width=12
        )
        close_btn.pack(side=tk.LEFT, padx=5)

        # 키보드 바인딩
        self.root.bind("<Escape>", lambda e: self._on_close())

    def update_status(self, message: str) -> None:
        """상태 메시지 업데이트"""
        if not self._closed:
            self.root.after(0, lambda: self.status_label.config(text=message))

    def show_result(
        self,
        success: bool,
        description: str = "",
        summary: str = "",
        error: str = ""
    ) -> None:
        """결과 표시로 전환"""
        self.description = description
        self.summary = summary
        self.root.after(0, lambda: self._build_result_ui(success, error))

    def _on_copy(self) -> None:
        """클립보드에 복사"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.description)
        self.copy_btn.config(text="복사됨!")
        self.root.after(1500, lambda: self.copy_btn.config(text="복사하기"))

    def _on_apply(self) -> None:
        """P4에 Description 적용"""
        if self.on_apply_callback and not self.applied:
            try:
                self.on_apply_callback(self.changelist, self.description)
                self.applied = True
                self.apply_btn.config(text="적용됨!", state=tk.DISABLED)
            except Exception as e:
                self.apply_btn.config(text="적용 실패")

    def _on_close(self) -> None:
        """다이얼로그 닫기"""
        self._closed = True
        self.root.destroy()

    def run(self) -> None:
        """다이얼로그 실행"""
        self.root.mainloop()


class SettingsDialog:
    """설정 다이얼로그"""

    def __init__(self, config_manager):
        self.config = config_manager
        self.root = tk.Tk()
        self.root.title("P4V AI Assistant 설정")
        self.root.geometry("450x200")
        self.root.resizable(False, False)

        # 화면 중앙에 배치
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 450) // 2
        y = (self.root.winfo_screenheight() - 200) // 2
        self.root.geometry(f"450x200+{x}+{y}")

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Webhook URL
        ttk.Label(frame, text="Webhook URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(frame, width=50)
        self.url_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        self.url_entry.insert(0, self.config.webhook_url)

        # Timeout
        ttk.Label(frame, text="Timeout (초):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.timeout_entry = ttk.Entry(frame, width=10)
        self.timeout_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.timeout_entry.insert(0, str(self.config.timeout))

        # 버튼
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="저장", command=self._save, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="취소", command=self.root.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        self.config.webhook_url = self.url_entry.get().strip()
        try:
            self.config.timeout = int(self.timeout_entry.get().strip())
        except ValueError:
            self.config.timeout = 60

        self.config.save()
        messagebox.showinfo("설정", "설정이 저장되었습니다.")
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def show_error(title: str, message: str) -> None:
    """에러 메시지 박스"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showerror(title, message)
    root.destroy()


def show_info(title: str, message: str) -> None:
    """정보 메시지 박스"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo(title, message)
    root.destroy()


def show_warning(title: str, message: str) -> None:
    """경고 메시지 박스"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showwarning(title, message)
    root.destroy()


def ask_yes_no(title: str, message: str) -> bool:
    """예/아니오 확인 대화상자"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    result = messagebox.askyesno(title, message)
    root.destroy()
    return result


def run_with_progress(
    task_func: Callable,
    title: str = "P4V AI Assistant",
    message: str = "처리 중..."
) -> any:
    """
    진행률 표시와 함께 작업 실행

    Args:
        task_func: 실행할 함수 (progress_callback을 인자로 받음)
        title: 다이얼로그 제목
        message: 표시할 메시지

    Returns:
        task_func의 반환값
    """
    result = [None]
    error = [None]

    dialog = ProgressDialog(title=title, message=message)

    def run_task():
        try:
            result[0] = task_func(dialog.update_status)
        except Exception as e:
            error[0] = e
        finally:
            dialog.close()

    thread = threading.Thread(target=run_task, daemon=True)
    thread.start()

    dialog.run()
    thread.join()

    if error[0]:
        raise error[0]

    return result[0]
