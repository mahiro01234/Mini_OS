from __future__ import annotations

from dataclasses import dataclass
import random
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable
import hashlib
import json
import os


@dataclass(frozen=True)
class ProcessDefinition:
    name: str
    category: str
    base_cpu: int
    description: str


@dataclass
class ProcessInstance:
    pid: int
    definition: ProcessDefinition
    instance_num: int
    status: str = "Running"


class FileExplorer:
    """Проводник - имитация файловой системы"""
    def __init__(self, username: str):
        self.username = username
        self.current_path = "Desktop"
        # Создаем отдельную файловую систему для каждого пользователя
        self.filesystem = {
            "Desktop": {
                "type": "folder",
                "children": {
                    "Документы": {"type": "folder", "children": {}},
                    "Изображения": {"type": "folder", "children": {}},
                    "Заметки.txt": {"type": "file", "size": "0 KB"},
                    "Привет.txt": {"type": "file", "size": "0 KB"}
                }
            }
        }
        self._load_user_files()
    
    def _load_user_files(self):
        """Загружает файлы пользователя из JSON файла"""
        user_dir = f"users_data/{self.username}"
        os.makedirs(user_dir, exist_ok=True)
        files_path = f"{user_dir}/filesystem.json"
        
        if os.path.exists(files_path):
            try:
                with open(files_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    # Восстанавливаем файловую систему
                    if "Desktop" in saved_data:
                        self.filesystem["Desktop"]["children"] = saved_data["Desktop"]["children"]
            except:
                pass
    
    def _save_user_files(self):
        """Сохраняет файлы пользователя в JSON файл"""
        user_dir = f"users_data/{self.username}"
        os.makedirs(user_dir, exist_ok=True)
        files_path = f"{user_dir}/filesystem.json"
        
        try:
            with open(files_path, 'w', encoding='utf-8') as f:
                json.dump(self.filesystem, f, ensure_ascii=False, indent=2)
        except:
            pass
        
    def get_current_items(self):
        """Получить содержимое текущей директории"""
        path_parts = self.current_path.split("/")
        current = self.filesystem
        for part in path_parts:
            if part == "Desktop":
                current = current["Desktop"]
            else:
                current = current["children"][part]
        return current["children"] if current["type"] == "folder" else {}
    
    def create_folder(self, name):
        """Создать папку"""
        path_parts = self.current_path.split("/")
        current = self.filesystem
        for part in path_parts:
            if part == "Desktop":
                current = current["Desktop"]
            else:
                current = current["children"][part]
        
        if name not in current["children"]:
            current["children"][name] = {"type": "folder", "children": {}}
            self._save_user_files()
            return True
        return False
    
    def create_file(self, name):
        """Создать файл"""
        path_parts = self.current_path.split("/")
        current = self.filesystem
        for part in path_parts:
            if part == "Desktop":
                current = current["Desktop"]
            else:
                current = current["children"][part]
        
        if name not in current["children"]:
            current["children"][name] = {"type": "file", "size": "0 KB"}
            self._save_user_files()
            return True
        return False
    
    def delete_item(self, name):
        """Удалить файл или папку"""
        path_parts = self.current_path.split("/")
        current = self.filesystem
        for part in path_parts:
            if part == "Desktop":
                current = current["Desktop"]
            else:
                current = current["children"][part]
        
        if name in current["children"]:
            del current["children"][name]
            self._save_user_files()
            return True
        return False
    
    def navigate_to(self, name):
        """Перейти в папку"""
        items = self.get_current_items()
        if name in items and items[name]["type"] == "folder":
            self.current_path = f"{self.current_path}/{name}"
            return True
        return False
    
    def go_back(self):
        """Вернуться назад"""
        if "/" in self.current_path:
            self.current_path = self.current_path.rsplit("/", 1)[0]
            return True
        return False


class UserManager:
    """Класс для управления пользователями"""
    def __init__(self):
        self.users_file = "users.json"
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Создает файл пользователей если его нет"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    
    def _hash_password(self, password: str) -> str:
        """Хэширует пароль с использованием SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str) -> bool:
        """Регистрирует нового пользователя"""
        if not username or not password:
            return False
        
        with open(self.users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        if username in users:
            return False
        
        users[username] = {
            "password": self._hash_password(password),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        
        # Создаем директорию для файлов пользователя
        os.makedirs(f"users_data/{username}", exist_ok=True)
        
        return True
    
    def login_user(self, username: str, password: str) -> bool:
        """Проверяет логин пользователя"""
        with open(self.users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        if username not in users:
            return False
        
        return users[username]["password"] == self._hash_password(password)


class LoginWindow:
    """Окно входа в систему"""
    def __init__(self, root: tk.Tk, on_success: Callable):
        self.root = root
        self.on_success = on_success
        self.user_manager = UserManager()
        
        # Скрываем главное окно
        self.root.withdraw()
        
        # Создаем окно авторизации
        self.login_window = tk.Toplevel(root)
        self.login_window.title("Вход в Mini-OS")
        self.login_window.geometry("400x500")
        self.login_window.configure(bg="#1a1a2e")
        self.login_window.resizable(False, False)
        
        # Центрируем окно
        x = (self.login_window.winfo_screenwidth() // 2) - 200
        y = (self.login_window.winfo_screenheight() // 2) - 250
        self.login_window.geometry(f"+{x}+{y}")
        
        self.login_window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создает виджеты окна входа"""
        # Заголовок
        title_frame = tk.Frame(self.login_window, bg="#1a1a2e")
        title_frame.pack(fill="x", pady=30)
        
        tk.Label(title_frame, text="🔐 Mini-OS", font=("Segoe UI", 24, "bold"),
                fg="#6c5ce7", bg="#1a1a2e").pack()
        tk.Label(title_frame, text="Вход в систему", font=("Segoe UI", 12),
                fg="#ffffff", bg="#1a1a2e").pack(pady=5)
        
        # Форма входа
        form_frame = tk.Frame(self.login_window, bg="#1a1a2e")
        form_frame.pack(pady=20)
        
        # Вкладки
        self.notebook = ttk.Notebook(form_frame, width=350, height=300)
        self.notebook.pack()
        
        # Вкладка входа
        login_tab = tk.Frame(self.notebook, bg="#2d2d44")
        self.notebook.add(login_tab, text="Вход")
        
        tk.Label(login_tab, text="Имя пользователя", font=("Segoe UI", 10),
                fg="#ffffff", bg="#2d2d44").pack(anchor="w", padx=20, pady=(20, 5))
        self.login_username = tk.Entry(login_tab, font=("Segoe UI", 11), bg="#3d3d5c",
                                       fg="white", insertbackground="white", width=25)
        self.login_username.pack(padx=20, pady=5)
        
        tk.Label(login_tab, text="Пароль", font=("Segoe UI", 10),
                fg="#ffffff", bg="#2d2d44").pack(anchor="w", padx=20, pady=(15, 5))
        self.login_password = tk.Entry(login_tab, font=("Segoe UI", 11), bg="#3d3d5c",
                                       fg="white", insertbackground="white", width=25, show="•")
        self.login_password.pack(padx=20, pady=5)
        
        tk.Button(login_tab, text="Войти", command=self._do_login,
                 font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white",
                 bd=0, padx=30, pady=8).pack(pady=30)
        
        # Вкладка регистрации
        register_tab = tk.Frame(self.notebook, bg="#2d2d44")
        self.notebook.add(register_tab, text="Регистрация")
        
        tk.Label(register_tab, text="Имя пользователя", font=("Segoe UI", 10),
                fg="#ffffff", bg="#2d2d44").pack(anchor="w", padx=20, pady=(20, 5))
        self.register_username = tk.Entry(register_tab, font=("Segoe UI", 11), bg="#3d3d5c",
                                          fg="white", insertbackground="white", width=25)
        self.register_username.pack(padx=20, pady=5)
        
        tk.Label(register_tab, text="Пароль", font=("Segoe UI", 10),
                fg="#ffffff", bg="#2d2d44").pack(anchor="w", padx=20, pady=(15, 5))
        self.register_password = tk.Entry(register_tab, font=("Segoe UI", 11), bg="#3d3d5c",
                                          fg="white", insertbackground="white", width=25, show="•")
        self.register_password.pack(padx=20, pady=5)
        
        tk.Label(register_tab, text="Подтверждение пароля", font=("Segoe UI", 10),
                fg="#ffffff", bg="#2d2d44").pack(anchor="w", padx=20, pady=(15, 5))
        self.register_confirm = tk.Entry(register_tab, font=("Segoe UI", 11), bg="#3d3d5c",
                                         fg="white", insertbackground="white", width=25, show="•")
        self.register_confirm.pack(padx=20, pady=5)
        
        tk.Button(register_tab, text="Зарегистрироваться", command=self._do_register,
                 font=("Segoe UI", 11, "bold"), bg="#2196F3", fg="white",
                 bd=0, padx=30, pady=8).pack(pady=30)
        
        # Навигация между полями по Enter
        self.login_username.bind("<Return>", lambda e: self.login_password.focus())
        self.login_password.bind("<Return>", lambda e: self._do_login())
        self.register_username.bind("<Return>", lambda e: self.register_password.focus())
        self.register_password.bind("<Return>", lambda e: self.register_confirm.focus())
        self.register_confirm.bind("<Return>", lambda e: self._do_register())
    
    def _do_login(self):
        """Выполняет вход пользователя"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите имя пользователя и пароль!")
            return
        
        if self.user_manager.login_user(username, password):
            self.login_window.destroy()
            self.root.deiconify()
            self.on_success(username)
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль!")
            self.login_password.delete(0, tk.END)
    
    def _do_register(self):
        """Регистрирует нового пользователя"""
        username = self.register_username.get().strip()
        password = self.register_password.get()
        confirm = self.register_confirm.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают!")
            return
        
        if len(password) < 4:
            messagebox.showerror("Ошибка", "Пароль должен содержать минимум 4 символа!")
            return
        
        if self.user_manager.register_user(username, password):
            messagebox.showinfo("Успех", f"Пользователь '{username}' успешно создан!\nТеперь вы можете войти.")
            self.notebook.select(0)  # Переключаем на вкладку входа
            self.login_username.delete(0, tk.END)
            self.login_password.delete(0, tk.END)
            self.register_username.delete(0, tk.END)
            self.register_password.delete(0, tk.END)
            self.register_confirm.delete(0, tk.END)
        else:
            messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует!")
    
    def _on_close(self):
        """Закрытие окна входа"""
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти?"):
            self.root.destroy()


class MiniOSApp:
    def __init__(self, root: tk.Tk, username: str) -> None:
        self.root = root
        self.username = username
        self.root.title(f"Мини-ОС - {username}")
        self.root.geometry("1180x720")
        self.root.minsize(1024, 640)
        self.root.configure(bg="#1a1a2e")

        self.current_user = username
        
        self.process_catalog = [
            ProcessDefinition("Диспетчер задач", "Система", 18, "Список и управление процессами"),
            ProcessDefinition("Монитор системы", "Система", 16, "Отображение загрузки CPU"),
            ProcessDefinition("Журнал событий", "Система", 7, "Логи действий пользователя и системы"),
            ProcessDefinition("Калькулятор", "Приложение", 9, "Базовые арифметические операции"),
            ProcessDefinition("Проводник", "Приложение", 5, "Файловый менеджер"),
        ]

        self.background_presets = {
            "Светлая": {"bg": "#e8f0fe", "text": "#1a1a2e", "accent": "#4a90e2", "card": "#ffffff", "pattern": "#c0c8d8"},
            "Темная": {"bg": "#1a1a2e", "text": "#ffffff", "accent": "#6c5ce7", "card": "#2d2d44", "pattern": "#2a2a44"},
            "Синяя": {"bg": "#0f3460", "text": "#ffffff", "accent": "#00b4d8", "card": "#16213e", "pattern": "#1a3a6a"},
            "Зеленая": {"bg": "#1b4332", "text": "#ffffff", "accent": "#74c69d", "card": "#2d6a4f", "pattern": "#2a5a3a"},
        }
        
        self.current_theme = tk.StringVar(value="Темная")
        
        # Системные переменные
        self.running_processes: list[ProcessInstance] = []
        self.pid_counter = 1000
        self.instance_counter: dict[str, int] = {}
        self.cpu_usage = tk.IntVar(value=8)
        self.clock_text = tk.StringVar(value="--:--:--")
        self.summary_text = tk.StringVar(value="Активных процессов: 0")
        self.desktop_selection = tk.StringVar(value="Диспетчер задач")
        
        # Файловая система
        self.file_explorer = FileExplorer(username)
        
        # UI элементы
        self.desktop_area: tk.Frame | None = None
        self.background_canvas: tk.Canvas | None = None
        self.start_menu: tk.Frame | None = None
        self.start_menu_visible = False
        self.desktop_icons: dict[str, dict] = {}
        self.window_states: dict[str, dict[str, object]] = {}
        self.process_to_window: dict[str, str] = {}
        self.taskbar_buttons: dict[str, tk.Button] = {}
        self.window_counter = 0
        self.drag_data = {"key": None, "x": 0, "y": 0}
        self.log_messages: list[str] = []
        self.window_bar: tk.Frame | None = None
        
        # Компоненты приложений
        self.process_tree: ttk.Treeview | None = None
        self.log_text: tk.Text | None = None
        self.cpu_value_label: tk.Label | None = None
        self.cpu_bar: ttk.Progressbar | None = None
        self.process_count_label: tk.Label | None = None
        
        self._configure_style()
        self._build_shell()
        self._draw_background_pattern()
        self._seed_initial_state()
        self._update_clock()
        self._schedule_cpu_update()
        self._log(f"Система запущена. Добро пожаловать, {username}!")

    def _draw_background_pattern(self) -> None:
        if self.background_canvas is None:
            return
        
        self.background_canvas.delete("all")
        theme = self.background_presets[self.current_theme.get()]
        bg_color = theme["bg"]
        pattern_color = theme["pattern"]
        
        self.background_canvas.configure(bg=bg_color)
        
        width = self.background_canvas.winfo_width()
        height = self.background_canvas.winfo_height()
        
        if width > 100 and height > 100:
            for x in range(20, width, 40):
                for y in range(20, height, 40):
                    self.background_canvas.create_oval(x-2, y-2, x+2, y+2, fill=pattern_color, outline="")

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        
        theme = self.background_presets[self.current_theme.get()]
        
        style.configure("Desktop.TFrame", background=theme["bg"])
        style.configure("Window.TFrame", background=theme["card"])
        style.configure("Taskbar.TFrame", background="#0f0f1a")
        style.configure("Taskbar.TLabel", background="#0f0f1a", foreground="#eff6ff", font=("Segoe UI", 10))
        style.configure("TaskbarWindow.TButton", font=("Segoe UI", 9), padding=(10, 4), 
                       background="#253241", foreground="#eff6ff", borderwidth=0)
        style.map("TaskbarWindow.TButton", background=[("active", "#334659")])
        style.configure("DesktopIcon.TFrame", background=theme["bg"])
        style.configure("DesktopIconTitle.TLabel", background=theme["bg"], foreground="#ffffff", 
                       font=("Segoe UI", 9))
        style.configure("DesktopGlyph.TLabel", background=theme["bg"], foreground="#ffffff", 
                       font=("Segoe UI", 22, "bold"), anchor="center")
        style.configure("WindowTitle.TLabel", background=theme["card"], foreground=theme["text"], 
                       font=("Segoe UI", 13, "bold"))
        style.configure("Info.TLabel", background=theme["card"], foreground=theme["text"], 
                       font=("Segoe UI", 10))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 7), 
                       background=theme["accent"], foreground="#ffffff", borderwidth=0)
        style.map("Accent.TButton", background=[("active", self._lighten_color(theme["accent"]))])
        style.configure("Soft.TButton", font=("Segoe UI", 10), padding=(12, 7), 
                       background="#d8e4f2", foreground="#1b2b3c", borderwidth=0)
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 7), 
                       background="#d9534f", foreground="#ffffff", borderwidth=0)
        style.configure("Start.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 6), 
                       background="#1d8f4e", foreground="#ffffff", borderwidth=0)
        style.configure("Treeview", background=theme["card"], fieldbackground=theme["card"], 
                       foreground=theme["text"], rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=theme["accent"], foreground="#ffffff", 
                       font=("Segoe UI", 10, "bold"))
        style.configure("Horizontal.TProgressbar", troughcolor="#d5dfeb", background=theme["accent"])

    def _lighten_color(self, color: str) -> str:
        return "#7c6ce7" if color == "#6c5ce7" else "#6c5ce7"

    def _build_shell(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        desktop = tk.Frame(self.root, bg=self.background_presets[self.current_theme.get()]["bg"])
        desktop.grid(row=0, column=0, sticky="nsew")
        self.desktop_area = desktop
        
        self.background_canvas = tk.Canvas(desktop, highlightthickness=0)
        self.background_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        self._build_desktop_icons()
        self._build_start_menu()
        self.root.bind("<Button-1>", self._handle_root_click, add="+")
        self.root.bind("<Configure>", lambda e: self._draw_background_pattern())

        taskbar = tk.Frame(self.root, bg="#0f0f1a", height=45)
        taskbar.grid(row=1, column=0, sticky="ew")
        taskbar.pack_propagate(False)
        
        start_btn = tk.Button(taskbar, text="◉ Пуск", font=("Segoe UI", 10, "bold"),
                              bg="#1d8f4e", fg="white", bd=0, padx=15, pady=8,
                              command=self.toggle_start_menu)
        start_btn.pack(side="left", padx=10, pady=5)
        
        tk.Label(taskbar, text="Mini-OS", font=("Segoe UI", 10),
                 bg="#0f0f1a", fg="#ffffff").pack(side="left", padx=(5, 20))
        
        self.window_bar = tk.Frame(taskbar, bg="#0f0f1a")
        self.window_bar.pack(side="left", fill="x", expand=True, pady=5)
        
        # Кнопка выхода из системы
        logout_btn = tk.Button(taskbar, text="🚪 Выйти", font=("Segoe UI", 10),
                               bg="#d9534f", fg="white", bd=0, padx=10, pady=5,
                               command=self.logout)
        logout_btn.pack(side="right", padx=10)
        
        tk.Label(taskbar, text=f"👤 {self.current_user}", font=("Segoe UI", 10),
                 bg="#0f0f1a", fg="#ffffff").pack(side="right", padx=10)
        
        clock_label = tk.Label(taskbar, textvariable=self.clock_text, font=("Segoe UI", 10),
                               bg="#0f0f1a", fg="#ffffff")
        clock_label.pack(side="right", padx=10)
    
    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти из системы?"):
            self._log(f"Пользователь {self.current_user} вышел из системы")
            self.root.destroy()
            # Запускаем новое окно входа
            new_root = tk.Tk()
            login_window = LoginWindow(new_root, lambda username: self._start_new_session(new_root, username))
            new_root.mainloop()
    
    def _start_new_session(self, root, username):
        """Запускает новую сессию с другим пользователем"""
        root.destroy()
        new_root = tk.Tk()
        app = MiniOSApp(new_root, username)
        new_root.mainloop()

    def _build_start_menu(self) -> None:
        if self.desktop_area is None:
            return
        
        self.start_menu = tk.Frame(self.desktop_area, bg="#2d2d44", bd=1, relief="solid")
        
        header = tk.Frame(self.start_menu, bg="#3d3d5c")
        header.pack(fill="x")
        
        tk.Label(header, text=f"👤 {self.current_user}", bg="#3d3d5c", fg="#ffffff", 
                font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 0))
        tk.Label(header, text="Системные инструменты", bg="#3d3d5c", fg="#aaaaaa", 
                font=("Segoe UI", 10)).pack(anchor="w", padx=12, pady=(0, 10))
        
        actions = tk.Frame(self.start_menu, bg="#2d2d44")
        actions.pack(fill="both", expand=True, padx=10, pady=10)
        
        buttons = [
            ("📋 Диспетчер задач", self.open_task_manager),
            ("📊 Монитор системы", self.open_system_monitor),
            ("📝 Журнал событий", self.open_log_window),
            ("🧮 Калькулятор", self.open_calculator_window),
            ("📁 Проводник", self.open_file_explorer),
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(actions, text=text, command=cmd,
                           font=("Segoe UI", 10), anchor="w",
                           bg="#3d3d5c", fg="#ffffff", bd=0, padx=10, pady=8)
            btn.pack(fill="x", pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#4d4d6c"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#3d3d5c"))
        
        sep = tk.Frame(actions, height=1, bg="#4d4d6c")
        sep.pack(fill="x", pady=10)
        
        shutdown_btn = tk.Button(actions, text="⏻ Выключение", command=self.shutdown_system,
                                font=("Segoe UI", 10), bg="#d9534f", fg="#ffffff", bd=0, pady=8)
        shutdown_btn.pack(fill="x", pady=2)
        shutdown_btn.bind("<Enter>", lambda e: shutdown_btn.configure(bg="#e0635f"))
        shutdown_btn.bind("<Leave>", lambda e: shutdown_btn.configure(bg="#d9534f"))

    def _build_desktop_icons(self) -> None:
        if self.desktop_area is None:
            return
        
        theme = self.background_presets[self.current_theme.get()]
        bg_color = theme["bg"]
        
        icon_specs = [
            ("Диспетчер задач", "📋", self.open_task_manager),
            ("Монитор системы", "📊", self.open_system_monitor),
            ("Журнал событий", "📝", self.open_log_window),
            ("Калькулятор", "🧮", self.open_calculator_window),
            ("Проводник", "📁", self.open_file_explorer),
        ]
        
        for index, (title, icon, action) in enumerate(icon_specs):
            x_pos = 28
            y_pos = 26 + index * 95
            
            icon_frame = tk.Frame(self.desktop_area, bg=bg_color, bd=0)
            icon_frame.place(x=x_pos, y=y_pos, width=130, height=80)
            
            icon_label = tk.Label(icon_frame, text=icon, font=("Segoe UI", 22),
                                 bg=bg_color, fg="#ffffff")
            icon_label.pack(pady=(5, 2))
            
            caption = tk.Label(icon_frame, text=title, font=("Segoe UI", 8),
                               bg=bg_color, fg="#ffffff", wraplength=110)
            caption.pack()
            
            for widget in (icon_frame, icon_label, caption):
                widget.bind("<Button-1>", lambda _event, current=title: self.desktop_selection.set(current))
                widget.bind("<Double-Button-1>", lambda _event, current=action: current())
                widget.bind("<Button-3>", lambda e, t=title, a=action: self._show_icon_context_menu(e, t, a))
            
            self.desktop_icons[title] = {"frame": icon_frame, "action": action, "title": title}

    def _show_icon_context_menu(self, event: tk.Event, title: str, action: Callable) -> None:
        menu = tk.Menu(self.root, tearoff=0)
        open_instances = [p for p in self.running_processes if p.definition.name == title]
        
        menu.add_command(label="Открыть новый экземпляр", command=action)
        
        if open_instances:
            menu.add_separator()
            menu.add_command(label="Закрыть все окна", command=lambda: self._close_all_instances(title))
        
        menu.post(event.x_root, event.y_root)

    def _close_all_instances(self, app_name: str) -> None:
        instances = [p for p in self.running_processes if p.definition.name == app_name]
        for instance in instances:
            self._force_close_app(instance)

    def _get_next_instance_num(self, app_name: str) -> int:
        if app_name not in self.instance_counter:
            self.instance_counter[app_name] = 1
            return 1
        self.instance_counter[app_name] += 1
        return self.instance_counter[app_name]

    def _reset_instance_counter(self, app_name: str) -> None:
        if len([p for p in self.running_processes if p.definition.name == app_name]) == 0:
            self.instance_counter[app_name] = 0

    def _force_close_app(self, instance: ProcessInstance) -> None:
        window_key = self.process_to_window.get(f"{instance.definition.name}_{instance.instance_num}")
        
        if window_key and window_key in self.window_states:
            self.window_states[window_key]["frame"].destroy()
            del self.window_states[window_key]
        
        if window_key and window_key in self.taskbar_buttons:
            self.taskbar_buttons[window_key].destroy()
            del self.taskbar_buttons[window_key]
        
        self.running_processes = [p for p in self.running_processes if p != instance]
        self._reset_instance_counter(instance.definition.name)
        self._refresh_process_views()
        self._log(f"Закрыт: {instance.definition.name} (PID {instance.pid})")

    def toggle_start_menu(self) -> None:
        if self.start_menu is None or self.desktop_area is None:
            return
        if self.start_menu_visible:
            self.start_menu.place_forget()
            self.start_menu_visible = False
            return
        
        self.root.update_idletasks()
        desktop_height = max(self.desktop_area.winfo_height(), 640)
        menu_height = 440
        self.start_menu.place(x=12, y=desktop_height - menu_height - 60, width=260, height=menu_height)
        self.start_menu.lift()
        self.start_menu_visible = True

    def _handle_root_click(self, event: tk.Event) -> None:
        if not self.start_menu_visible or self.start_menu is None:
            return
        current = event.widget
        while current is not None:
            if current == self.start_menu:
                return
            current = current.master
        self.start_menu.place_forget()
        self.start_menu_visible = False

    def shutdown_system(self) -> None:
        if messagebox.askyesno("Выключение", "Вы действительно хотите выключить Mini-OS?"):
            self._log("Система выключается...")
            self.root.after(500, self.root.destroy)

    def _show_internal_window(self, key: str, title: str, width: int, height: int, 
                              builder: Callable[[tk.Frame], None], process_name: str | None = None, 
                              instance_num: int = 1) -> None:
        if self.desktop_area is None:
            return
        
        state = self.window_states.get(key)
        if state is None:
            frame = tk.Frame(self.desktop_area, bg="#3d3d5c", bd=1, relief="solid")
            
            titlebar = tk.Frame(frame, bg="#3d3d5c", height=34)
            titlebar.pack(fill="x")
            
            title_label = tk.Label(titlebar, text=title, bg="#3d3d5c", fg="#ffffff", 
                                  font=("Segoe UI", 10, "bold"))
            title_label.pack(side="left", padx=10)
            
            tk.Button(titlebar, text="✕", width=4, bd=0, bg="#d9534f", fg="#ffffff",
                     command=lambda: self._close_window_by_key(key)).pack(side="right", padx=6, pady=4)
            tk.Button(titlebar, text="─", width=4, bd=0, bg="#3d3d5c", fg="#ffffff",
                     command=lambda: self._minimize_window_by_key(key)).pack(side="right", padx=(0, 4), pady=4)
            
            body = tk.Frame(frame, bg="#2d2d44")
            body.pack(fill="both", expand=True, padx=10, pady=10)
            builder(body)
            
            offset = (self.window_counter % 5) * 30
            x_pos = 160 + offset
            y_pos = 80 + offset
            frame.place(x=x_pos, y=y_pos, width=width, height=height)
            self.window_counter += 1
            
            self.window_states[key] = {
                "frame": frame, "body": body, "process_name": process_name,
                "instance_num": instance_num, "visible": True, "minimized": False,
                "title": title, "x": x_pos, "y": y_pos
            }
            
            if process_name:
                self.process_to_window[f"{process_name}_{instance_num}"] = key
            
            frame.bind("<Button-1>", lambda e, k=key: self._bring_to_front(k), add="+")
            titlebar.bind("<Button-1>", lambda e, k=key: self._bring_to_front(k), add="+")
            title_label.bind("<Button-1>", lambda e, k=key: self._bring_to_front(k), add="+")
            
            for widget in (frame, titlebar, title_label):
                widget.bind("<Button-1>", lambda event, k=key: self._start_drag(event, k), add="+")
                widget.bind("<B1-Motion>", self._drag)
                widget.bind("<ButtonRelease-1>", self._stop_drag)
        else:
            if state.get("minimized"):
                state["frame"].place(x=state.get("x", 160), y=state.get("y", 80))
                state["minimized"] = False
            self._bring_to_front(key)
        
        self._sync_taskbar_button(key)

    def _bring_to_front(self, key: str) -> None:
        state = self.window_states.get(key)
        if state and not state.get("minimized"):
            state["frame"].lift()
            state["frame"].focus_set()

    def _close_window_by_key(self, key: str) -> None:
        state = self.window_states.get(key)
        if state:
            process_name = state.get("process_name")
            instance_num = state.get("instance_num")
            if process_name and instance_num:
                instance = next((p for p in self.running_processes 
                               if p.definition.name == process_name and p.instance_num == instance_num), None)
                if instance:
                    self._force_close_app(instance)
                else:
                    self._remove_window_by_key(key)
            else:
                self._remove_window_by_key(key)

    def _remove_window_by_key(self, key: str) -> None:
        if key in self.window_states:
            self.window_states[key]["frame"].destroy()
            del self.window_states[key]
        
        if key in self.taskbar_buttons:
            self.taskbar_buttons[key].destroy()
            del self.taskbar_buttons[key]

    def _minimize_window_by_key(self, key: str) -> None:
        state = self.window_states.get(key)
        if state:
            frame = state["frame"]
            state["x"] = frame.winfo_x()
            state["y"] = frame.winfo_y()
            frame.place_forget()
            state["minimized"] = True
            self._sync_taskbar_button(key)

    def _sync_taskbar_button(self, key: str) -> None:
        if self.window_bar is None:
            return
        
        state = self.window_states.get(key)
        if not state:
            return
        
        title = str(state["title"])
        button = self.taskbar_buttons.get(key)
        
        if button is None:
            button = tk.Button(self.window_bar, text=title, font=("Segoe UI", 9),
                              bg="#2d2d44", fg="#ffffff", bd=0, padx=12, pady=4,
                              command=lambda k=key: self._toggle_window(k))
            button.pack(side="left", padx=(0, 5))
            button.bind("<Button-3>", lambda e, k=key: self._show_window_context_menu(e, k))
            button.bind("<Enter>", lambda e, b=button: b.configure(bg="#3d3d5c"))
            button.bind("<Leave>", lambda e, b=button: b.configure(bg="#2d2d44"))
            self.taskbar_buttons[key] = button
        
        suffix = " [свернуто]" if state.get("minimized") else ""
        button.config(text=f"{title}{suffix}")

    def _toggle_window(self, key: str) -> None:
        state = self.window_states.get(key)
        if state:
            if state.get("minimized"):
                state["frame"].place(x=state.get("x", 160), y=state.get("y", 80))
                state["minimized"] = False
                self._bring_to_front(key)
            else:
                frame = state["frame"]
                state["x"] = frame.winfo_x()
                state["y"] = frame.winfo_y()
                frame.place_forget()
                state["minimized"] = True
            self._sync_taskbar_button(key)

    def _show_window_context_menu(self, event: tk.Event, key: str) -> None:
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Закрыть окно", command=lambda: self._close_window_by_key(key))
        menu.post(event.x_root, event.y_root)

    def _start_drag(self, event: tk.Event, key: str) -> None:
        self.drag_data["key"] = key
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        self._bring_to_front(key)

    def _drag(self, event: tk.Event) -> None:
        key = self.drag_data.get("key")
        if not key:
            return
        
        state = self.window_states.get(str(key))
        if not state or state.get("minimized"):
            return
        
        frame = state["frame"]
        dx = event.x_root - self.drag_data["x"]
        dy = event.y_root - self.drag_data["y"]
        
        new_x = max(0, frame.winfo_x() + dx)
        new_y = max(0, frame.winfo_y() + dy)
        frame.place(x=new_x, y=new_y)
        
        state["x"] = new_x
        state["y"] = new_y
        
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root

    def _stop_drag(self, _event: tk.Event) -> None:
        self.drag_data["key"] = None

    def open_task_manager(self) -> None:
        for process in self.running_processes:
            if process.definition.name == "Диспетчер задач":
                window_key = self.process_to_window.get(f"Диспетчер задач_{process.instance_num}")
                if window_key and window_key in self.window_states:
                    self._bring_to_front(window_key)
                return
        
        instance_num = self._get_next_instance_num("Диспетчер задач")
        definition = next((item for item in self.process_catalog if item.name == "Диспетчер задач"), None)
        instance = ProcessInstance(pid=self.pid_counter + 1, definition=definition, instance_num=instance_num)
        self.pid_counter += 1
        self.running_processes.append(instance)
        key = f"task_manager_{instance_num}"
        self.process_to_window[f"Диспетчер задач_{instance_num}"] = key
        self._show_internal_window(key, "Диспетчер задач", 760, 430, 
                                   self._build_task_manager_window, "Диспетчер задач", instance_num)
        self._refresh_process_views()
        self._log(f"Запуск: Диспетчер задач (PID {instance.pid})")

    def open_system_monitor(self) -> None:
        for process in self.running_processes:
            if process.definition.name == "Монитор системы":
                window_key = self.process_to_window.get(f"Монитор системы_{process.instance_num}")
                if window_key and window_key in self.window_states:
                    self._bring_to_front(window_key)
                return
        
        instance_num = self._get_next_instance_num("Монитор системы")
        definition = next((item for item in self.process_catalog if item.name == "Монитор системы"), None)
        instance = ProcessInstance(pid=self.pid_counter + 1, definition=definition, instance_num=instance_num)
        self.pid_counter += 1
        self.running_processes.append(instance)
        key = f"system_monitor_{instance_num}"
        self.process_to_window[f"Монитор системы_{instance_num}"] = key
        self._show_internal_window(key, "Монитор системы", 500, 320, 
                                   self._build_system_monitor_window, "Монитор системы", instance_num)
        self._refresh_process_views()
        self._log(f"Запуск: Монитор системы (PID {instance.pid})")

    def open_log_window(self) -> None:
        for process in self.running_processes:
            if process.definition.name == "Журнал событий":
                window_key = self.process_to_window.get(f"Журнал событий_{process.instance_num}")
                if window_key and window_key in self.window_states:
                    self._bring_to_front(window_key)
                return
        
        instance_num = self._get_next_instance_num("Журнал событий")
        definition = next((item for item in self.process_catalog if item.name == "Журнал событий"), None)
        instance = ProcessInstance(pid=self.pid_counter + 1, definition=definition, instance_num=instance_num)
        self.pid_counter += 1
        self.running_processes.append(instance)
        key = f"log_window_{instance_num}"
        self.process_to_window[f"Журнал событий_{instance_num}"] = key
        self._show_internal_window(key, "Журнал событий", 680, 320, 
                                   self._build_log_window, "Журнал событий", instance_num)
        self._refresh_process_views()
        self._log(f"Запуск: Журнал событий (PID {instance.pid})")

    def open_calculator_window(self) -> None:
        instance_num = self._get_next_instance_num("Калькулятор")
        definition = next((item for item in self.process_catalog if item.name == "Калькулятор"), None)
        instance = ProcessInstance(pid=self.pid_counter + 1, definition=definition, instance_num=instance_num)
        self.pid_counter += 1
        self.running_processes.append(instance)
        key = f"calculator_{instance_num}"
        self.process_to_window[f"Калькулятор_{instance_num}"] = key
        self._show_internal_window(key, "Калькулятор", 320, 400, 
                                   self._build_calculator_window, "Калькулятор", instance_num)
        self._refresh_process_views()
        self._log(f"Запуск: Калькулятор (PID {instance.pid})")
    
    def open_file_explorer(self) -> None:
        instance_num = self._get_next_instance_num("Проводник")
        definition = next((item for item in self.process_catalog if item.name == "Проводник"), None)
        instance = ProcessInstance(pid=self.pid_counter + 1, definition=definition, instance_num=instance_num)
        self.pid_counter += 1
        self.running_processes.append(instance)
        key = f"explorer_{instance_num}"
        self.process_to_window[f"Проводник_{instance_num}"] = key
        self._show_internal_window(key, "Проводник", 600, 450, 
                                   self._build_explorer_window, "Проводник", instance_num)
        self._refresh_process_views()
        self._log(f"Запуск: Проводник (PID {instance.pid})")
    
    def _create_internal_dialog(self, parent_frame, title: str, fields: list, on_submit: Callable) -> None:
        """Создает диалоговое окно внутри указанного фрейма"""
        dialog_frame = tk.Frame(parent_frame, bg="#2d2d44", bd=2, relief="solid")
        dialog_frame.place(relx=0.5, rely=0.5, anchor="center", width=300, height=180)
        dialog_frame.lift()
        
        tk.Label(dialog_frame, text=title, font=("Segoe UI", 12, "bold"),
                fg="white", bg="#2d2d44").pack(pady=15)
        
        entries = []
        for field in fields:
            tk.Label(dialog_frame, text=field, font=("Segoe UI", 10),
                    fg="white", bg="#2d2d44").pack(pady=5)
            entry = tk.Entry(dialog_frame, font=("Segoe UI", 10), width=25)
            entry.pack(pady=5)
            entries.append(entry)
        
        button_frame = tk.Frame(dialog_frame, bg="#2d2d44")
        button_frame.pack(pady=15)
        
        def submit():
            values = [e.get() for e in entries]
            if on_submit(values):
                dialog_frame.destroy()
        
        def cancel():
            dialog_frame.destroy()
        
        tk.Button(button_frame, text="Создать", command=submit,
                 bg="#4CAF50", fg="white", bd=0, padx=15, pady=5).pack(side="left", padx=10)
        tk.Button(button_frame, text="Отмена", command=cancel,
                 bg="#d9534f", fg="white", bd=0, padx=15, pady=5).pack(side="left", padx=10)
        
        if entries:
            entries[0].focus()
    
    def _build_explorer_window(self, body: tk.Frame) -> None:
        """Построение окна проводника внутри Mini-OS"""
        self.explorer_body = body
        
        nav_frame = tk.Frame(body, bg="#3d3d5c", height=40)
        nav_frame.pack(fill="x")
        nav_frame.pack_propagate(False)
        
        tk.Button(nav_frame, text="← Назад", command=self._explorer_go_back,
                 font=("Segoe UI", 9), bg="#4a90e2", fg="white", bd=0, padx=10, pady=5).pack(side="left", padx=5)
        
        self.explorer_path_label = tk.Label(nav_frame, text="Desktop", font=("Segoe UI", 9),
                                            fg="white", bg="#3d3d5c")
        self.explorer_path_label.pack(side="left", padx=10)
        
        actions_frame = tk.Frame(body, bg="#2d2d44", height=35)
        actions_frame.pack(fill="x")
        actions_frame.pack_propagate(False)
        
        tk.Button(actions_frame, text="📁 Создать папку", command=self._explorer_create_folder_dialog,
                 font=("Segoe UI", 9), bg="#4CAF50", fg="white", bd=0, padx=10, pady=5).pack(side="left", padx=5)
        tk.Button(actions_frame, text="📄 Создать файл", command=self._explorer_create_file_dialog,
                 font=("Segoe UI", 9), bg="#2196F3", fg="white", bd=0, padx=10, pady=5).pack(side="left", padx=5)
        
        list_frame = tk.Frame(body, bg="#2d2d44")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.explorer_listbox = tk.Listbox(list_frame, bg="#1e1e2e", fg="white", 
                                           font=("Segoe UI", 10), selectmode=tk.SINGLE,
                                           yscrollcommand=scrollbar.set)
        self.explorer_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.explorer_listbox.yview)
        
        self.explorer_listbox.bind("<Double-Button-1>", self._explorer_on_double_click)
        self.explorer_listbox.bind("<Button-3>", self._explorer_show_context_menu)
        
        self._explorer_refresh()
    
    def _explorer_create_folder_dialog(self):
        self._create_internal_dialog(self.explorer_body, "Создание папки", ["Имя папки:"], self._explorer_create_folder)
    
    def _explorer_create_folder(self, values):
        name = values[0].strip()
        if name:
            if self.file_explorer.create_folder(name):
                self._explorer_refresh()
                self._log(f"Создана папка: {name}")
                return True
            else:
                messagebox.showerror("Ошибка", "Папка уже существует!")
                return False
        return False
    
    def _explorer_create_file_dialog(self):
        self._create_internal_dialog(self.explorer_body, "Создание файла", ["Имя файла:"], self._explorer_create_file)
    
    def _explorer_create_file(self, values):
        name = values[0].strip()
        if name:
            if not name.endswith('.txt'):
                name += '.txt'
            if self.file_explorer.create_file(name):
                self._explorer_refresh()
                self._log(f"Создан файл: {name}")
                return True
            else:
                messagebox.showerror("Ошибка", "Файл уже существует!")
                return False
        return False
    
    def _explorer_refresh(self):
        self.explorer_listbox.delete(0, tk.END)
        items = self.file_explorer.get_current_items()
        
        self.explorer_path_label.config(text=self.file_explorer.current_path)
        
        if self.file_explorer.current_path != "Desktop":
            self.explorer_listbox.insert(tk.END, "📁 ..")
        
        for name, info in items.items():
            if info["type"] == "folder":
                self.explorer_listbox.insert(tk.END, f"📁 {name}")
            else:
                self.explorer_listbox.insert(tk.END, f"📄 {name}")
    
    def _explorer_on_double_click(self, event):
        selection = self.explorer_listbox.curselection()
        if selection:
            item = self.explorer_listbox.get(selection[0])
            name = item[2:]
            if name == "..":
                self.file_explorer.go_back()
                self._explorer_refresh()
            elif item.startswith("📁"):
                if self.file_explorer.navigate_to(name):
                    self._explorer_refresh()
    
    def _explorer_show_context_menu(self, event):
        selection = self.explorer_listbox.curselection()
        if selection:
            item = self.explorer_listbox.get(selection[0])
            name = item[2:]
            if name != "..":
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Удалить", command=lambda: self._explorer_delete_item(name))
                menu.post(event.x_root, event.y_root)
    
    def _explorer_delete_item(self, name):
        if messagebox.askyesno("Удаление", f"Удалить '{name}'?"):
            self.file_explorer.delete_item(name)
            self._explorer_refresh()
            self._log(f"Удален: {name}")
    
    def _explorer_go_back(self):
        if self.file_explorer.go_back():
            self._explorer_refresh()

    def _build_task_manager_window(self, body: tk.Frame) -> None:
        columns = ("pid", "name", "status", "cpu")
        self.process_tree = ttk.Treeview(body, columns=columns, show="headings", selectmode="browse")
        self.process_tree.pack(fill="both", expand=True)
        
        col_names = [("pid", "PID", 80), ("name", "Имя", 200), ("status", "Статус", 100), ("cpu", "CPU (%)", 150)]
        
        for col_id, col_name, width in col_names:
            self.process_tree.heading(col_id, text=col_name)
            self.process_tree.column(col_id, width=width, anchor="center")
        
        btn_frame = tk.Frame(body, bg="#2d2d44")
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(btn_frame, text="Остановить процесс", font=("Segoe UI", 10),
                 bg="#d9534f", fg="white", padx=15, pady=5,
                 command=self._stop_selected_process).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Обновить", font=("Segoe UI", 10),
                 bg="#4a90e2", fg="white", padx=15, pady=5,
                 command=self._refresh_process_views).pack(side="left", padx=5)
        
        self._refresh_process_views()

    def _stop_selected_process(self) -> None:
        if self.process_tree and self.process_tree.selection():
            selected = self.process_tree.selection()[0]
            values = self.process_tree.item(selected)['values']
            pid = int(values[0])
            process = next((p for p in self.running_processes if p.pid == pid), None)
            if process:
                self._force_close_app(process)

    def _build_system_monitor_window(self, body: tk.Frame) -> None:
        main_frame = tk.Frame(body, bg="#2d2d44")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="📊 Монитор состояния системы", font=("Segoe UI", 18, "bold"),
                fg="#ffffff", bg="#2d2d44").pack(pady=(0, 20))
        
        cpu_frame = tk.Frame(main_frame, bg="#2d2d44", relief="groove", bd=2)
        cpu_frame.pack(fill="x", pady=10)
        
        tk.Label(cpu_frame, text="Процессор (CPU)", font=("Segoe UI", 14, "bold"),
                fg="#ffffff", bg="#2d2d44").pack(anchor="w", padx=15, pady=(15, 10))
        
        self.cpu_value_label = tk.Label(cpu_frame, text=f"{self.cpu_usage.get()}%", 
                                        font=("Segoe UI", 32, "bold"), fg="#6c5ce7", bg="#2d2d44")
        self.cpu_value_label.pack(anchor="w", padx=15)
        
        self.cpu_bar = ttk.Progressbar(cpu_frame, style="Horizontal.TProgressbar", 
                                       maximum=100, variable=self.cpu_usage, length=450)
        self.cpu_bar.pack(fill="x", padx=15, pady=(15, 15))
        
        proc_frame = tk.Frame(main_frame, bg="#2d2d44", relief="groove", bd=2)
        proc_frame.pack(fill="x", pady=10)
        
        tk.Label(proc_frame, text="Активные процессы", font=("Segoe UI", 14, "bold"),
                fg="#ffffff", bg="#2d2d44").pack(anchor="w", padx=15, pady=(15, 10))
        
        self.process_count_label = tk.Label(proc_frame, text="0", 
                                            font=("Segoe UI", 28, "bold"), fg="#4CAF50", bg="#2d2d44")
        self.process_count_label.pack(anchor="w", padx=15, pady=(5, 15))

    def _build_log_window(self, body: tk.Frame) -> None:
        self.log_text = tk.Text(body, wrap="word", bg="#0f1a28", fg="#e8f1ff", 
                                relief="flat", font=("Consolas", 10), padx=12, pady=10)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        self._refresh_log_view()

    def _build_calculator_window(self, body: tk.Frame) -> None:
        calculator_display = tk.StringVar(value="0")
        
        display = tk.Entry(body, textvariable=calculator_display, justify="right", 
                          font=("Segoe UI", 16), bg="#2d2d44", fg="#ffffff")
        display.pack(fill="x", pady=(0, 12))
        
        grid = tk.Frame(body, bg="#2d2d44")
        grid.pack(fill="both", expand=True)
        
        def calc_click(value: str):
            if value == "C":
                calculator_display.set("0")
            elif value == "=":
                try:
                    result = eval(calculator_display.get())
                    calculator_display.set(str(result))
                except:
                    calculator_display.set("Ошибка")
            else:
                current = calculator_display.get()
                if current in ["0", "Ошибка"]:
                    current = ""
                calculator_display.set(current + value)
        
        buttons = ["7", "8", "9", "/", "4", "5", "6", "*", "1", "2", "3", "-",
                   "0", ".", "C", "+", "="]
        
        for index, value in enumerate(buttons):
            row = index // 4
            column = index % 4
            grid.grid_columnconfigure(column, weight=1)
            btn = tk.Button(grid, text=value, font=("Segoe UI", 12),
                           bg="#4a90e2" if value == "=" else "#3d3d5c",
                           fg="white", bd=0, padx=5, pady=10,
                           command=lambda v=value: calc_click(v))
            btn.grid(row=row, column=column, sticky="nsew", padx=2, pady=2)

    def _refresh_process_views(self) -> None:
        process_count = len(self.running_processes)
        self.summary_text.set(f"Активных процессов: {process_count}")
        
        if self.process_count_label and self.process_count_label.winfo_exists():
            self.process_count_label.config(text=str(process_count))
        
        if self.process_tree and self.process_tree.winfo_exists():
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
            for p in self.running_processes:
                cpu_display = f"{random.randint(1, 30)}%"
                self.process_tree.insert("", "end", values=(
                    p.pid, p.definition.name, p.status, cpu_display
                ))
        
        self._update_cpu_display()

    def _refresh_log_view(self) -> None:
        if self.log_text and self.log_text.winfo_exists():
            self.log_text.configure(state="normal")
            self.log_text.delete(1.0, "end")
            if self.log_messages:
                self.log_text.insert("end", "\n".join(self.log_messages[-100:]) + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    def _seed_initial_state(self) -> None:
        self._log("Рабочий стол загружен")
        self._refresh_process_views()

    def _update_clock(self) -> None:
        self.clock_text.set(time.strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _schedule_cpu_update(self) -> None:
        active_load = sum(p.definition.base_cpu for p in self.running_processes)
        variation = random.randint(-6, 8)
        new_cpu = max(3, min(96, active_load + variation))
        self.cpu_usage.set(new_cpu)
        
        if self.process_tree and self.process_tree.winfo_exists():
            for i, item in enumerate(self.process_tree.get_children()):
                current_cpu = random.randint(1, min(40, new_cpu))
                self.process_tree.set(item, "cpu", f"{current_cpu}%")
        
        self._update_cpu_display()
        self.root.after(1500, self._schedule_cpu_update)

    def _update_cpu_display(self) -> None:
        if self.cpu_value_label and self.cpu_value_label.winfo_exists():
            self.cpu_value_label.config(text=f"{self.cpu_usage.get()}%")
        if self.cpu_bar and self.cpu_bar.winfo_exists():
            self.cpu_bar['value'] = self.cpu_usage.get()

    def _log(self, message: str) -> None:
        timestamp = self.clock_text.get()
        self.log_messages.append(f"[{timestamp}] {message}")
        self._refresh_log_view()


def main() -> None:
    root = tk.Tk()
    login_window = LoginWindow(root, lambda username: start_os(root, username))
    root.mainloop()


def start_os(old_root, username):
    """Запускает основное приложение после успешного входа"""
    old_root.destroy()
    new_root = tk.Tk()
    app = MiniOSApp(new_root, username)
    new_root.mainloop()


if __name__ == "__main__":
    main()