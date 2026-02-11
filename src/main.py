
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import threading
from browser_controller import BrowserController
from utils import Logger, normalize_date, normalize_time
from doc_parser import parse_google_doc_text
from updater import get_current_version, check_for_update, download_update, apply_update

CONFIG_FILE = 'config.json'
APP_VERSION = get_current_version()

class DailyReporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Daily Progress Reporter v{APP_VERSION}")
        self.root.geometry("750x780")
        self.root.resizable(False, False)
        
        # Set app icon (if exists)
        try:
            self.root.iconbitmap('assets/app_icon.ico')
        except Exception:
            pass

        self.config = self.load_config()
        self.setup_style()
        
        # UI Variables
        self.doc_url_var = tk.StringVar(value=self.config.get('last_doc_url', ''))
        self.username_var = tk.StringVar(value=self.config.get('username', ''))
        self.password_var = tk.StringVar(value=self.config.get('password', ''))
        self.auth_code_var = tk.StringVar()
        self.completion_mode = tk.IntVar(value=self.config.get('completion_mode', 2))
        # 1 = Normal, 2 = Headless
        self.browser_mode = tk.IntVar(value=2 if self.config.get('browser_headless', False) else 1)

        # Screen management
        self.current_screen = None
        
        # Status bar at bottom (shared between screens)
        self.create_status_bar()
        
        # Update state
        self.update_info = None  # Will hold (new_version, download_url)
        
        # Show appropriate screen based on browser status
        # Bind Enter key to start automation
        self.root.bind('<Return>', lambda e: self.start_automation())
        
        if self.is_browser_ready():
            self.show_main_screen()
        else:
            self.show_setup_screen()

    def setup_style(self):
        """Modern styling with better colors"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        BG_COLOR = "#f5f5f5"
        ACCENT_COLOR = "#0066CC"
        
        self.root.configure(bg=BG_COLOR)
        
        # Button styles
        style.configure('Accent.TButton',
            background=ACCENT_COLOR,
            foreground='white',
            borderwidth=0,
            focuscolor='none',
            font=('Segoe UI', 10, 'bold'),
            padding=10
        )
        
        style.map('Accent.TButton',
            background=[('active', '#0052A3')]
        )
        
        style.configure('TLabel',
            background=BG_COLOR,
            font=('Segoe UI', 9)
        )
        
        style.configure('TLabelframe',
            background=BG_COLOR,
            borderwidth=1,
            relief='solid'
        )
        
        style.configure('TLabelframe.Label',
            background=BG_COLOR,
            font=('Segoe UI', 9, 'bold'),
            foreground='#333'
        )
        
        # White-background variants for widgets inside white cards
        style.configure('White.TLabel',
            background='white',
            font=('Segoe UI', 9)
        )
        
        style.configure('White.TRadiobutton',
            background='white',
            font=('Segoe UI', 9)
        )
        style.map('White.TRadiobutton',
            background=[('active', 'white')]
        )

    def create_menu(self):
        """Add menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Berkas", menu=file_menu)
        file_menu.add_command(label="Simpan Konfigurasi", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Keluar", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Alat", menu=tools_menu)
        tools_menu.add_command(label="Bersihkan Log", command=self.clear_log)
        tools_menu.add_command(label="Buka Folder Log", command=self.open_log_folder)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Bantuan", menu=help_menu)
        help_menu.add_command(label="Panduan Pengguna", command=self.show_user_guide)
        help_menu.add_command(label="Format Dokumen", command=self.show_doc_format)
        help_menu.add_separator()
        help_menu.add_command(label="Tentang", command=self.show_about)

    def create_widgets(self):
        # Main Container
        self.current_screen = ttk.Frame(self.root, padding="20 20 20 10")
        main_frame = self.current_screen
        main_frame.pack(fill='both', expand=True)

        # Header with icon/logo space
        header_frame = tk.Frame(main_frame, bg="#f5f5f5")
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Try to load logo
        try:
            from PIL import Image, ImageTk
            if os.path.exists('assets/logo_small.png'):
                logo_img = Image.open('assets/logo_small.png')
                logo_img = logo_img.resize((48, 48), Image.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(header_frame, image=logo_photo, bg="#f5f5f5")
                logo_label.image = logo_photo  # Keep reference
                logo_label.pack(side='left', padx=(0, 15))
        except Exception:
            pass
        
        title_frame = tk.Frame(header_frame, bg="#f5f5f5")
        title_frame.pack(side='left', fill='both', expand=True)
        
        header = tk.Label(title_frame, text="Pelapor Kinerja Harian", 
                         font=("Segoe UI", 18, "bold"), fg="#222", bg="#f5f5f5")
        header.pack(anchor='w')
        
        subtitle = tk.Label(title_frame, text="Otomatisasi laporan kinerja Anda dalam hitungan detik", 
                           font=("Segoe UI", 9), fg="#666", bg="#f5f5f5")
        subtitle.pack(anchor='w')

        # --- TWO COLUMN LAYOUT ---
        content_frame = tk.Frame(main_frame, bg="#f5f5f5")
        content_frame.pack(fill='both', expand=True)
        
        left_col = tk.Frame(content_frame, bg="#f5f5f5")
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_col = tk.Frame(content_frame, bg="#f5f5f5")
        right_col.pack(side='right', fill='both', expand=True)

        # --- LEFT COLUMN: Configuration ---
        config_frame = ttk.LabelFrame(left_col, text=" 📄 Dokumen & Akun ", padding="15")
        config_frame.pack(fill='both', expand=True)
        
        # White background card for left section (bordered like 2FA card)
        config_inner = tk.Frame(config_frame, bg='white', relief='solid', borderwidth=1)
        config_inner.pack(fill='both', expand=True)

        # Doc URL with helper
        doc_frame = tk.Frame(config_inner, bg='white')
        doc_frame.pack(fill='x', padx=10, pady=(10, 10))
        
        ttk.Label(doc_frame, text="Link Google Doc:", style='White.TLabel').pack(anchor='w')
        self.doc_entry = ttk.Entry(doc_frame, textvariable=self.doc_url_var, font=('Segoe UI', 9))
        self.doc_entry.pack(fill='x', pady=(2, 0))
        
        helper = tk.Label(doc_frame, text="💡 Perbarui link ini setiap awal bulan", 
                         font=("Segoe UI", 8), fg="#666", bg='white')
        helper.pack(anchor='w', pady=(2, 0))
        
        template_link = tk.Label(doc_frame, text="📥 Unduh Template Dokumen", 
                                font=("Segoe UI", 8, "underline"), fg="#0066CC", bg='white', cursor="hand2")
        template_link.pack(anchor='w', pady=(5, 0))
        template_link.bind("<Button-1>", lambda e: self.open_url("https://docs.google.com/document/d/1Hghqt2kR3D9P-S_AC38_nS5kDoNVhbWDWBA72m7rbFQ/edit?usp=sharing"))

        # Username
        username_frame = tk.Frame(config_inner, bg='white')
        username_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(username_frame, text="Username (NIP):", style='White.TLabel').pack(anchor='w', pady=(0, 2))
        self.user_entry = ttk.Entry(username_frame, textvariable=self.username_var, font=('Segoe UI', 9))
        self.user_entry.pack(fill='x')

        # Password with show/hide toggle
        pwd_frame = tk.Frame(config_inner, bg='white')
        pwd_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(pwd_frame, text="Kata Sandi:", style='White.TLabel').pack(anchor='w')
        
        pwd_inner = tk.Frame(pwd_frame, bg='white')
        pwd_inner.pack(fill='x')
        
        self.pwd_entry = ttk.Entry(pwd_inner, textvariable=self.password_var, 
                                    show="●", font=('Segoe UI', 9))
        self.pwd_entry.pack(side='left', fill='x', expand=True, pady=(2, 0))
        
        self.show_pwd_btn = tk.Button(pwd_inner, text="👁", font=('Segoe UI', 10),
                                      command=self.toggle_password, 
                                      relief='flat', bg='white', cursor='hand2')
        self.show_pwd_btn.pack(side='right', padx=(5, 0))

        # Browser Mode (Normal / Headless)
        browser_mode_frame = tk.Frame(config_inner, bg='white')
        browser_mode_frame.pack(fill='x', padx=10, pady=(10, 10))
        
        # Header with Info Icon
        bm_header = tk.Frame(browser_mode_frame, bg='white')
        bm_header.pack(fill='x', pady=(0, 5))
        
        ttk.Label(bm_header, text="Mode Browser:", style='White.TLabel').pack(side='left')
        
        info_label = tk.Label(bm_header, text="ℹ️", bg='white', fg='#0066CC', cursor='hand2')
        info_label.pack(side='left', padx=(5, 0))
        
        # Tooltip implementation
        def show_tooltip(event):
            # Calculate position relative to the icon using message event
            x = event.x_root + 15
            y = event.y_root + 10
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(info_label)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=(
                "Normal: Browser terlihat di layar (Default)\n"
                "Headless: Browser berjalan di belakang layar (Lebih cepat)"
            ), justify='left', background="#ffffe0", relief='solid', borderwidth=1,
            font=("Segoe UI", 8))
            label.pack()

        def hide_tooltip(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        
        info_label.bind('<Enter>', show_tooltip)
        info_label.bind('<Leave>', hide_tooltip)

        # Radio Buttons
        bm_options = tk.Frame(browser_mode_frame, bg='white')
        bm_options.pack(fill='x')
        
        ttk.Radiobutton(bm_options, text="Normal", variable=self.browser_mode, value=1,
                       style='White.TRadiobutton').pack(side='left', padx=(0, 15))
        ttk.Radiobutton(bm_options, text="Headless", variable=self.browser_mode, value=2,
                       style='White.TRadiobutton').pack(side='left')

        # --- RIGHT COLUMN: Options & Control ---
        options_frame = ttk.LabelFrame(right_col, text=" ⚙️ Opsi Sesi ", padding="15")
        options_frame.pack(fill='both', expand=True)

        # 2FA with better explanation
        auth_info = tk.Frame(options_frame, bg='white', relief='solid', borderwidth=1)
        auth_info.pack(fill='x', pady=(0, 10))
        
        info_label = tk.Label(auth_info, text="🔐 Otentikasi Dua Faktor (2FA)", 
                             font=("Segoe UI", 9, "bold"), bg='white', fg='#333')
        info_label.pack(anchor='w', padx=10, pady=(10, 5))
        
        info_text = tk.Label(auth_info, 
            text="Masukkan kode OTP SEBELUM klik Mulai.\nAtau biarkan kosong dan isi manual nanti.",
            font=("Segoe UI", 8), bg='white', fg='#666', justify='left')
        info_text.pack(anchor='w', padx=10, pady=(0, 10))
        
        auth_entry_frame = tk.Frame(auth_info, bg='white')
        auth_entry_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(auth_entry_frame, text="Kode OTP:", style='White.TLabel').pack(side='left')
        auth_entry = ttk.Entry(auth_entry_frame, textvariable=self.auth_code_var, 
                              width=15, font=('Segoe UI', 11))
        auth_entry.pack(side='left', padx=(10, 0))

        # Completion mode selector (bordered card like 2FA)
        mode_card = tk.Frame(options_frame, bg='white', relief='solid', borderwidth=1)
        mode_card.pack(fill='x', pady=(0, 10))
        
        mode_label = tk.Label(mode_card, text="Setelah terisikan, maka...",
                             font=("Segoe UI", 9, "bold"), bg='white', fg='#333')
        mode_label.pack(anchor='w', padx=10, pady=(10, 5))
        
        ttk.Radiobutton(mode_card,
            text="Biarkan browser dan aplikasi terbuka",
            variable=self.completion_mode, value=1,
            style='White.TRadiobutton').pack(anchor='w', padx=(15, 10))
        ttk.Radiobutton(mode_card,
            text="Tutup browser, biarkan aplikasi terbuka",
            variable=self.completion_mode, value=2,
            style='White.TRadiobutton').pack(anchor='w', padx=(15, 10))
        ttk.Radiobutton(mode_card,
            text="Tutup browser dan aplikasi",
            variable=self.completion_mode, value=3,
            style='White.TRadiobutton').pack(anchor='w', padx=(15, 10), pady=(0, 10))

        # --- UPDATE STATUS SECTION ---
        self.update_card = tk.Frame(options_frame, bg='white', relief='solid', borderwidth=1)
        self.update_card.pack(fill='x', pady=(0, 10))
        
        update_header = tk.Label(self.update_card, text="📦 Pembaruan Aplikasi",
                                font=("Segoe UI", 9, "bold"), bg='white', fg='#333')
        update_header.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.update_status_label = tk.Label(self.update_card,
            text="⏳ Memeriksa pembaruan...",
            font=("Segoe UI", 9), bg='white', fg='#888', justify='left')
        self.update_status_label.pack(anchor='w', padx=10, pady=(0, 5))
        
        self.update_progress_label = tk.Label(self.update_card,
            text="", font=("Segoe UI", 8), bg='white', fg='#666')
        self.update_progress_label.pack(anchor='w', padx=10)
        
        # Container for the update button (shown only when update available)
        self.update_btn_frame = tk.Frame(self.update_card, bg='white')
        self.update_btn_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        # Start checking for updates in background
        threading.Thread(target=self._check_for_update_worker, daemon=True).start()

        # --- ACTION BUTTON (centered, prominent) ---
        btn_container = tk.Frame(main_frame, bg="#f5f5f5")
        btn_container.pack(pady=20)
        
        self.start_btn = tk.Button(btn_container, 
            text="▶  Mulai Otomatisasi", 
            command=self.start_automation,
            bg="#28a745", 
            fg="white", 
            font=("Segoe UI", 12, "bold"),
            padx=40, 
            pady=12,
            relief="flat",
            cursor="hand2",
            borderwidth=0
        )
        self.start_btn.pack()
        
        # Hover effect
        self.start_btn.bind('<Enter>', lambda e: self.start_btn.config(bg="#218838"))
        self.start_btn.bind('<Leave>', lambda e: self.start_btn.config(bg="#28a745"))

        # --- STATUS LOG ---
        log_frame = ttk.LabelFrame(main_frame, text=" 📋 Log Aktivitas ", padding="10")
        log_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # Scrolled text widget
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=12,
            state='disabled',
            bg="#1e1e1e",  # Dark theme for logs
            fg="#d4d4d4",
            font=("Consolas", 9),
            relief="flat",
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Configure log text tags for colored output
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        self.log_text.tag_config('info', foreground='#569cd6')

        self.logger = Logger(self.log_text)
        
        # Log ready state
        self.logger.log("✓ Siap memulai otomatisasi", 'success')

    def is_browser_ready(self):
        """Check if browser is already installed (no logger needed)."""
        try:
            class _NoOpLogger:
                def log(self, *args, **kwargs): pass
            temp_browser = BrowserController(_NoOpLogger(), self.config)
            return temp_browser.is_browser_installed()
        except Exception:
            return False

    def show_setup_screen(self):
        """Show minimalist setup screen for first-time users."""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.root.geometry("600x650")
        
        self.current_screen = ttk.Frame(self.root, padding="20 20 20 10")
        self.current_screen.pack(fill='both', expand=True)
        
        # Header
        header_frame = tk.Frame(self.current_screen, bg="#f5f5f5")
        header_frame.pack(fill='x', pady=(0, 20))
        
        try:
            from PIL import Image, ImageTk
            if os.path.exists('assets/logo_small.png'):
                logo_img = Image.open('assets/logo_small.png')
                logo_img = logo_img.resize((48, 48), Image.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(header_frame, image=logo_photo, bg="#f5f5f5")
                logo_label.image = logo_photo
                logo_label.pack(side='left', padx=(0, 15))
        except Exception:
            pass
        
        title_frame = tk.Frame(header_frame, bg="#f5f5f5")
        title_frame.pack(side='left', fill='both', expand=True)
        
        tk.Label(title_frame, text="Pelapor Kinerja Harian",
                 font=("Segoe UI", 18, "bold"), fg="#222", bg="#f5f5f5").pack(anchor='w')
        tk.Label(title_frame, text="Otomatisasi laporan kinerja harian eKinerja BKN",
                 font=("Segoe UI", 9), fg="#666", bg="#f5f5f5").pack(anchor='w')
        
        # Description card
        desc_frame = tk.Frame(self.current_screen, bg='white', relief='solid', borderwidth=1)
        desc_frame.pack(fill='x', pady=(0, 20))
        
        desc_text = (
            "Selamat datang! Aplikasi ini membantu Anda mengisi\n"
            "laporan kinerja harian secara otomatis dari Google Docs.\n\n"
            "Sebelum memulai, Anda perlu:\n"
            "  1. Unduh format dokumen Google Docs\n"
            "  2. Install browser otomatis (~400MB, sekali saja)"
        )
        tk.Label(desc_frame, text=desc_text,
                 font=("Segoe UI", 10), bg='white', fg='#333',
                 justify='left', padx=20, pady=20).pack(anchor='w')
        
        # Buttons
        btn_frame = tk.Frame(self.current_screen, bg="#f5f5f5")
        btn_frame.pack(fill='x', pady=(0, 15))
        
        guide_btn = tk.Button(btn_frame,
            text="📥  Panduan dan Unduh Format",
            command=lambda: self.open_url(
                "https://docs.google.com/document/d/1Hghqt2kR3D9P-S_AC38_nS5kDoNVhbWDWBA72m7rbFQ/edit?usp=sharing"
            ),
            bg="#0066CC", fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20, pady=10, relief="flat", cursor="hand2")
        guide_btn.pack(fill='x', pady=(0, 8))
        guide_btn.bind('<Enter>', lambda e: guide_btn.config(bg="#0052A3"))
        guide_btn.bind('<Leave>', lambda e: guide_btn.config(bg="#0066CC"))
        
        self.setup_install_btn = tk.Button(btn_frame,
            text="⬇  Install Browser (~400MB)",
            command=self.start_setup_download,
            bg="#ff9800", fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20, pady=10, relief="flat", cursor="hand2")
        self.setup_install_btn.pack(fill='x')
        self.setup_install_btn.bind('<Enter>', lambda e: self.setup_install_btn.config(bg="#e68900"))
        self.setup_install_btn.bind('<Leave>', lambda e: self.setup_install_btn.config(bg="#ff9800"))
        
        # Log area
        log_frame = ttk.LabelFrame(self.current_screen, text=" 📋 Log Aktivitas ", padding="10")
        log_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=10, state='disabled',
            bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 9), relief="flat", wrap='word')
        self.log_text.pack(fill='both', expand=True)
        
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        self.log_text.tag_config('info', foreground='#569cd6')
        
        self.logger = Logger(self.log_text)
        self.logger.log("👋 Selamat datang! Silakan install browser terlebih dahulu.", 'info')
        self.update_status("Setup diperlukan")

    def show_main_screen(self):
        """Show the main application screen (after browser installed)."""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.root.geometry("750x780")
        self.create_menu()
        self.create_widgets()

    def start_setup_download(self):
        """Start browser download from setup screen."""
        self.setup_install_btn.config(state='disabled', text="⏳ Mengunduh...", bg='#6c757d')
        self.update_status("Mengunduh browser...")
        threading.Thread(target=self._setup_download_worker, daemon=True).start()

    def _setup_download_worker(self):
        """Download worker for setup screen — closes app after success."""
        browser = BrowserController(self.logger, self.config)
        self.logger.log("⬇️ Memulai unduhan... (Sekitar 400MB)", 'info')
        self.logger.log("   Mohon tunggu, tergantung kecepatan internet Anda.", 'info')
        self.logger.log("   Proses ini hanya dilakukan sekali saja.", 'info')
        
        try:
            import re as _re
            progress = 0
            
            for line in browser.install_browser():
                match = _re.search(r'(\d+)%', line)
                if match:
                    try:
                        progress = int(match.group(1))
                    except:
                        pass
                else:
                    progress = min(progress + 5, 99)
                
                bar_len = 30
                filled = int(bar_len * progress / 100)
                bar = "|" + "=" * filled + " " * (bar_len - filled) + "|"
                
                if '%' in line:
                    self.logger.log(f"{bar} {progress}%")
                else:
                    self.logger.log(f"   {line}")
            
            self.logger.log("|" + "=" * 30 + "| 100%")
            self.logger.log("✅ Instalasi browser selesai!", 'success')
            
            def _show_success():
                messagebox.showinfo(
                    "Instalasi Berhasil",
                    "Instalasi berhasil! Silakan tutup dan buka kembali aplikasi ini.\n\n"
                    "Klik OK untuk menutup aplikasi."
                )
                self.root.destroy()
            
            self.root.after(0, _show_success)
            
        except Exception as e:
            self.logger.log(f"❌ Gagal mengunduh: {e}", 'error')
            self.root.after(0, lambda: self.setup_install_btn.config(
                state='normal', text="⬇  Coba Lagi", bg='#ff9800'))

    def create_status_bar(self):
        """Bottom status bar"""
        status_frame = tk.Frame(self.root, bg='#e0e0e0', height=25)
        status_frame.pack(side='bottom', fill='x')
        
        self.status_label = tk.Label(status_frame, 
            text=f"Version {APP_VERSION}  |  Ready", 
            bg='#e0e0e0', 
            fg='#666',
            font=('Segoe UI', 8),
            anchor='w'
        )
        self.status_label.pack(side='left', padx=10)

    def toggle_password(self):
        """Show/hide password"""
        if self.pwd_entry.cget('show') == '●':
            self.pwd_entry.config(show='')
            self.show_pwd_btn.config(text='🙈')
        else:
            self.pwd_entry.config(show='●')
            self.show_pwd_btn.config(text='👁')

    def clear_log(self):
        """Clear the log display"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        self.logger.log("Log dibersihkan.", 'info')

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def open_log_folder(self):
        """Open the folder containing log files"""
        import webbrowser
        log_dir = os.getcwd() # Currently logs are in the same dir
        webbrowser.open(log_dir)

    def show_user_guide(self):
        """Open user guide"""
        messagebox.showinfo("User Guide", "Coming soon!")

    def show_doc_format(self):
        """Show document format requirements"""
        format_text = (
            "Document Format Requirements:\n\n"
            "[Date in Indonesian format]\n"
            "[Empty line]\n"
            "[Time Range] :\n"
            "[Category/Activity Name]\n"
            "[Description]\n"
            "[Proof Link]\n\n"
            "Example:\n"
            "2 Februari 2026\n\n"
            "0730 - 1300 :\n"
            "Meeting dan Penyetaraan Desain\n"
            "https://drive.google.com/..."
        )
        messagebox.showinfo("Document Format", format_text)

    def show_about(self):
        """Show about dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("About")
        dialog.geometry("300x200")
        tk.Label(dialog, text=f"Daily Progress Reporter v{APP_VERSION}", font=('Segoe UI', 12, 'bold')).pack(pady=20)
        tk.Label(dialog, text="Created by Your Agent").pack()
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=20)

    def update_status(self, text):
        """Update status bar"""
        self.status_label.config(text=f"Version {APP_VERSION}  |  {text}")

    # --- AUTO-UPDATE METHODS ---
    def _check_for_update_worker(self):
        """Background thread: check GitHub for updates."""
        result = check_for_update(APP_VERSION)
        self.root.after(0, lambda: self._on_update_check_complete(result))

    def _on_update_check_complete(self, result):
        """Called on main thread after update check finishes."""
        if result is None:
            self.update_status_label.config(
                text="✅ Aplikasi terbaru sudah terinstall,\n     tidak ada update baru.",
                fg='#28a745'
            )
        else:
            new_version, download_url = result
            self.update_info = result
            self.update_status_label.config(
                text=f"🔄 Versi baru tersedia: v{new_version}\n     (Anda: v{APP_VERSION})",
                fg='#e65100'
            )
            # Show the update button
            update_btn = tk.Button(self.update_btn_frame,
                text="⬇  Perbarui Sekarang",
                command=self._start_download_update,
                bg="#ff9800", fg="white",
                font=("Segoe UI", 9, "bold"),
                padx=15, pady=5, relief="flat", cursor="hand2")
            update_btn.pack(fill='x')
            update_btn.bind('<Enter>', lambda e: update_btn.config(bg="#e68900"))
            update_btn.bind('<Leave>', lambda e: update_btn.config(bg="#ff9800"))

    def _start_download_update(self):
        """Start downloading the update."""
        if not self.update_info:
            return
        
        # Disable the button and clear it
        for widget in self.update_btn_frame.winfo_children():
            widget.destroy()
        
        self.update_status_label.config(
            text="⬇️ Mengunduh pembaruan...",
            fg='#1565c0'
        )
        self.update_progress_label.config(text="0%")
        
        _, download_url = self.update_info
        threading.Thread(
            target=self._download_update_worker,
            args=(download_url,),
            daemon=True
        ).start()

    def _download_update_worker(self, download_url):
        """Background thread: download the update exe."""
        def progress_cb(percent):
            self.root.after(0, lambda p=percent: self.update_progress_label.config(
                text=f"{'█' * (p // 5)}{'░' * (20 - p // 5)}  {p}%"
            ))
        
        new_exe_path = download_update(download_url, progress_callback=progress_cb)
        self.root.after(0, lambda: self._on_download_complete(new_exe_path))

    def _on_download_complete(self, new_exe_path):
        """Called on main thread after download finishes."""
        if new_exe_path is None:
            self.update_status_label.config(
                text="❌ Gagal mengunduh pembaruan.\n     Coba lagi nanti.",
                fg='#c62828'
            )
            self.update_progress_label.config(text="")
            # Re-show the retry button
            retry_btn = tk.Button(self.update_btn_frame,
                text="🔄  Coba Lagi",
                command=self._start_download_update,
                bg="#ff9800", fg="white",
                font=("Segoe UI", 9, "bold"),
                padx=15, pady=5, relief="flat", cursor="hand2")
            retry_btn.pack(fill='x')
            return
        
        self.update_progress_label.config(text="")
        self.update_status_label.config(
            text="✅ Pembaruan siap! Aplikasi akan\n     ditutup dan dimulai ulang.",
            fg='#28a745'
        )
        
        # Ask for confirmation
        confirm = messagebox.askyesno(
            "Pembaruan Siap",
            "Pembaruan telah diunduh.\n\n"
            "Aplikasi perlu ditutup dan dibuka kembali\n"
            "untuk menerapkan pembaruan.\n\n"
            "Lanjutkan sekarang?"
        )
        
        if confirm:
            success = apply_update(new_exe_path, self.root)
            if not success:
                messagebox.showwarning(
                    "Mode Pengembangan",
                    "Pembaruan otomatis hanya bekerja pada versi .exe.\n"
                    "File pembaruan tersimpan di: " + new_exe_path
                )
        else:
            self.update_status_label.config(
                text="⏸️ Pembaruan ditunda.\n     Akan diterapkan saat dibuka lagi.",
                fg='#f57c00'
            )

    def load_config(self):
        default_config = {
            "last_doc_url": "",
            "web_app_url": "https://asndigital.bkn.go.id/",
            "calendar_url": "https://asndigital.bkn.go.id/progress/calendar",
            "new_entry_url": "https://asndigital.bkn.go.id/progress/new",
            "username": "",
            "password": "",
            "max_backtrack_days": 3,
            "browser_headless": False,
            "keep_browser": False
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded) # Merge loaded into defaults
                    return default_config
            except Exception as e:
                # Silent fail for GUI start
                print(f"Config load error: {e}")
        
        return default_config

    def save_config(self):
        # Update config object with current UI values
        self.config['last_doc_url'] = self.doc_url_var.get()
        self.config['username'] = self.username_var.get()
        self.config['password'] = self.password_var.get()
        self.config['completion_mode'] = self.completion_mode.get()
        self.config['browser_headless'] = (self.browser_mode.get() == 2)
        
        # Ensure other keys exist (handled by load_config defaults, but safe to keep)
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.update_status("Konfigurasi disimpan")
        except Exception as e:
            messagebox.showerror("Gagal Menyimpan", f"Gagal menyimpan konfigurasi:\n{str(e)}")

    def start_automation(self):
        # Validation
        if not self.doc_url_var.get():
            messagebox.showerror("Informasi Kurang", "Mohon masukkan Link Google Doc Anda")
            return

        # Headless Safety Check
        if self.browser_mode.get() == 2:
            # Check if any critical field is missing
            missing_fields = []
            if not self.username_var.get().strip(): missing_fields.append("Username")
            if not self.password_var.get().strip(): missing_fields.append("Password")
            if not self.auth_code_var.get().strip(): missing_fields.append("Kode OTP")
            
            if missing_fields:
                proceed = messagebox.askyesno(
                    "Peringatan Mode Headless",
                    "Anda memilih Mode Headless namun data berikut kosong:\n"
                    f"• {', '.join(missing_fields)}\n\n"
                    "Mode Headless tidak memungkinkan input manual saat browser berjalan.\n"
                    "Proses kemungkinan besar akan gagal/stuck.\n\n"
                    "Lanjutkan?"
                )
                if not proceed:
                    return

        
        self.save_config()
        self.start_btn.config(state='disabled', text="⏳ Sedang Berjalan...", bg='#6c757d')
        self.update_status("Otomatisasi sedang berjalan...")
        self.logger.log("=" * 60, 'info')
        
        thread = threading.Thread(target=self.run_process)
        thread.start()

    def run_process(self):
        try:
            self.logger.log("🚀 Memulai otomatisasi...", 'info')
            
            # Initialize Browser
            browser = BrowserController(self.logger, self.config)
            if not browser.launch_browser():
                self.finish_process(browser)
                return

            # Navigate to Doc
            browser.navigate_to_doc(self.doc_url_var.get())
            
            # Navigate to App and Login
            browser.login(auth_code=self.auth_code_var.get())
            
            # Post-Login Navigation
            if not browser.navigate_to_dashboard():
                self.logger.log("❌ Gagal navigasi ke dashboard Kinerja.", 'error')
                self.finish_process(browser)
                return
            
            # Smart Calendar Navigation
            if not browser.navigate_to_calendar():
                self.logger.log("❌ Gagal mencapai halaman Kalender.", 'error')
                self.finish_process(browser)
                return
            
            # MAIN LOGIC INTEGRATION FROM EXISTING CODE
            import time
            self.logger.log("⏱️ Waiting for page to stabilize...", 'info')
            time.sleep(1)
            
            self.logger.log("📄 Switching to Google Doc tab...", 'info')
            if browser.page_doc:
                browser.page_doc.bring_to_front()
                
            doc_text = browser.get_doc_text()
            if not doc_text:
                self.logger.log("❌ Gagal mendapatkan teks dokumen.", 'error')
                self.finish_process(browser)
                return

            # Debug Dump
            with open("doc_dump.txt", "w", encoding="utf-8") as f:
                f.write(doc_text)
            self.logger.log("💾 Saved raw doc text to 'doc_dump.txt'", 'info')

            entries = parse_google_doc_text(doc_text)
            self.logger.log(f"✓ Parsed {len(entries)} raw entries.", 'success')
            
            valid_entries = []
            for entry in entries:
                norm_date = normalize_date(entry['date_raw'])
                if norm_date:
                    entry['date'] = norm_date
                    valid_entries.append(entry)

            if not valid_entries:
                self.logger.log("⚠️ No valid entries found.", 'warning')
                with open("doc_dump_fail.txt", "w", encoding="utf-8") as f:
                    f.write(doc_text)
                self.finish_process(browser)
                return

            self.logger.log(f"✓ {len(valid_entries)} valid entries ready.", 'success')
            
            # --- SMART FILLING LOGIC ---
            from calendar_scanner import CalendarScanner
            from utils import is_date_fillable
            
            scanner = CalendarScanner(browser.page_app, self.logger)
            existing_entries = scanner.scan_with_previous_week()
            self.logger.log(f"ℹ️ Found entries on {len(existing_entries)} dates.", 'info')

            entries_to_fill = []
            for entry in valid_entries:
                date = entry['date']
                
                if not is_date_fillable(date):
                    self.logger.log(f"  ⊗ Skipping {date} (Outside window/Weekend)", 'warning')
                    continue
                    
                is_collision = False
                if date in existing_entries:
                    # Check for holiday/disabled day first
                    if any(e['start'] == 'HOLIDAY' for e in existing_entries[date]):
                        self.logger.log(f"  🔴 Skipping {date} (Hari Libur/Disabled)", 'warning')
                        is_collision = True
                    else:
                        doc_start = normalize_time(entry['start_time'])
                        
                        for existing in existing_entries[date]:
                            if existing['start'] == doc_start:
                                self.logger.log(f"  ⊗ Skipping {date} [{doc_start}] (Time Collision)", 'warning')
                                is_collision = True
                                break
                        
                        if not is_collision:
                            self.logger.log(f"  ✓ Gap found on {date} at {doc_start}", 'success')
                
                if is_collision:
                    continue
                    
                entries_to_fill.append(entry)
                
            self.logger.log(f"✓ {len(entries_to_fill)} entries identified for filling.", 'success')

            if not entries_to_fill:
                self.logger.log("✅ Tidak ada yang perlu diisi! Gunakan mode paksa jika diperlukan.", 'success')
                mode = self.completion_mode.get()
                is_headless = (self.browser_mode.get() == 2)
                
                if is_headless and mode == 1:
                    self.logger.log("Mode Headless: Menutup browser otomatis.", 'info')
                    
                keep_open = (mode == 1 and not is_headless)
                self.finish_process(browser, keep_open=keep_open, close_app=(mode==3))
                return

            from form_filler import FormFiller
            filler = FormFiller(browser.page_app, self.logger)
            doc_url = self.config.get('last_doc_url', '')

            self.logger.log("📝 Switching to App tab...", 'info')
            time.sleep(1)
            if browser.page_app:
                browser.page_app.bring_to_front()

            for i, entry in enumerate(entries_to_fill):
                self.logger.log(f"▶ Entry {i+1}/{len(entries_to_fill)}: {entry['date']}", 'info')
                
                if not filler.open_form():
                    break
                
                if not filler.fill_entry(entry, doc_url):
                    break
                
                if filler.submit_form():
                    self.logger.log("✓ Entri Dikirim.", 'success')
                    time.sleep(1)  # Reduced from 3s
                else:
                    self.logger.log("❌ Pengiriman gagal. Menghentikan loop.", 'error')
                    break
            
            self.logger.log("=" * 60, 'info')
            self.logger.log("🎉 Fase 2 Selesai.", 'success')
            
            mode = self.completion_mode.get()
            is_headless = (self.browser_mode.get() == 2)
            
            # Logic: Always close browser if headless or if user Chose to close (mode != 1)
            should_keep_browser = (mode == 1 and not is_headless)
            should_close_app = (mode == 3)

            if is_headless and mode == 1:
                self.logger.log("Mode Headless: Mengabaikan opsi 'Biarkan browser terbuka'.", 'info')

            if should_keep_browser:
                self.logger.log("Browser dan aplikasi tetap terbuka.", 'info')
            elif should_close_app:
                self.logger.log("Menutup browser dan aplikasi...", 'info')
            else:
                self.logger.log("Menutup browser...", 'info')

            self.finish_process(browser, keep_open=should_keep_browser, close_app=should_close_app)
            
        except Exception as e:
            self.logger.log(f"❌ ERROR KRITIS: {str(e)}", 'error')
            import traceback
            self.logger.log(traceback.format_exc(), 'error')
            # Don't close on error
            self.logger.log("Proses dijeda karena error.", 'warning')

    def finish_process(self, browser, keep_open=False, close_app=False):
        if browser and not keep_open:
            browser.close_browser()
            
        if close_app:
            self.root.after(0, lambda: self.root.destroy())
        else:
            self.root.after(0, lambda: self.reset_ui())

    def reset_ui(self):
        self.start_btn.config(state='normal', text="▶  Mulai Otomatisasi", bg="#28a745")
        self.update_status("Siap | Proses selesai")
        self.logger.log("Proses selesai.", 'info')

if __name__ == "__main__":
    root = tk.Tk()
    app = DailyReporterApp(root)
    root.mainloop()

