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

def normalize_time(time_str: str) -> str:
    """
    Normalize various time formats to HH:MM.
    Handles: 0730, 07:30, 07.30, 7:30, 730, etc.
    """
    import re
    t = time_str.strip().replace('.', ':')
    
    # Already HH:MM format
    match = re.match(r'^(\d{1,2}):(\d{2})$', t)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        return f"{h:02d}:{m:02d}"
    
    # Pure digits: 0730, 730, 1300, etc.
    digits = re.sub(r'\D', '', t)
    if len(digits) == 4:
        return f"{digits[:2]}:{digits[2:]}"
    elif len(digits) == 3:
        return f"0{digits[0]}:{digits[1:]}"
    
    return time_str  # Return as-is if unparseable

def normalize_date(date_str: str) -> str:
    """
    Convert various date formats to YYYY-MM-DD.
    Handles:
        - "2 Februari 2026" / "01 Januari 2026" (Indonesian)
        - "2 February 2026" / "1 Jan 2026" (English)
        - "2026-02-01" / "2026/02/01" (ISO)
        - "01/02/2026" / "1-2-2026" (DD/MM/YYYY)
        - "1 1 2026" (D M YYYY numeric)
    """
    import re
    
    # Month name mapping (Indonesian + English + abbreviations)
    month_map = {
        # Indonesian
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
        # Indonesian short
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7,
        'agu': 8, 'ags': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'des': 12,
        # English
        'january': 1, 'february': 2, 'march': 3, 'may': 5,
        'june': 6, 'july': 7, 'august': 8, 'october': 10,
        'december': 12,
        # English short
        'aug': 8, 'oct': 10, 'dec': 12,
    }
    
    text = date_str.lower().strip()
    
    # 1. Named month: "2 Februari 2026" or "2 February 2026" or "01 Jan 2026"
    match = re.match(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', text)
    if match:
        day, month_name, year = match.groups()
        month = month_map.get(month_name)
        if month:
            return f"{year}-{month:02d}-{int(day):02d}"
    
    # 2. ISO: "2026-02-01" or "2026/02/01"
    match = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', text)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    # 3. DD/MM/YYYY or DD-MM-YYYY: "01/02/2026" or "1-2-2026"
    match = re.match(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', text)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    # 4. Numeric with spaces: "1 1 2026"
    match = re.match(r'(\d{1,2})\s+(\d{1,2})\s+(\d{4})$', text)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
        
    return ""  # Return empty if all parsing failed

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
