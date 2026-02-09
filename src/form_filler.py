from playwright.sync_api import Page
import time

class FormFiller:
    def __init__(self, page: Page, logger):
        self.page = page
        self.logger = logger

    def open_form(self):
        """Opens the 'Tambah Progress Harian' modal."""
        self.logger.log("Membuka Form...")
        try:
            # Look for the green success button with the specific text
            self.page.wait_for_selector("button.btn-success:has-text('Tambah Progress Harian')", timeout=5000)
            self.page.click("button.btn-success:has-text('Tambah Progress Harian')")
            
            # Wait for modal to appear (It is actually an h5, so use class only)
            self.page.wait_for_selector(".modal-title:has-text('Tambah Progress Harian')", state='visible', timeout=5000)
            self.logger.log("✓ Modal Form Dibuka")
            return True
        except Exception as e:
            self.logger.log(f"❌ Gagal membuka form: {e}")
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
        self.logger.log(f"Mengisi entri untuk {entry.get('date')}...")
        
        try:
            # 1. Rencana Aksi
            action_plan = entry.get('action_plan', '')
            if action_plan:
                self.logger.log(f"Selecting Rencana Aksi: '{action_plan}'...")
                # Strategy: Click dropdown -> Wait for list -> Click item (Text or Index)
                
                # Dropdown trigger (Generic wrapper usually)
                dropdown_container = "//div[contains(@class, 'form-group')][.//label[contains(text(), 'Rencana Aksi')]]"
                
                # Click to open
                try:
                    self.page.click(f"{dropdown_container}//div[contains(@class, 'multiselect')]", timeout=2000)
                except:
                    self.page.click(f"{dropdown_container}//input")
                
                # Wait for options visibility
                self.page.wait_for_timeout(300) # Small buffer for animation

                try:
                    if action_plan.isdigit():
                        # INDEX BASED SELECTION (User Convention: "1" -> First Option)
                        idx = int(action_plan) - 1 # 0-based
                        self.logger.log(f"  > Memilih Opsi #{action_plan} (Indeks {idx})...")
                        
                        # Find all options. Usually .multiselect__element or li
                        # We use a broad logic: find the UL inside the container -> then LIs
                        # Or generic global LIs if the library renders them at root (common in Vue)
                        
                        # Attempt 1: Look inside the container (if semantic)
                        options = self.page.locator(f"{dropdown_container}//li")
                        if options.count() == 0:
                            # Attempt 2: Global multiselect open list (Vue-Multiselect style)
                            options = self.page.locator(".multiselect__content-wrapper .multiselect__element")
                        
                        if options.count() > idx:
                            options.nth(idx).click()
                            self.logger.log("  > Dipilih berdasarkan Indeks.")
                        else:
                            self.logger.log(f"  ⚠️ Indeks {idx} di luar batas (Ditemukan {options.count()} opsi).")
                            
                    else:
                        # TEXT BASED SELECTION
                        option_selector = f"li:has-text('{action_plan}')"
                        if self.page.is_visible(option_selector):
                            self.page.click(option_selector)
                            self.logger.log("  > Dipilih berdasarkan Teks.")
                        else:
                            self.page.locator(f"span:text('{action_plan}')").first.click()
                            self.logger.log("  > Dipilih via span match.")
                        
                except Exception as ex:
                    self.logger.log(f"  ⚠️ Tidak dapat memilih rencana: {ex}")
                    self.page.keyboard.press("Escape")
            else:
                self.logger.log("No Rencana Aksi specified in Doc. Skipping (Default).")
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
            self.logger.log(f"Mengisi Kegiatan: '{entry.get('category', 'N/A')}'")
            self.page.fill('input[name="kegiatan"]', entry['category'])

            # 6. Realisasi (Volume = 1, Satuan via config/default?)
            # Logic: User said "Fill left field with 1, keep right field blank"
            self.logger.log("Filling Realisasi (1)...")
            self.page.fill('input[name="realisasi_activity"]', "1")
            
            # 7. Bukti Dukung
            self.logger.log("Mengisi URL Bukti...")
            self.page.fill('input[name="bukti_eviden"]', doc_url)

            self.logger.log("✓ Entri Terisi")
            return True

        except Exception as e:
            self.logger.log(f"❌ Error mengisi form: {e}")
            return False
            
    def _fill_date_time(self, selector, value, label):
        """Helper to fill date/time inputs which are Vue/MX components."""
        try:
            # Format Time: 0730 -> 07:30
            if len(value) == 4 and value.isdigit():
                formatted_value = value[:2] + ":" + value[2:]
            else:
                formatted_value = value

            # Attempt: Click to focus, then Type (better for masked inputs)
            self.logger.log(f"  > Mengetik {label}: {formatted_value} ke {selector}...")
            
            # Ensure visible
            element = self.page.locator(selector).first
            if not element.is_visible():
                self.logger.log(f"  ⚠️ Field {label} tersembunyi/tidak ditemukan")
                return

            element.click()
            # Clear existing content first
            element.fill('') # Clears standard inputs
            # For robust clearing on some frameworks, we might need a small wait or keyboard action
            # But fill('') triggers 'input' event usually.
            # self.page.keyboard.press("Control+A")
            # self.page.keyboard.press("Backspace")
            
            # Clear field first, then type with faster delay
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Delete")
            self.page.keyboard.type(formatted_value, delay=30) 
            self.page.keyboard.press("Enter")
            self.page.keyboard.press("Tab") # Trigger blur
            
        except Exception as e:
            self.logger.log(f"  ⚠️ Error mengatur {label}: {e}")

    def submit_form(self):
        """Submits the form."""
        self.logger.log("Mengirim form...")
        try:
            # Find the OK button in modal footer
            # Logic: Valid OK button is usually 'btn-primary' and has text 'OK' and is VISIBLE
            
            # Selector for the specific OK button in the active modal
            # We use a broad but specific enough selector to catch the button even if nested
            submit_btn = self.page.locator("button.btn.btn-primary:has-text('OK'):visible")
            
            if submit_btn.count() > 0:
                submit_btn.first.click()
                self.logger.log("  > Klik OK.")
                
                # Wait for modal to close (smarter than fixed delay)
                try:
                    self.page.wait_for_selector(".modal[style*='display: none'], .modal:not(.show)", timeout=3000)
                except:
                    time.sleep(0.5)  # Fallback short wait
                return True
            else:
                self.logger.log("  ❌ Tidak dapat menemukan tombol SUBMIT (OK)!")
                # Fallback: Try generic footer selector
                try:
                    self.page.click("//div[contains(@class, 'modal-footer')]//button[contains(text(), 'OK')]")
                    self.logger.log("  > Klik OK (Fallback).")
                    return True
                except:
                    return False

        except Exception as e:
            self.logger.log(f"❌ Error mengirim: {e}")
            return False
