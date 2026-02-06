from playwright.sync_api import Page
import time

class FormFiller:
    def __init__(self, page: Page, logger):
        self.page = page
        self.logger = logger

    def open_form(self):
        """Opens the 'Tambah Progress Harian' modal."""
        self.logger.log("Opening Form...")
        try:
            # Look for the green success button with the specific text
            self.page.wait_for_selector("button.btn-success:has-text('Tambah Progress Harian')", timeout=5000)
            self.page.click("button.btn-success:has-text('Tambah Progress Harian')")
            
            # Wait for modal to appear (It is actually an h5, so use class only)
            self.page.wait_for_selector(".modal-title:has-text('Tambah Progress Harian')", state='visible', timeout=5000)
            self.logger.log("✓ Form Modal Opened")
            return True
        except Exception as e:
            self.logger.log(f"❌ Failed to open form: {e}")
            return False

    def fill_entry(self, entry: dict, doc_url: str):
        """
        Fills the form with data from the parsed entry.
        entry: {
            'date': '2026-02-06',
            'start_time': '07:30',
            'end_time': '16:00',
            'activity': '...'
        }
        """
        self.logger.log(f"Filling entry for {entry.get('date')}...")
        
        try:
            # 1. Rencana Aksi - Skip (User instruction: Keep empty)
            
            # 2. Tanggal Kegiatan
            # Selector strategy: Find div with label "Tanggal Kegiatan" -> input[name="date"]
            date_selector = "//div[contains(@class, 'form-group')][.//label[contains(text(), 'Tanggal Kegiatan')]]//input[@name='date']"
            self._fill_date_time(date_selector, entry['date'], "Date")

            # 3. Jam Mulai
            start_selector = "//div[contains(@class, 'form-group')][.//label[contains(text(), 'Jam Mulai')]]//input[@name='date']"
            self._fill_date_time(start_selector, entry['start_time'], "Start Time")

            # 4. Jam Selesai
            end_selector = "//div[contains(@class, 'form-group')][.//label[contains(text(), 'Jam Selesai')]]//input[@name='date']"
            self._fill_date_time(end_selector, entry['end_time'], "End Time")

            # 5. Kegiatan Harian
            self.logger.log(f"Filling Activity: '{entry.get('activity', 'N/A')}'")
            self.page.fill('input[name="kegiatan"]', entry['activity'])

            # 6. Realisasi (Volume = 1, Satuan via config/default?)
            # Logic: User said "Fill left field with 1, keep right field blank"
            self.logger.log("Filling Realisasi (1)...")
            self.page.fill('input[name="realisasi_activity"]', "1")
            
            # 7. Bukti Dukung
            self.logger.log("Filling Proof URL...")
            self.page.fill('input[name="bukti_eviden"]', doc_url)

            self.logger.log("✓ Entry Filled")
            return True

        except Exception as e:
            self.logger.log(f"❌ Error filling form: {e}")
            return False
            
    def _fill_date_time(self, selector, value, label):
        """Helper to fill date/time inputs which are Vue/MX components."""
        try:
            # Attempt 1: Direct Fill + Enter
            self.page.fill(selector, value)
            self.page.press(selector, 'Enter')
            self.page.press(selector, 'Tab') # Trigger blur/change
            self.logger.log(f"  > Set {label}: {value}")
        except Exception as e:
            self.logger.log(f"  ⚠️ Error setting {label}: {e}")

    def submit_form(self):
        """Submits the form."""
        self.logger.log("Submitting form...")
        try:
            # Find the OK button in modal footer
            # Be careful not to click the 'Close' button or the 'OK' in the Error modal
            # The form modal should be the one currently active/visible.
            
            # We can target the specific modal footer
            footer_selector = "//div[contains(@class, 'modal-content')]//div[contains(@class, 'modal-footer')]//button[contains(@class, 'btn-primary') and text()='OK']"
            
            self.page.click(footer_selector)
            
            # Wait for modal to disappear or success message?
            # For now, just wait a bit
            time.sleep(2) 
            self.logger.log("✓ Submitted")
            return True
        except Exception as e:
            self.logger.log(f"❌ Error submitting: {e}")
            return False
