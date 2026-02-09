from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import time
import os
import sys

class BrowserController:
    def __init__(self, logger, config: dict):
        self.logger = logger
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page_doc = None  # Tab for Google Doc
        self.page_app = None  # Tab for Web App
        
        # CRITICAL: Force Playwright to use a persistent local folder for browsers.
        # This ensures both the "install" command and the "launch" command look in the same place.
        # We use a folder "browsers" next to the config (or executable).
        
        if getattr(sys, 'frozen', False):
             # If frozen (exe), use the folder where the exe is located
             base_path = os.path.dirname(sys.executable)
        else:
             # If script, use current working directory
             base_path = os.getcwd()
             
        self.browsers_path = os.path.join(base_path, 'browsers')
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.browsers_path
        
        # Ensure path exists
        if not os.path.exists(self.browsers_path):
            try:
                os.makedirs(self.browsers_path, exist_ok=True)
            except Exception:
                pass # Fail silently, let playwright handle logic if path weak

    def is_browser_installed(self):
        """Checks if the browser looks installed in the local folder."""
        import os
        if not os.path.exists(self.browsers_path):
            return False
        # Check for any subdirectories (playwright installs like 'chromium-1234')
        try:
            items = os.listdir(self.browsers_path)
            for item in items:
                if os.path.isdir(os.path.join(self.browsers_path, item)):
                    return True
        except Exception:
            return False
        return False

    def install_browser(self):
        """
        Generator that installs the browser and yields progress output.
        Usage: for line in browser.install_browser(): log(line)
        """
        import subprocess
        import os
        from playwright._impl._driver import compute_driver_executable
        
        driver_exec = compute_driver_executable()
        install_cmd = []
        
        if isinstance(driver_exec, tuple):
            install_cmd.extend(list(driver_exec))
        else:
            install_cmd.append(str(driver_exec))
            
        install_cmd.extend(["install", "chromium"])
        
        creationflags = 0x08000000 if os.name == 'nt' else 0
        env = os.environ.copy()
        
        process = subprocess.Popen(
            install_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            creationflags=creationflags,
            env=env,
            text=True
        )
        
        for line in process.stdout:
            yield line.strip()
            
        process.wait()
        if process.returncode != 0:
            raise Exception(f"Install failed with code {process.returncode}")

    def launch_browser(self, retry=True):
        """Launches the browser and opens two tabs."""
        try:
            self.playwright = sync_playwright().start()
            headless = self.config.get('browser_headless', False)
            self.logger.log(f"Membuka browser (Headless: {headless})...")
            
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context()
            
            # Open Tab 1: Web App
            self.page_app = self.context.new_page()
            self.logger.log("Membuka Tab 1: Web App (ASN/SSO)")
            
            # Open Tab 2: Google Doc
            self.page_doc = self.context.new_page()
            self.logger.log("Membuka Tab 2: Google Doc")
            
            return True
        except Exception as e:
            error_msg = str(e)
            if "Executable doesn't exist" in error_msg or "browsers" in error_msg:
                self.logger.log("❌ Browser tidak ditemukan! Silakan klik 'Unduh Browser Otomatis'.")
                return False
            else:
                self.logger.log(f"❌ Gagal membuka browser: {error_msg}")
                return False

    def close_browser(self):
        """Closes the browser and cleanup."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.logger.log("Browser ditutup.")

    def navigate_to_doc(self, url: str):
        """Navigates the doc tab to the Google Doc URL."""
        if not self.page_doc:
            return
            
        self.logger.log(f"Membuka Google Doc...")
        
        # Retry loop for unstable connection
        for attempt in range(3):
            try:
                self.logger.log(f"Memuat Doc (Percobaan {attempt+1}/3)...")
                # Using a very long timeout (3 mins)
                self.page_doc.goto(url, timeout=180000, wait_until='domcontentloaded')
                self.logger.log("✓ Google Doc dimuat (DOM Siap)")
                return
            except Exception as e:
                self.logger.log(f"⚠️ Error memuat Doc (Percobaan {attempt+1}): {str(e)}")
                time.sleep(5) # Wait before retry
        
        self.logger.log("❌ Gagal memuat Google Doc setelah 3 percobaan")

    def login(self, auth_code=None):
        """Handles the login flow on the web app tab."""
        if not self.page_app:
            return
            
        login_url = self.config.get('web_app_url')
        username = self.config.get('username')
        password = self.config.get('password')
        
        self.logger.log(f"Membuka Halaman Login: {login_url}")
        try:
            self.page_app.bring_to_front()
            self.page_app.goto(login_url)
            
            # Identify selectors (using loose selectors as per PRD placeholders)
            # In a real scenario, we'd need exact selectors. 
            # I'll use some generic ones or best guesses based on common patterns 
            # and allow the user to easily update them.
            
            # Using specific selectors if provided in PRD appendix, else generic
            # "Input details here..." was in PRD, so I'll try to find common ones.
            # Assuming: input[name="username"], input[name="password"]
            
            self.logger.log("Mencoba mengisi kredensial...")
            
            # 1. Open Login Modal on Landing Page
            self.logger.log("Mencoba membuka modal login...")
            # 1. Expand Main Menu
            # Logic: Check if "Majalah Digital BKN" (bottom menu item) is visible.
            # If so, menu is expanded. If not, hover/click '#start'.
            majalah_selector = "span:has-text('Majalah Digital BKN')"
            
            try:
                if self.page_app.is_visible(majalah_selector):
                    self.logger.log("Menu sudah terbuka.")
                else:
                    self.logger.log("Mengarahkan kursor ke menu utama untuk membuka...")
                    self.page_app.hover('#start')
                    # Wait for expansion (Majalah button to appear)
                    try:
                        self.page_app.wait_for_selector(majalah_selector, state='visible', timeout=2000)
                        self.logger.log("✓ Menu terbuka (Majalah terdeteksi)")
                    except:
                        self.logger.log("⚠️ Animasi pembukaan menu timeout. Mencoba klik...")
                        self.page_app.click('#start')
                        time.sleep(1)

                # Now try clicking the button
                if self.page_app.is_visible('#btn-layanan-public'):
                    self.page_app.click('#btn-layanan-public', force=True)
                elif self.page_app.is_visible('#btn-layanan-login-mobile'):
                    self.page_app.click('#btn-layanan-login-mobile', force=True)
                else:
                    self.logger.log("Mencoba klik fallback untuk menu Login...")
                    # Fallback: force click specific text
                    self.page_app.click('text=Login', force=True)
                    
            except Exception as e:
                self.logger.log(f"⚠️ Pembukaan/klik awal gagal: {e}")

            # 2. Click 'Masuk' in Modal to redirect to SSO
            self.logger.log("Menunggu tombol 'Masuk'...")
            try:
                self.page_app.wait_for_selector('#btn-login', state='visible', timeout=3000)
                self.page_app.click('#btn-login')
            except Exception as e:
                self.logger.log(f"⚠️ Error mengklik Masuk: {e}")

            # 3. Wait for SSO Page Redirection
            self.logger.log("Menunggu halaman SSO...")
            try:
                self.page_app.wait_for_url('**/sso-siasn.bkn.go.id/**', timeout=20000)
                self.logger.log("✓ Dialihkan ke SSO")
            except Exception as e:
                self.logger.log(f"⚠️ Pengalihan timeout atau gagal: {e}")
            
            # 4. Fill SSO Credentials
            if username and password:
                self.logger.log("Mengisi kredensial SSO...")
                try:
                    self.page_app.wait_for_selector('input[name="username"]', state='visible', timeout=10000)
                    self.page_app.fill('input[name="username"]', username)
                    self.page_app.fill('input[name="password"]', password)
                    
                    # 5. Submit SSO Form
                    self.logger.log("Mengirim form SSO...")
                    
                    if self.page_app.is_visible('button[type="submit"]'):
                        self.page_app.click('button[type="submit"]')
                    elif self.page_app.is_visible('#kc-login'):
                        self.page_app.click('#kc-login')
                    else:
                        self.page_app.press('input[name="password"]', 'Enter')
                    
                    self.logger.log("✓ Kredensial dikirim")
                    
                    # --- AUTO-FILL 2FA (Experimental) ---
                    if auth_code and auth_code.strip():
                        self.logger.log(f"⏳ Mencoba Auto-2FA dengan kode: {auth_code}")
                        try:
                            otp_selector = 'input[name="otp"], input[id="otp"], input[id="totp"]'
                            self.page_app.wait_for_selector(otp_selector, state='visible', timeout=5000)
                            
                            self.page_app.fill(otp_selector, auth_code)
                            self.logger.log("  > Kode OTP Terisi.")
                            
                            if self.page_app.is_visible('#kc-login'):
                                self.page_app.click('#kc-login')
                            elif self.page_app.is_visible('button[type="submit"]'):
                                self.page_app.click('button[type="submit"]')
                            
                            self.logger.log("  > OTP Dikirim. Menyerahkan ke validasi...")
                        except Exception as e:
                            self.logger.log(f"⚠️ Auto-2FA gagal (Field tidak ditemukan/Error): {e}")
                    
                except Exception as e:
                    self.logger.log(f"⚠️ Error mengisi/mengirim SSO: {e}")
            else:
                self.logger.log("ℹ️ Kredensial tidak diberikan. Silakan login manual.")
                
            # 2FA Pause Logic (Handles validation of success for both Manual and Auto)
            self.handler_2fa()

        except Exception as e:
            self.logger.log(f"❌ Error spesifik login: {str(e)}")
            return # Stop if critical failure

    def navigate_to_dashboard(self):
        """
        Navigates to the Kinerja/SKP page from ASN Digital portal.
        Flow:
        1. Hover on BKN logo (#start) to reveal menu buttons
        2. Wait for "Majalah Digital BKN" to appear (menu expanded)
        3. Click "Layanan Individu ASN" (#btn-layanan-individu)  
        4. Click "Kinerja" in the submenu
        5. On Kinerja page, find current year SKP and click Penilaian
        """
        if not self.page_app:
            return False
            
        max_retries = 3
        
        try:
            for attempt in range(max_retries):
                try:
                    self.logger.log("Membuka Dashboard Kinerja...")
                    
                    # Wait for page to stabilize after login
                    time.sleep(2)
                    
                    current_url = self.page_app.url
                    self.logger.log(f"URL Saat Ini: {current_url}")
                    
                    # Check if we're on ASN Digital portal (need to navigate to Kinerja)
                    if 'asndigital.bkn.go.id' in current_url and '/skp' not in current_url:
                        # Step 1: Hover on BKN logo to reveal menu
                        self.logger.log("Mengarahkan kursor ke logo BKN untuk membuka menu...")
                        
                        # Wait for the start button to be visible
                        start_btn = self.page_app.locator("#start")
                        start_btn.wait_for(state='visible', timeout=10000)
                        
                        # Hover to reveal menu
                        start_btn.hover()
                        time.sleep(1)
                        
                        # Step 2: Wait for menu to expand (detected by Majalah Digital BKN appearing)
                        majalah_selector = "span:has-text('Majalah Digital BKN'), #book-icon"
                        try:
                            self.page_app.wait_for_selector(majalah_selector, state='visible', timeout=5000)
                            self.logger.log("✓ Menu terbuka")
                        except Exception:
                            # Try clicking the start button if hover doesn't work
                            self.logger.log("⚠️ Menu tidak terbuka dengan hover, mencoba klik...")
                            start_btn.click()
                            time.sleep(1)
                        
                        # Step 3: Click "Layanan Individu ASN"
                        self.logger.log("Mengklik 'Layanan Individu ASN'...")
                        layanan_individu_btn = self.page_app.locator("#btn-layanan-individu")
                        layanan_individu_btn.wait_for(state='visible', timeout=10000)
                        layanan_individu_btn.click()
                        time.sleep(2)
                        
                        # Step 4: Wait for navbar/submenu to appear and click Kinerja
                        self.logger.log("Menunggu submenu muncul...")
                        
                        # Wait a moment for the navbar to become visible
                        time.sleep(2)
                        
                        # Look for Kinerja link in the menu (should now be visible)
                        self.logger.log("Mencari link 'Kinerja'...")
                        kinerja_link = self.page_app.locator("#menu-individu a:has-text('Kinerja')").first
                        
                        # Wait for link to be visible
                        kinerja_link.wait_for(state='visible', timeout=10000)
                        
                        self.logger.log("Mengklik 'Kinerja'...")
                        kinerja_link.click()
                        
                        # Wait for navigation to complete
                        time.sleep(3)
                        self.page_app.wait_for_load_state('networkidle', timeout=30000)
                        
                        self.logger.log(f"✓ Navigasi ke Kinerja berhasil")
                        self.logger.log(f"URL Saat Ini: {self.page_app.url}")
                    
                    # Now we should be on kinerja.bkn.go.id - check if we need to go to SKP/Penilaian
                    current_url = self.page_app.url
                    
                    if 'kinerja.bkn.go.id' in current_url:
                        # Wait for page to load
                        self.page_app.wait_for_load_state('networkidle', timeout=15000)
                        time.sleep(2)
                        
                        # Look for SKP page elements - find current year's SKP and click Penilaian
                        import datetime
                        current_year = str(datetime.datetime.now().year)
                        self.logger.log(f"Mencari SKP untuk tahun {current_year}...")
                        
                        # Check if we're on SKP list or need to navigate there
                        if '/skp' not in current_url:
                            # Try to navigate to SKP via sidebar
                            skp_link = self.page_app.locator("a.sidebar-link[href='/skp'], a[href='/skp']")
                            if skp_link.count() > 0 and skp_link.first.is_visible():
                                self.logger.log("Mengklik menu SKP di sidebar...")
                                skp_link.first.click()
                                self.page_app.wait_for_load_state('networkidle', timeout=10000)
                                time.sleep(2)
                        
                        # Now find and click Penilaian for current year
                        year_badge = self.page_app.locator(f".badge:has-text('{current_year}')")
                        
                        if year_badge.count() > 0:
                            self.logger.log(f"✓ Ditemukan {year_badge.count()} periode SKP untuk {current_year}")
                            
                            penilaian_btns = self.page_app.locator("a:has-text('Penilaian')")
                            
                            if penilaian_btns.count() > 0:
                                self.logger.log("Mengklik tombol 'Penilaian'...")
                                penilaian_btns.first.click()
                                self.page_app.wait_for_load_state('networkidle', timeout=15000)
                                time.sleep(2)
                                
                                self.logger.log("✓ Tiba di Halaman Penilaian")
                                self.logger.log(f"URL Saat Ini: {self.page_app.url}")
                                return True
                            else:
                                self.logger.log("⚠️ Tombol 'Penilaian' tidak ditemukan")
                        else:
                            # Fallback: click any Penilaian button
                            penilaian_btn = self.page_app.locator("a:has-text('Penilaian')").first
                            if penilaian_btn.is_visible():
                                self.logger.log("Mengklik tombol 'Penilaian' (fallback)...")
                                penilaian_btn.click()
                                self.page_app.wait_for_load_state('networkidle', timeout=15000)
                                time.sleep(2)
                                self.logger.log("✓ Tiba di Halaman Penilaian")
                                return True
                    
                    # Check if we're already on the right page
                    if '/penilaian' in self.page_app.url or '/skp' in self.page_app.url:
                        self.logger.log("✓ Sudah berada di halaman yang benar")
                        return True
                    
                    raise Exception("Tidak dapat menyelesaikan navigasi ke halaman Kinerja/Penilaian")
                
                except Exception as e:
                    self.logger.log(f"⚠️ Percobaan navigasi {attempt+1}/{max_retries} gagal: {str(e)}")
                    if attempt < max_retries - 1:
                        self.logger.log("Mencoba lagi dalam 5 detik...")
                        time.sleep(5)
                        # Reload page to reset state
                        self.page_app.reload()
                        self.page_app.wait_for_load_state('networkidle', timeout=10000)
                    else:
                        self.logger.log("❌ Semua percobaan navigasi gagal.")
                        return False
        except Exception as e:
            self.logger.log(f"❌ Error Navigasi Kritis: {e}")
            return False

    def navigate_to_calendar(self):
        """
        Navigates to the actual daily reporting calendar page.
        Handles dynamic redirects:
        1. Direct to Calendar (Ideal)
        2. Redirect to SKP List -> Click Penilaian -> Click Progress Harian
        """
        if not self.page_app:
            return False
            
        self.logger.log("Memverifikasi akses Halaman Kalender...")
        time.sleep(3) # Let redirects settle
        
        current_url = self.page_app.url
        
        # Helper to detect current Year and Quarter
        import datetime
        now = datetime.datetime.now()
        current_year = str(now.year)
        # Determine Triwulan (Quarter)
        month = now.month
        if 1 <= month <= 3: qtr = "TRIWULAN I"
        elif 4 <= month <= 6: qtr = "TRIWULAN II"
        elif 7 <= month <= 9: qtr = "TRIWULAN III"
        else: qtr = "TRIWULAN IV"
        
        self.logger.log(f"Periode Target: Tahun {current_year}, {qtr}")

        # CASE 2: Redirected to SKP List (URL contains '/skp' but not '/penilaian'?)
        # Or simply check for specific elements on the page
        
        # If we see "Daftar Sasaran Kinerja Pegawai" or similar headers
        is_skp_page = False
        try:
            if "skp" in current_url and "penilaian" not in current_url:
                is_skp_page = True
            elif self.page_app.is_visible("text=Daftar SKP") or self.page_app.is_visible("text=Daftar Sasaran Kinerja Pegawai"):
                is_skp_page = True
        except: pass
        
        if is_skp_page:
            self.logger.log("⚠️ Dialihkan ke Daftar SKP. Navigasi manual...")
            try:
                # 1. Find Row with Current Year (e.g., "1 Januari 2026")
                # We look for a row that has the year. Current hypothesis: text=2026
                # And click "Penilaian" button in that container.
                
                # We'll use a locator that finds the row containing the year, then the assessment button
                # This is tricky without exact HTML, but trying text based chaining.
                
                self.logger.log(f"Mencari SKP aktif untuk {current_year}...")
                
                # Fallback strategy: Just click the first 'Penilaian' button? 
                # User said "find the most latest". Usually the top one or bottom one.
                # Let's try to find text "31 Desember 2026" or similar.
                
                # Using Playwright's layout selectors: 
                # Click 'Penilaian' right-of '2026' or similar?
                # Let's try strict text first.
                
                # Assumption: Button text is "Penilaian"
                # We want the Penilaian button that is associated with current year.
                
                # Strategy: Get all 'Penilaian' buttons, check which one is near the year?
                # Simpler: Click the text "Penilaian" that is visible.
                # If there are multiple, usually the active one is what we want.
                
                # BETTER: Use a specific selector if possible. 
                # For MVP, let's try to click the FIRST "Penilaian" button visible, 
                # assuming the latest is usually at top.
                # User said: "taking the Periode value and find the most current range"
                
                self.logger.log("Mengklik 'Penilaian' untuk periode aktif...")
                # We interpret "Penilaian" button.
                # Using specific class from user image visual (blue outline button usually)
                # Text is likely "Penilaian" or "Penilaian SKP"
                
                # Try to locate the button that contains text "Penilaian" inside the list
                self.page_app.click("a:has-text('Penilaian'), button:has-text('Penilaian')", force=True)
                
                self.page_app.wait_for_load_state('networkidle')
                self.logger.log("✓ Masuk ke Halaman Penilaian")
                
            except Exception as e:
                self.logger.log(f"❌ Gagal mengklik Penilaian: {e}")
                return False

        # CASE 2b: Now we are likely on Penilaian Page (or were already there)
        # URL likely contains '/penilaian'
        # We need to find "TRIWULAN I" (current) and click "Progress Harian"
        
        try:
            # Check if we are on assessment page
            if "penilaian" in self.page_app.url or self.page_app.is_visible("text=Pelaksanaan Kinerja"):
                
                # STABILITY CHECK: Wait for the Quarter header to be visible
                self.logger.log(f"Menunggu bagian '{qtr}' dimuat...")
                try:
                    self.page_app.wait_for_selector(f"text={qtr}", timeout=10000)
                    time.sleep(2) # Extra stability buffer as requested
                except:
                    self.logger.log("⚠️ Teks kuartal tidak langsung ditemukan, melanjutkan...")

                self.logger.log(f"Mencari tombol 'Progress Harian' untuk {qtr}...")
                
                # Attempt to click specifically associated with the Quarter
                # Using a broad locator that filters by text
                # We expect the button to be visible.
                
                # Attempt 1: XPath (Sibling/Container)
                xpath_selector = f"//tr[.//b[contains(text(), '{qtr}')]]/following-sibling::tr[1]//a[contains(., 'Progress Harian')]"
                
                clicked = False
                if self.page_app.is_visible(xpath_selector):
                    self.logger.log("Mengklik via XPath...")
                    self.page_app.click(xpath_selector)
                    clicked = True
                else:
                    self.logger.log("Selektor XPath tidak terlihat atau tidak valid. Mencoba selektor sederhana...")
                    # Attempt 2: Locator based on text "Progress Harian"
                    # We grab all of them, and if there's more than one, we might need logic.
                    # But usually the TOP one is the active one (Triwulan I).
                    
                    btn = self.page_app.locator("a", has_text="Progress Harian").first
                    if btn.is_visible():
                        self.logger.log("Ditemukan tombol 'Progress Harian' (Generik). Mengklik...")
                        btn.click()
                        clicked = True
                    else:
                        # Attempt 3: Button tag?
                        btn2 = self.page_app.locator("button", has_text="Progress Harian").first
                        if btn2.is_visible():
                            btn2.click()
                            clicked = True
                
                if clicked:
                    # Wait for navigation explicitly
                    self.logger.log("Menunggu navigasi ke Kalender...")
                    try:
                        self.page_app.wait_for_url("**/kinerja_harian/**", timeout=15000)
                    except:
                        self.logger.log("⚠️ URL tidak berubah dengan cepat. Memeriksa manual...")
                        
        except Exception as e:
            self.logger.log(f"⚠️ Error di langkah Penilaian: {e}")

        # FINAL CHECK: Are we on Calendar page?
        # Image 1 shows "Progress Harian" header and a calendar view.
        try:
            time.sleep(2)
            if "progress" in self.page_app.url or self.page_app.is_visible("text=Total Jam Progress") or self.page_app.is_visible("text=Hari Ini"):
                self.logger.log("✅ Berhasil mencapai Halaman Kalender!")
                self.logger.log(f"URL Kalender: {self.page_app.url}")
                return True
            else:
                self.logger.log("❌ Tidak dapat mengkonfirmasi halaman Kalender.")
                self.logger.log(f"Terjebak di: {self.page_app.url}")
                return False
        except:
            return False

    def handler_2fa(self):
        """Waits for user to handle 2FA."""
        self.logger.log("⏸️  DIJEDA: Silakan selesaikan 2FA secara manual di browser.")
        self.logger.log("Menunggu login berhasil (mendeteksi perubahan URL atau dashboard)...")
        
        # In a real app we might look for specific elements. 
        # Here we'll wait for URL to NOT be the login URL or contain 'dashboard'/'home'
        # Or just a long timeout allowing the user to do it. 
        
        try:
            # Just waiting for a navigation that indicates success. 
            # For MVP, let's give them 2 minutes or until they close it.
            # Better: Check for a specific 'success' element if we knew it.
            # For now, I'll loop check the URL.
            
            start_time = time.time()
            initial_url = self.page_app.url
            self.logger.log(f"URL Awal: {initial_url}")
            
            while time.time() - start_time < 180: # 3 mins
                # Check 1: "Selamat Datang" text (Strongest indicator)
                try:
                    if self.page_app.is_visible("text=Selamat Datang"):
                        self.logger.log("✅ Terdeteksi 'Selamat Datang'. Login berhasil!")
                        return True
                except:
                    pass
                
                # Check 2: URL Change (Fallback)
                # Ensure we are off the SSO/Login page
                current_url = self.page_app.url
                if current_url != initial_url and 'sso-siasn' not in current_url and 'login' not in current_url:
                    # Double check we aren't just on a loading state
                    self.logger.log(f"✅ Login tampaknya berhasil! URL: {current_url}")
                    return True
                    
                time.sleep(1)
            
            self.logger.log("❌ 2FA/Login timeout.")
            return False
        except Exception as e:
            self.logger.log(f"❌ Error saat menunggu 2FA: {str(e)}")
            return False

    def get_doc_text(self) -> str:
        """Extracts text content from the Google Doc tab."""
        if not self.page_doc:
            return ""
        
        self.logger.log("Mengekstrak teks dari Google Doc...")
        try:
            self.page_doc.bring_to_front()
            
            # Wait for doc to load (Google Docs is canvas based but usually has a11y text)
            # .kix-appview-editor is the main container usually
            # But Playwright's page.inner_text('body') usually captures the accessible text content
            
            # Let's wait a bit for load
            # Google Docs content is dynamically loaded.
            # We need to wait for the main editor container
            
            # Skipped waiting for network idle as per user request to speed up
            self.logger.log("Menganggap Doc sudah dimuat (melewati penantian ketat)...")
            
            # Skipped waiting for specific selector
            # self.page_doc.wait_for_selector('.kix-appview-editor', timeout=10000)

            time.sleep(2) # Buffer for rendering
            
            # Google docs is tricky. simple inner_text might get a lot of UI noise.
            # Best approach for MVP without API: Select All + Copy? No, clipboard access is blocked usually.
            # Attempt to read 'body' text content via evaluate which sometimes captures a11y text better
            
            # STRATEGY: Scroll to Bottom to ensure recent entries (virtualized) are rendered
            self.logger.log("Menggulir ke bawah Doc untuk memastikan teks cocok...")
            try:
                self.page_doc.click('body') # Focus
                self.page_doc.keyboard.press("Control+End")
                time.sleep(3) # Wait for virtualized render
            except Exception as e:
                self.logger.log(f"⚠️ Pengguliran gagal: {e}")

            self.logger.log("Membaca konten...")
            
            # Simple body extraction after scroll is often best for a11y text
            content = self.page_doc.evaluate("document.body.innerText")
            
            self.logger.log(f"✓ Diekstrak {len(content)} karakter")
            
            # If content is too short (just header), maybe wait more?
            # Or if it fails to get nodes, we might need to wait for render
            if len(content) < 200:
                self.logger.log("⚠️ Konten tampak pendek. Menunggu dan mencoba lagi...")
                time.sleep(5)
                # Retry with simple body access as safety net
                content = self.page_doc.evaluate("document.body.innerText")
                self.logger.log(f"✓ Percobaan ulang mengekstrak {len(content)} karakter")
            
            return content
            
        except Exception as e:
            self.logger.log(f"❌ Error mengekstrak teks doc: {str(e)}")
            return ""
