from playwright.sync_api import Page
from datetime import datetime
from utils import Logger

class CalendarScanner:
    def __init__(self, page: Page, logger: Logger):
        self.page = page
        self.logger = logger

    def get_filled_dates(self) -> list:
        """
        Scans the generic Week View to find which dates have events.
        Returns a list of date strings ['2026-02-02', '2026-02-03'].
        """
        self.logger.log("Scanning calendar for existing entries...")
        filled_dates = []
        
        try:
            # 1. capture Headers to map Column Index -> Date
            # Selectors for Vue Cal headers usually: .vuecal__heading .weekday-label
            # Text format: "Senin 2", "Selasa 3"
            
            # Wait for any header to be visible
            self.page.wait_for_selector(".weekday-label", timeout=5000)
            
            headers = self.page.locator(".vuecal__heading .weekday-label").all_inner_texts()
            # headers = ['Senin 2', 'Selasa 3', ...]
            
            # 2. Capture Check Cells for Events
            # We look for cells in the main body.
            # Usually .vuecal__body .vuecal__cell
            # NOTE: There might be multiple rows? usually week view is 1 row of 7 columns.
            cells = self.page.locator(".vuecal__body .vuecal__cell").all()
            
            # We expect 7 headers and 7 cells (or multiple of 7 if month view, but user said week view)
            # Let's assume Week View for now.
            
            if len(headers) != len(cells):
                self.logger.log(f"⚠️ Mismatch: {len(headers)} headers vs {len(cells)} cells. Attempting to match first 7...")
            
            # Helper to parse "Senin 2" -> Date
            # We need the current month/year context. 
            # We can grab it from proper header or just assume from current config?
            # Safer: Grab the title "Minggu 6 (Februari 2026)"
            month_year_text = self.page.locator(".vuecal__title-bar .vuecal__title").inner_text()
            # "Minggu 6 (Februari 2026)" or "Februari 2026"
            
            current_month, current_year = self._parse_month_year(month_year_text)
            
            for i, header_text in enumerate(headers):
                if i >= len(cells): break
                
                # Parse day from "Senin 2"
                day_match = [s for s in header_text.split() if s.isdigit()]
                if not day_match:
                    continue
                day = int(day_match[0])
                
                # Construct Date String
                # Note: Handling month rollover (e.g. 30 Jan - 2 Feb) is tricky without full context.
                # But typically the header title reflects the majority? 
                # Or the headers might have full dates?
                # For MVP, let's assume the date is within the "Current Month" unless logical check fails?
                # Actually, if we use the day number, we can construct the date.
                
                date_str = f"{current_year}-{current_month:02d}-{day:02d}"
                
                # Check for events
                cell = cells[i]
                # Check if class contains 'has-events' OR checks for children
                # Snippet showed: class="vuecal__cell vuecal__cell--has-events"
                
                class_attr = cell.get_attribute("class") or ""
                has_events = "vuecal__cell--has-events" in class_attr
                
                # Double check with content look up (just in case class is flaky)
                if not has_events:
                    count = cell.locator(".vuecal__event").count()
                    if count > 0:
                        has_events = True
                
                if has_events:
                    self.logger.log(f"  > Found entry on {date_str} ({header_text.strip()})")
                    filled_dates.append(date_str)
                else:
                    self.logger.log(f"  . Empty slot: {date_str}")

        except Exception as e:
            self.logger.log(f"⚠️ Calendar scan failed: {e}")
            
        return filled_dates

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
        found_year = 2026 # Default
        
        for m_name, m_val in indo_months.items():
            if m_name in text:
                found_month = m_val
                break
        
        # Find year (4 digits)
        import re
        y_match = re.search(r'\d{4}', text)
        if y_match:
            found_year = int(y_match.group(0))
            
        # Fallback to current system date if fail?
        if found_month == 0:
            now = datetime.now()
            found_month = now.month
            
        return found_month, found_year
