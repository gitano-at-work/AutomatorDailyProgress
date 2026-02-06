import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
from browser_controller import BrowserController
from utils import Logger, normalize_date
from doc_parser import parse_google_doc_text

CONFIG_FILE = 'config.json'

class DailyReporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Progress Reporter")
        self.root.geometry("550x650")
        self.root.resizable(False, False)

        self.config = self.load_config()

        # UI Variables
        self.doc_url_var = tk.StringVar(value=self.config.get('last_doc_url', ''))
        self.username_var = tk.StringVar(value=self.config.get('username', ''))
        self.password_var = tk.StringVar(value=self.config.get('password', ''))
        self.auth_code_var = tk.StringVar() # No config save for security/freshness
        self.keep_browser_var = tk.BooleanVar(value=self.config.get('keep_browser', False))

        self.create_widgets()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Warning: Failed to load config.json ({e}). Using defaults.")
                # Optional: Rename corrupt file?
        return {}

    def save_config(self):
        self.config['last_doc_url'] = self.doc_url_var.get()
        self.config['username'] = self.username_var.get()
        self.config['password'] = self.password_var.get()
        self.config['keep_browser'] = self.keep_browser_var.get()
        # Default URLs if not present
        if 'web_app_url' not in self.config:
            self.config['web_app_url'] = 'https://example.com/login'
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def create_widgets(self):
        # UI Styling (Basic ttk theme)
        import tkinter.ttk as ttk
        style = ttk.Style()
        style.theme_use('clam') # Usually cleaner on Windows than default
        
        # Main Container with Padding
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill='both', expand=True)

        # Header
        header = tk.Label(main_frame, text="Daily Progress Reporter", font=("Segoe UI", 16, "bold"), fg="#333")
        header.pack(pady=(0, 20))

        # --- Section 1: Configuration ---
        config_frame = ttk.LabelFrame(main_frame, text=" Configuration ", padding="15 10")
        config_frame.pack(fill='x', pady=5)

        # Doc URL
        ttk.Label(config_frame, text="Google Doc URL:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(config_frame, textvariable=self.doc_url_var, width=50).grid(row=0, column=1, padx=10, pady=5)

        # Username
        ttk.Label(config_frame, text="Username (NIP):").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(config_frame, textvariable=self.username_var, width=50).grid(row=1, column=1, padx=10, pady=5)

        # Password
        ttk.Label(config_frame, text="Password:").grid(row=2, column=0, sticky='w', pady=5)
        ttk.Entry(config_frame, textvariable=self.password_var, show="*", width=50).grid(row=2, column=1, padx=10, pady=5)

        # --- Section 2: Session Options ---
        options_frame = ttk.LabelFrame(main_frame, text=" Session Options ", padding="15 10")
        options_frame.pack(fill='x', pady=10)

        # Auth Code
        ttk.Label(options_frame, text="Auth Code (2FA):").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(options_frame, textvariable=self.auth_code_var, width=20).grid(row=0, column=1, sticky='w', padx=10, pady=5)
        ttk.Label(options_frame, text="(Optional - Auto-fills if provided)", font=("Segoe UI", 8, "italic"), foreground="gray").grid(row=0, column=2, sticky='w')

        # Keep Browser Checkbox
        ttk.Checkbutton(options_frame, text="Keep Browser Open after finish", variable=self.keep_browser_var).grid(row=1, column=0, columnspan=3, sticky='w', pady=5)

        # --- Action Buttons ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        self.start_btn = tk.Button(btn_frame, text="Start Automation", command=self.start_automation, 
                                bg="#28a745", fg="white", font=("Segoe UI", 10, "bold"), 
                                padx=20, pady=5, relief="flat")
        self.start_btn.pack()

        # --- Status Log ---
        log_frame = ttk.LabelFrame(main_frame, text=" Live Log ", padding="10")
        log_frame.pack(fill='both', expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, state='disabled', bg="#f8f9fa", font=("Consolas", 9), relief="flat")
        self.log_text.pack(fill='both', expand=True)

        self.logger = Logger(self.log_text)
        self.logger.log("Ready to start...")

    def start_automation(self):
        self.save_config()
        self.start_btn.config(state='disabled', text="Running...")
        
        # Run in a separate thread so GUI doesn't freeze
        thread = threading.Thread(target=self.run_process)
        thread.start()



    def run_process(self):
        try:
            self.logger.log("Initializing automation...")
            
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
                self.logger.log("❌ Failed to navigate to Kinerja dashboard.")
                self.finish_process(browser)
                return
            
            # Smart Calendar Navigation
            if not browser.navigate_to_calendar():
                self.logger.log("❌ Failed to reach Calendar page.")
                # fail softly? or prompt user?
                self.finish_process(browser)
                return
            
            # (Removed Calendar Dump per user request)
            
            # --- Phase 2: Parse Doc ---
            # --- New Logic: Tab Switching & Form Filling ---
            
            # 1. Wait a moment for rendering (reduced from 5s)
            self.logger.log("Waiting 1s on Calendar page...")
            import time
            time.sleep(1)
            
            # 2. Switch back to Doc tab to capture text
            self.logger.log("Switching to Google Doc tab...")
            if browser.page_doc:
                browser.page_doc.bring_to_front()
            # 3. Capture Text
            doc_text = browser.get_doc_text()
            if not doc_text:
                self.logger.log("❌ Failed to get document text.")
                # We stop here
                self.finish_process(browser)
                return

            # DUMP FOR DEBUG - User requested keeping Doc Dump
            with open("doc_dump.txt", "w", encoding="utf-8") as f:
                f.write(doc_text)
            self.logger.log("ℹ️  Saved raw doc text to 'doc_dump.txt'")

            # 4. Parse Entries
            entries = parse_google_doc_text(doc_text)
            self.logger.log(f"✓ Parsed {len(entries)} raw entries.")
            
            # Normalize
            valid_entries = []
            for entry in entries:
                norm_date = normalize_date(entry['date_raw'])
                if norm_date:
                    entry['date'] = norm_date
                    valid_entries.append(entry)

            if not valid_entries:
                self.logger.log("⚠️ No valid entries found.")
                # DUMP FOR DEBUG
                with open("doc_dump_fail.txt", "w", encoding="utf-8") as f:
                    f.write(doc_text)
                self.finish_process(browser)
                return

            self.logger.log(f"✓ {len(valid_entries)} entries ready to process.")
            
            # --- SMART FILLING LOGIC ---
            from calendar_scanner import CalendarScanner
            from utils import is_date_fillable
            
            scanner = CalendarScanner(browser.page_app, self.logger)
            existing_entries = scanner.get_existing_entries()
            self.logger.log(f"ℹ️ Found entries on {len(existing_entries)} dates.")

            # Filter Entries to Process
            entries_to_fill = []
            for entry in valid_entries:
                date = entry['date']
                
                # Check 1: Is it allowed? (Weekday + Window)
                if not is_date_fillable(date):
                    self.logger.log(f"  . Skipping {date} (Outside window or Weekend)")
                    continue
                    
                # Check 2: Is it already filled? (Collision Detection)
                # We need to check not just Date, but Date + Time Range
                is_collision = False
                
                if date in existing_entries:
                    # Check specifically for time collision
                    # Simplified logic: If Start Time matches, it's a collision.
                    # (Assuming no two valid activities start at same minute)
                    
                    entries_on_date = existing_entries[date] # List of dicts {'start':.., 'end':..}
                    
                    # Normalize doc time (0730 -> 07:30) for comparison
                    doc_start = entry['start_time']
                    if len(doc_start) == 4:
                        doc_start = f"{doc_start[:2]}:{doc_start[2:]}"
                    
                    for existing in entries_on_date:
                        # Existing is already HH:MM
                        if existing['start'] == doc_start:
                            self.logger.log(f"  . Skipping {date} [{doc_start}] (Time slot collision detected)")
                            is_collision = True
                            break
                    
                    if not is_collision:
                        self.logger.log(f"  > Valid Gap found on {date} at {doc_start}")
                
                if is_collision:
                    continue
                    
                entries_to_fill.append(entry)
                
            self.logger.log(f"✓ {len(entries_to_fill)} entries identified for filling.")

            if not entries_to_fill:
                self.logger.log("✅ Nothing to fill! Use force mode if needed (not implemented).")
                self.finish_process(browser, keep_open=self.keep_browser_var.get())
                return

            # 5. Form Filling (Dry Run)
            from form_filler import FormFiller
            filler = FormFiller(browser.page_app, self.logger)
            doc_url = self.config.get('last_doc_url', '')

            # Switch back to App for filling
            self.logger.log("Switching back to App tab...")
            time.sleep(1)
            if browser.page_app:
                browser.page_app.bring_to_front()

            # Process Filtered Entries
            for i, entry in enumerate(entries_to_fill):
                self.logger.log(f"--- Processing Entry {i+1}/{len(entries_to_fill)}: {entry['date']} ---")
                
                # Open Form
                if not filler.open_form():
                    break
                
                # Fill Form
                if not filler.fill_entry(entry, doc_url):
                    break
                
                # Submit Form
                if filler.submit_form():
                    self.logger.log("✓ Entry Submitted.")
                    # Optional: Wait regarding user request "check if entry appears"
                    # We rely on visual check or simply waiting for table refresh.
                    time.sleep(3) # Wait for table to update/modal to close fully
                else:
                    self.logger.log("❌ Submit failed. Stopping loop.")
                    break
                
                # Loop continues to next entry...
            # browser.close_browser() # Keep open

            # FUTURE STEPS (Calendar scanning, etc.)
            
            self.logger.log("Phase 2 Complete.")
            
            # Check Keep Open Preference
            if self.keep_browser_var.get():
                self.logger.log("Browser will remain open.")
                # self.finish_process(browser, keep_open=True) # Dont close
                self.root.after(0, lambda: self.reset_ui())
            else:
                self.logger.log("Closing browser...")
                self.finish_process(browser, keep_open=False)
            
        except Exception as e:
            self.logger.log(f"❌ CRITICAL ERROR: {str(e)}")
            # Don't close on error
            self.logger.log("Process paused due to error.")
            # In case of error we might want to keep browser open for debugging
            # but for now let's close to be safe or maybe leave it?
            # browser.close_browser() 

    def finish_process(self, browser, keep_open=False):
        if browser and not keep_open:
            browser.close_browser()
        self.root.after(0, lambda: self.reset_ui())

    def reset_ui(self):
        self.start_btn.config(state='normal', text="Start Automation")
        self.logger.log("Process finished.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DailyReporterApp(root)
    root.mainloop()
