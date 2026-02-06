
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import threading
from browser_controller import BrowserController
from utils import Logger, normalize_date
from doc_parser import parse_google_doc_text

CONFIG_FILE = 'config.json'
APP_VERSION = "1.0.0"

class DailyReporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Daily Progress Reporter v{APP_VERSION}")
        self.root.geometry("750x780")
        self.root.resizable(False, False)
        
        # Set app icon (if exists)
        try:
            self.root.iconbitmap('assets/app_icon.ico')
        except:
            pass

        self.config = self.load_config()
        self.setup_style()
        
        # UI Variables
        self.doc_url_var = tk.StringVar(value=self.config.get('last_doc_url', ''))
        self.username_var = tk.StringVar(value=self.config.get('username', ''))
        self.password_var = tk.StringVar(value=self.config.get('password', ''))
        self.auth_code_var = tk.StringVar()
        self.keep_browser_var = tk.BooleanVar(value=self.config.get('keep_browser', False))

        self.create_menu()
        self.create_widgets()
        
        # Status bar at bottom
        self.create_status_bar()

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
        main_frame = ttk.Frame(self.root, padding="20 20 20 10")
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
        except:
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

        # Doc URL with helper
        doc_frame = tk.Frame(config_frame, bg='white')
        doc_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(doc_frame, text="Link Google Doc:").pack(anchor='w')
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
        ttk.Label(config_frame, text="Username (NIP):").pack(anchor='w', pady=(10, 2))
        self.user_entry = ttk.Entry(config_frame, textvariable=self.username_var, font=('Segoe UI', 9))
        self.user_entry.pack(fill='x')

        # Password with show/hide toggle
        pwd_frame = tk.Frame(config_frame, bg='white')
        pwd_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(pwd_frame, text="Kata Sandi:").pack(anchor='w')
        
        pwd_inner = tk.Frame(pwd_frame, bg='white')
        pwd_inner.pack(fill='x')
        
        self.pwd_entry = ttk.Entry(pwd_inner, textvariable=self.password_var, 
                                    show="●", font=('Segoe UI', 9))
        self.pwd_entry.pack(side='left', fill='x', expand=True, pady=(2, 0))
        
        self.show_pwd_btn = tk.Button(pwd_inner, text="👁", font=('Segoe UI', 10),
                                      command=self.toggle_password, 
                                      relief='flat', bg='white', cursor='hand2')
        self.show_pwd_btn.pack(side='right', padx=(5, 0))

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
        
        ttk.Label(auth_entry_frame, text="Kode OTP:").pack(side='left')
        auth_entry = ttk.Entry(auth_entry_frame, textvariable=self.auth_code_var, 
                              width=15, font=('Segoe UI', 11))
        auth_entry.pack(side='left', padx=(10, 0))

        # Keep browser checkbox
        ttk.Checkbutton(options_frame, 
                       text="Biarkan browser terbuka setelah selesai", 
                       variable=self.keep_browser_var).pack(anchor='w', pady=(10, 0))

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
        
        # Initial Check
        self.root.after(500, self.check_initial_state)

    def check_initial_state(self):
        """Check if browser is installed and set UI mode."""
        # Create a temp controller just to check
        temp_browser = BrowserController(self.logger, self.config)
        if temp_browser.is_browser_installed():
            self.set_ready_mode()
            self.logger.log("✓ Siap memulai otomatisasi", 'success')
        else:
            self.set_download_mode()
            self.logger.log("⚠️ Browser belum terinstall. Silakan unduh terlebih dahulu.", 'warning')

        self.status_label.pack(side='left')
        
        # Version info
        ttk.Label(status_frame, text=f"v{APP_VERSION}", font=("Segoe UI", 8)).pack(side='right')

    def toggle_inputs(self, state):
        """Enable or disable input fields."""
        # state is 'normal' or 'disabled'
        try:
            self.doc_entry.config(state=state)
            self.user_entry.config(state=state)
            self.pwd_entry.config(state=state)
            self.show_pwd_btn.config(state=state)
            # Template link is a label, no easy disable but it's harmless
        except:
            pass # In case called before widgets init

    def set_download_mode(self):
        """Disable inputs, set button to Download."""
        self.toggle_inputs('disabled') # Gray out inputs
        
        self.start_btn.config(
            text="⬇ Unduh Browser Otomatis", 
            command=self.start_download,
            bg='#ff9800' # Orange for attention
        )
        self.update_status("Diperlukan instalasi browser")

    def set_ready_mode(self):
        """Enable inputs, set button to Start."""
        self.toggle_inputs('normal') # Enable inputs
        
        self.start_btn.config(
            text="🚀 Mulai Otomatisasi", 
            command=self.start_automation,
            bg='#4CAF50'
        )
        self.update_status("Siap")

    def start_download(self):
        """Start download thread."""
        self.start_btn.config(state='disabled', text="⏳ Mengunduh...", bg='#6c757d')
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        browser = BrowserController(self.logger, self.config)
        self.logger.log("⬇️ Memulai unduhan... (Sekitar 400MB)", 'info')
        self.logger.log("   Mohon tunggu, tergantung kecepatan internet Anda. Proses ini hanya dilakukan sekali saja, setelah install tidak perlu menunggu lagi", 'info')
        
        try:
            # Custom ASCII Progress Bar Logic
            # Since real parsing is hard, we simulate a 'beat' bar based on output activity
            # Or assume roughly 10 steps if we can guess.
            # Simple approach: Just print/update a bar line for every chunk of output.
            
            progress = 0
            
            for line in browser.install_browser():
                # Try to detect percentage in line (e.g. "34%")
                import re
                match = re.search(r'(\d+)%', line)
                if match:
                    try:
                        pct = int(match.group(1))
                        progress = pct
                    except: 
                        pass
                else:
                    # If no percentage, just increment slowly to show activity
                    progress = (progress + 5) % 100
                
                # Render ASCII Bar: |==========          | 50%
                bar_len = 30
                filled = int(bar_len * progress / 100)
                bar = "|" + "=" * filled + " " * (bar_len - filled) + "|"
                
                # We log this as a status update
                # Since Logger appends, we can't replace lines easily. 
                # So we ONLY log the bar if it changes significantly or just the status line.
                # Actually, appending many bars is spammy. 
                # Let's just log key updates or a compact bar.
                if '%' in line:
                    self.logger.log(f"{bar} {progress}%")
                else:
                    # For non-percentage lines (like "Downloading..."), just log the text
                    self.logger.log(f"   {line}")
                
            self.logger.log("|" + "=" * 30 + "| 100%")
            self.logger.log("✅ Unduhan & Instalasi Selesai! Tutup aplikasi ini lalu buka lagi", 'success')
            self.root.after(0, self.set_ready_mode)
        except Exception as e:
            self.logger.log(f"❌ Gagal mengunduh: {e}", 'error')
            self.root.after(0, lambda: self.start_btn.config(state='normal', text="⬇ Coba Lagi"))

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
        self.logger.log("Log cleared.", 'info')

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
        self.config['keep_browser'] = self.keep_browser_var.get()
        
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

        
        self.save_config()
        self.start_btn.config(state='disabled', text="⏳ Sedang Berjalan...", bg='#6c757d')
        self.update_status("Otomatisasi sedang berjalan...")
        self.logger.log("=" * 60, 'info')
        
        thread = threading.Thread(target=self.run_process)
        thread.start()

    def run_process(self):
        try:
            self.logger.log("🚀 Initializing automation...", 'info')
            
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
                self.logger.log("❌ Failed to navigate to Kinerja dashboard.", 'error')
                self.finish_process(browser)
                return
            
            # Smart Calendar Navigation
            if not browser.navigate_to_calendar():
                self.logger.log("❌ Failed to reach Calendar page.", 'error')
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
                self.logger.log("❌ Failed to get document text.", 'error')
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
            existing_entries = scanner.get_existing_entries()
            self.logger.log(f"ℹ️ Found entries on {len(existing_entries)} dates.", 'info')

            entries_to_fill = []
            for entry in valid_entries:
                date = entry['date']
                
                if not is_date_fillable(date):
                    self.logger.log(f"  ⊗ Skipping {date} (Outside window/Weekend)", 'warning')
                    continue
                    
                is_collision = False
                if date in existing_entries:
                    doc_start = entry['start_time']
                    if len(doc_start) == 4:
                        doc_start = f"{doc_start[:2]}:{doc_start[2:]}"
                    
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
                self.logger.log("✅ Nothing to fill! Use force mode if needed.", 'success')
                self.finish_process(browser, keep_open=self.keep_browser_var.get())
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
                    self.logger.log("✓ Entry Submitted.", 'success')
                    time.sleep(3)
                else:
                    self.logger.log("❌ Submit failed. Stopping loop.", 'error')
                    break
            
            self.logger.log("=" * 60, 'info')
            self.logger.log("🎉 Phase 2 Complete.", 'success')
            
            if self.keep_browser_var.get():
                self.logger.log("Browser will remain open.", 'info')
                self.root.after(0, lambda: self.reset_ui())
            else:
                self.logger.log("Closing browser...", 'info')
                self.finish_process(browser, keep_open=False)
            
        except Exception as e:
            self.logger.log(f"❌ CRITICAL ERROR: {str(e)}", 'error')
            import traceback
            self.logger.log(traceback.format_exc(), 'error')
            # Don't close on error
            self.logger.log("Process paused due to error.", 'warning')

    def finish_process(self, browser, keep_open=False):
        if browser and not keep_open:
            browser.close_browser()
        self.root.after(0, lambda: self.reset_ui())

    def reset_ui(self):
        self.start_btn.config(state='normal', text="▶  Start Automation", bg="#28a745")
        self.update_status("Ready | Process finished")
        self.logger.log("Process finished.", 'info')

if __name__ == "__main__":
    root = tk.Tk()
    app = DailyReporterApp(root)
    root.mainloop()

