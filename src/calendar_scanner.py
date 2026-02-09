from playwright.sync_api import Page
from datetime import datetime
from utils import Logger
import re
import time

class CalendarScanner:
    def __init__(self, page: Page, logger: Logger):
        self.page = page
        self.logger = logger

    def get_existing_entries(self, silent=False) -> dict:
        """
        Scans the generic Week View to find existing events with time ranges.
        Returns a dictionary mapping dates to list of time ranges:
        {
            '2026-02-06': [ {'start': '07:30', 'end': '13:00'}, ... ] 
        }
        """
        if not silent:
            self.logger.log("Memindai kalender untuk entri yang ada...")
        existing_data = {}
        
        try:
            # 1. capture Headers to map Column Index -> Date
            self.page.wait_for_selector(".weekday-label", timeout=5000)
            headers = self.page.locator(".vuecal__heading .weekday-label").all_inner_texts()
            
            # 2. Capture Check Cells for Events
            cells = self.page.locator(".vuecal__body .vuecal__cell").all()
            
            if len(headers) != len(cells):
                self.logger.log(f"⚠️ Mismatch: {len(headers)} headers vs {len(cells)} cells. Attempting to match first {min(len(headers), len(cells))}...")
            
            # Helper to parse "Senin 2" -> Date
            month_year_text = self.page.locator(".vuecal__title-bar .vuecal__title").inner_text()
            current_month, current_year = self._parse_month_year(month_year_text)
            
            for i, header_text in enumerate(headers):
                if i >= len(cells): break
                
                # Parse day from "Senin 2"
                day_match = [s for s in header_text.split() if s.isdigit()]
                if not day_match: continue
                day = int(day_match[0])
                
                # Construct Date String (ISO)
                date_str = f"{current_year}-{current_month:02d}-{day:02d}"
                
                # Check for events in this cell
                cell = cells[i]
                events = cell.locator(".vuecal__event").all()
                
                if not events:
                    self.logger.log(f"  . Slot kosong: {date_str}")
                    continue
                
                # Parse events
                self.logger.log(f"  > Ditemukan {len(events)} entri pada {date_str}")
                existing_data[date_str] = []
                
                for ev in events:
                    # Extract text content. Expecting format "07:30 - 13:00"
                    # Usually spans multiple lines. "Activity Title \n 07:30 - 13:00"
                    ev_text = ev.inner_text()
                    
                    # Regex for HH:MM - HH:MM
                    time_match = re.search(r'(\d{1,2}[:\.]\d{2})\s*-\s*(\d{1,2}[:\.]\d{2})', ev_text)
                    if time_match:
                        s_time = time_match.group(1).replace('.', ':') # normalize
                        e_time = time_match.group(2).replace('.', ':')
                        existing_data[date_str].append({'start': s_time, 'end': e_time})
                        self.logger.log(f"    - Ditemukan waktu: {s_time} - {e_time}")
                    else:
                        self.logger.log(f"    - Ditemukan event tapi tidak bisa parsing waktu: {ev_text[:20]}...")
                        # Assume full day checking? Or assume collision?
                        # Probably safest to mark simple presence if time fails
                        existing_data[date_str].append({'start': '?', 'end': '?'})

        except Exception as e:
            self.logger.log(f"⚠️ Pemindaian kalender gagal: {e}")
            
        return existing_data

    def scan_with_previous_week(self) -> dict:
        """
        Scans BOTH current week AND previous week for existing entries.
        This ensures Friday entries are detected when running on Monday.
        """
        self.logger.log("Memindai kalender (minggu ini + sebelumnya)...")
        existing = {}
        
        # 1. Scan current week first
        current_week_entries = self.get_existing_entries(silent=True)
        existing.update(current_week_entries)
        
        # 2. Navigate to previous week
        self.logger.log("⏪ Navigasi ke minggu sebelumnya...")
        try:
            prev_btn = self.page.locator("button.vuecal__arrow--prev")
            prev_btn.click()
            time.sleep(1)  # Reduced from 1.5s
            
            # 3. Scan previous week
            prev_week_entries = self.get_existing_entries(silent=True)
            existing.update(prev_week_entries)
            
            # 4. Return to current week (today)
            self.logger.log("⏩ Kembali ke minggu ini...")
            today_btn = self.page.locator("button.vuecal__today-btn")
            today_btn.click()
            time.sleep(1)  # Reduced from 1.5s
            
        except Exception as e:
            self.logger.log(f"⚠️ Gagal scan minggu sebelumnya: {e}")
        
        return existing

    def _parse_month_year(self, text):
        # text: "Minggu 6 (Februari 2026)" or "Februari 2026" or "Januari 2024"
        # Return (month_int, year_int)
        
        # Mapping
        indo_months = {
            'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
        }
        
        text = text.lower()
        found_month = 0
        found_year = datetime.now().year  # Use current year as default
        
        for m_name, m_val in indo_months.items():
            if m_name in text:
                found_month = m_val
                break
        
        # Find year (4 digits)
        y_match = re.search(r'\d{4}', text)
        if y_match:
            found_year = int(y_match.group(0))
            
        # Fallback to current system date if fail?
        if found_month == 0:
            now = datetime.now()
            found_month = now.month
            
        return found_month, found_year
