import tkinter as tk
from datetime import datetime, timedelta

class Logger:
    def __init__(self, text_widget: tk.Text, log_file="daily_reporter.log"):
        self.text_widget = text_widget
        self.log_file = log_file

    def log(self, message: str, tag: str = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        # 1. Update GUI
        self.text_widget.configure(state='normal')
        # Insert with tag if provided, otherwise just insert
        if tag:
            self.text_widget.insert(tk.END, full_message, tag)
        else:
            self.text_widget.insert(tk.END, full_message)
            
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')
        
        # 2. Write to File
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")

        # 3. Console Output (Safe)
        try:
            print(full_message.strip())
        except UnicodeEncodeError:
            print(full_message.encode('ascii', 'ignore').decode('ascii').strip())

def normalize_date(date_str: str) -> str:
    """
    Convert various date formats to YYYY-MM-DD.
    Input examples:
        - "2 Februari 2026" (Indonesian)
        - "2026-02-02" (ISO)
    """
    import re
    # Indonesian month mapping
    indo_months = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
        # Short forms just in case (though not in PRD)
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 
        'agu': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'des': 12
    }
    
    text = date_str.lower().strip()
    
    # Try Indonesian format first: "2 Februari 2026"
    match = re.match(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', text)
    if match:
        day, month_name, year = match.groups()
        month = indo_months.get(month_name)
        if month:
            return f"{year}-{month:02d}-{int(day):02d}"
    
    # Try ISO format
    if re.match(r'\d{4}-\d{2}-\d{2}', text):
        return text
        
    return "" # Return empty if failed

def is_date_fillable(target_date_str: str) -> bool:
    """
    Checks if a date is valid for filling:
    1. Not Saturday or Sunday.
    2. Within the [Today - 3 days, Today] window.
    """
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Check Weekend (5 = Saturday, 6 = Sunday)
        if target_date.weekday() >= 5:
            return False
            
        # 2. Check Window (Today - 3 <= Target <= Today)
        start_window = today - timedelta(days=3)
        
        if start_window <= target_date <= today:
            return True
            
        return False
        
    except ValueError:
        return False
