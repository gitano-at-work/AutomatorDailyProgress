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
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        self.config = self.load_config()

        # UI Variables
        self.doc_url_var = tk.StringVar(value=self.config.get('last_doc_url', ''))
        self.username_var = tk.StringVar(value=self.config.get('username', ''))
        self.password_var = tk.StringVar(value=self.config.get('password', ''))

        self.create_widgets()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_config(self):
        self.config['last_doc_url'] = self.doc_url_var.get()
        self.config['username'] = self.username_var.get()
        self.config['password'] = self.password_var.get()
        # Default URLs if not present
        if 'web_app_url' not in self.config:
            self.config['web_app_url'] = 'https://example.com/login'
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def create_widgets(self):
        # Header
        header = tk.Label(self.root, text="Daily Progress Reporter", font=("Helvetica", 16, "bold"))
        header.pack(pady=10)

        # Input Frame
        frame = tk.Frame(self.root)
        frame.pack(pady=5, padx=20, fill='x')

        # Doc URL
        tk.Label(frame, text="Google Doc URL (Current Month):").pack(anchor='w')
        tk.Entry(frame, textvariable=self.doc_url_var, width=50).pack(fill='x', pady=2)

        # Username
        tk.Label(frame, text="Username:").pack(anchor='w')
        tk.Entry(frame, textvariable=self.username_var, width=50).pack(fill='x', pady=2)

        # Password
        tk.Label(frame, text="Password:").pack(anchor='w')
        tk.Entry(frame, textvariable=self.password_var, show="*", width=50).pack(fill='x', pady=2)

        # Start Button
        self.start_btn = tk.Button(self.root, text="Start Automation", command=self.start_automation, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.start_btn.pack(pady=15, ipadx=10, ipady=5)

        # Status Log
        tk.Label(self.root, text="Status Log:").pack(anchor='w', padx=20)
        self.log_text = tk.Text(self.root, height=10, state='disabled', bg="#f0f0f0", font=("Consolas", 9))
        self.log_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))

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
            browser.login()
            
            # Post-Login Navigation
            if not browser.navigate_to_dashboard():
                self.logger.log("❌ Failed to navigate to Kinerja dashboard.")
                self.finish_process(browser)
                return
            
            # --- Phase 2: Parse Doc ---
            doc_text = browser.get_doc_text()
            if not doc_text:
                self.logger.log("❌ Failed to get document text or empty.")
                # We continue or stop? Let's stop to be safe for now
            else:
                entries = parse_google_doc_text(doc_text)
                self.logger.log(f"✓ Parsed {len(entries)} potential entries.")
                
                # Normalize dates strings
                valid_entries = []
                for entry in entries:
                    norm_date = normalize_date(entry['date_raw'])
                    if norm_date:
                        entry['date'] = norm_date
                        valid_entries.append(entry)
                    else:
                        self.logger.log(f"⚠️ Invalid date ignored: {entry['date_raw']}")
                
                self.logger.log(f"✓ {len(valid_entries)} entries with valid dates ready.")

            # FUTURE STEPS (Calendar scanning, etc.)
            
            self.logger.log("Phase 2 Complete. Browser will close in 5 seconds.")
            import time
            time.sleep(5)
            
            self.finish_process(browser)

        except Exception as e:
            self.logger.log(f"❌ CRITICAL ERROR: {str(e)}")
            # In case of error we might want to keep browser open for debugging
            # but for now let's close to be safe or maybe leave it?
            # browser.close_browser() 

    def finish_process(self, browser):
        if browser:
            browser.close_browser()
        self.root.after(0, lambda: self.reset_ui())

    def reset_ui(self):
        self.start_btn.config(state='normal', text="Start Automation")
        self.logger.log("Process finished.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DailyReporterApp(root)
    root.mainloop()
