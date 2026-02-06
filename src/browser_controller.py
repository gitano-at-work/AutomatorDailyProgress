from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import time

class BrowserController:
    def __init__(self, logger, config: dict):
        self.logger = logger
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page_doc = None  # Tab for Google Doc
        self.page_app = None  # Tab for Web App

    def launch_browser(self):
        """Launches the browser and opens two tabs."""
        try:
            self.playwright = sync_playwright().start()
            headless = self.config.get('browser_headless', False)
            self.logger.log(f"Launching browser (Headless: {headless})...")
            
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context()
            
            # Open Tab 1: Web App
            self.page_app = self.context.new_page()
            self.logger.log("Opened Tab 1: Web App (ASN/SSO)")
            
            # Open Tab 2: Google Doc
            self.page_doc = self.context.new_page()
            self.logger.log("Opened Tab 2: Google Doc")
            
            return True
        except Exception as e:
            error_msg = str(e)
            if "Executable doesn't exist" in error_msg:
                self.logger.log("⚠️ Chromium browser not found.")
                self.logger.log("⬇️ Installing Chromium... (This happens only once)")
                try:
                    import subprocess
                    import sys
                    # Use sys.executable to ensure we use the bundled python or environment
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                    self.logger.log("✅ Browser installed. Retrying launch...")
                    return self.launch_browser() # Retry once
                except Exception as install_error:
                    self.logger.log(f"❌ Failed to auto-install browser: {install_error}")
                    return False
            else:
                self.logger.log(f"❌ Error launching browser: {error_msg}")
                return False

    def close_browser(self):
        """Closes the browser and cleanup."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.logger.log("Browser closed.")

    def navigate_to_doc(self, url: str):
        """Navigates the doc tab to the Google Doc URL."""
        if not self.page_doc:
            return
            
        self.logger.log(f"Navigating to Google Doc...")
        
        # Retry loop for unstable connection
        for attempt in range(3):
            try:
                self.logger.log(f"Loading Doc (Attempt {attempt+1}/3)...")
                # Using a very long timeout (3 mins)
                self.page_doc.goto(url, timeout=180000, wait_until='domcontentloaded')
                self.logger.log("✓ Google Doc loaded (DOM Ready)")
                return
            except Exception as e:
                self.logger.log(f"⚠️ Error loading Doc (Attempt {attempt+1}): {str(e)}")
                time.sleep(5) # Wait before retry
        
        self.logger.log("❌ Failed to load Google Doc after 3 attempts")

    def login(self, auth_code=None):
        """Handles the login flow on the web app tab."""
        if not self.page_app:
            return
            
        login_url = self.config.get('web_app_url')
        username = self.config.get('username')
        password = self.config.get('password')
        
        self.logger.log(f"Navigating to Login Page: {login_url}")
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
            
            self.logger.log("Attempting to fill credentials...")
            
            # 1. Open Login Modal on Landing Page
            self.logger.log("Attempting to open login modal...")
            # 1. Expand Main Menu
            # Logic: Check if "Majalah Digital BKN" (bottom menu item) is visible.
            # If so, menu is expanded. If not, hover/click '#start'.
            majalah_selector = "span:has-text('Majalah Digital BKN')"
            
            try:
                if self.page_app.is_visible(majalah_selector):
                    self.logger.log("Menu already expanded.")
                else:
                    self.logger.log("Hovering main menu to expand...")
                    self.page_app.hover('#start')
                    # Wait for expansion (Majalah button to appear)
                    try:
                        self.page_app.wait_for_selector(majalah_selector, state='visible', timeout=2000)
                        self.logger.log("✓ Menu expanded (Majalah detected)")
                    except:
                        self.logger.log("⚠️ Menu expansion animation timeout. Trying click...")
                        self.page_app.click('#start')
                        time.sleep(1)

                # Now try clicking the button
                if self.page_app.is_visible('#btn-layanan-public'):
                    self.page_app.click('#btn-layanan-public', force=True)
                elif self.page_app.is_visible('#btn-layanan-login-mobile'):
                    self.page_app.click('#btn-layanan-login-mobile', force=True)
                else:
                    self.logger.log("Attempting fallback click for Login menu...")
                    # Fallback: force click specific text
                    self.page_app.click('text=Login', force=True)
                    
            except Exception as e:
                self.logger.log(f"⚠️ Initial expand/click failed: {e}")

            # 2. Click 'Masuk' in Modal to redirect to SSO
            self.logger.log("Waiting for 'Masuk' button...")
            try:
                self.page_app.wait_for_selector('#btn-login', state='visible', timeout=3000)
                self.page_app.click('#btn-login')
            except Exception as e:
                self.logger.log(f"⚠️ Error clicking Masuk: {e}")

            # 3. Wait for SSO Page Redirection
            self.logger.log("Waiting for SSO page...")
            try:
                self.page_app.wait_for_url('**/sso-siasn.bkn.go.id/**', timeout=20000)
                self.logger.log("✓ Redirected to SSO")
            except Exception as e:
                self.logger.log(f"⚠️ Redirection timeout or failed: {e}")
            
            # 4. Fill SSO Credentials
            self.logger.log("Filling SSO credentials...")
            try:
                self.page_app.wait_for_selector('input[name="username"]', state='visible', timeout=10000)
                self.page_app.fill('input[name="username"]', username)
                self.page_app.fill('input[name="password"]', password)
                
                # 5. Submit SSO Form
                self.logger.log("Submitting SSO form...")
                # Try to find a button, or just press Enter
                if self.page_app.is_visible('button[type="submit"]'):
                    self.page_app.click('button[type="submit"]')
                elif self.page_app.is_visible('#kc-login'):
                    self.page_app.click('#kc-login')
                else:
                    self.page_app.press('input[name="password"]', 'Enter')
                
                self.logger.log("✓ Credentials submitted")
                
                # --- AUTO-FILL 2FA (Experimental) ---
                if auth_code and auth_code.strip():
                    self.logger.log(f"⏳ Attempting Auto-2FA with code: {auth_code}")
                    # Wait for OTP input to appear
                    try:
                        # Common ID for Keycloak/SSO OTP is often 'otp', 'totp', or input[name="otp"]
                        # We try to find it quickly (3s)
                        otp_selector = 'input[name="otp"], input[id="otp"], input[id="totp"]'
                        self.page_app.wait_for_selector(otp_selector, state='visible', timeout=5000)
                        
                        self.page_app.fill(otp_selector, auth_code)
                        self.logger.log("  > OTP Code Filled.")
                        
                        # Submit again (often same button ID)
                        if self.page_app.is_visible('#kc-login'):
                            self.page_app.click('#kc-login')
                        elif self.page_app.is_visible('button[type="submit"]'):
                            self.page_app.click('button[type="submit"]')
                        
                        self.logger.log("  > OTP Submitted. Handing off to validation...")
                        
                    except Exception as e:
                        self.logger.log(f"⚠️ Auto-2FA failed (Field not found/Error): {e}")
                
            except Exception as e:
                self.logger.log(f"⚠️ Error filling/submitting SSO: {e}")
                
            # 2FA Pause Logic (Handles validation of success for both Manual and Auto)
            self.handler_2fa()

        except Exception as e:
            self.logger.log(f"❌ Login specific error: {str(e)}")
            return # Stop if critical failure

    def navigate_to_dashboard(self):
        """Navigates from the portal to the specific Kinerja application."""
        if not self.page_app:
            return

        self.logger.log("Navigating to Kinerja Dashboard...")
        try:
            # Retry logic for dashboard navigation
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 1. Expand Menu (Smart Hover)
                    try:
                        majalah_selector = "span:has-text('Majalah Digital BKN')"
                        if self.page_app.is_visible(majalah_selector):
                            self.logger.log("Menu already expanded.")
                        elif self.page_app.is_visible('#start'):
                            self.logger.log("Hovering main menu to expand...")
                            self.page_app.hover('#start')
                            try:
                                self.page_app.wait_for_selector(majalah_selector, state='visible', timeout=2000)
                            except:
                                self.page_app.click('#start')
                                time.sleep(1)
                    except:
                        pass
        
                    # 2. Click 'Layanan Individu ASN'
                    self.logger.log("Clicking 'Layanan Individu ASN'...")
                    self.page_app.wait_for_selector('#btn-layanan-individu', state='visible', timeout=10000)
                    self.page_app.click('#btn-layanan-individu')
                    
                    # 2. Click 'Kinerja'
                    # The user provided HTML shows it's an <a> tag with specific href and class
                    self.logger.log("Clicking 'Kinerja'...")
                    kinerja_selector = 'a[href="https://kinerja.bkn.go.id/login"]'
                    self.page_app.wait_for_selector(kinerja_selector, state='visible', timeout=10000)
                    
                    # Note: This might open in a new tab if target="_blank" (not seen in snippet but possible)
                    # or redirect current page. We assume redirect for now based on "move to another page".
                    
                    # Use expect_navigation or wait_for_url if it redirects
                    with self.page_app.expect_navigation(url="**kinerja.bkn.go.id**", timeout=20000):
                        self.page_app.click(kinerja_selector)
                        
                    self.logger.log("✓ Arrived at Kinerja Dashboard")
                    
                    # Update config URL if needed or just log current
                    self.logger.log(f"Current URL: {self.page_app.url}")
                    return True
                
                except Exception as e:
                    self.logger.log(f"⚠️ Navigation attempt {attempt+1}/{max_retries} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        self.logger.log("Retrying in 5 seconds...")
                        time.sleep(5)
                        # Optional: Reload page to reset state?
                        # self.page_app.reload()
                    else:
                        self.logger.log("❌ All navigation attempts failed.")
                        return False
        except Exception as e:
            self.logger.log(f"❌ Critical Navigation Error: {e}")
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
            
        self.logger.log("Verifying Calendar Page access...")
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
        
        self.logger.log(f"Target Period: Year {current_year}, {qtr}")

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
            self.logger.log("⚠️ Redirected to SKP List. Navigating manually...")
            try:
                # 1. Find Row with Current Year (e.g., "1 Januari 2026")
                # We look for a row that has the year. Current hypothesis: text=2026
                # And click "Penilaian" button in that container.
                
                # We'll use a locator that finds the row containing the year, then the assessment button
                # This is tricky without exact HTML, but trying text based chaining.
                
                self.logger.log(f"Looking for active SKP for {current_year}...")
                
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
                
                self.logger.log("Clicking 'Penilaian' for active period...")
                # We interpret "Penilaian" button.
                # Using specific class from user image visual (blue outline button usually)
                # Text is likely "Penilaian" or "Penilaian SKP"
                
                # Try to locate the button that contains text "Penilaian" inside the list
                self.page_app.click("a:has-text('Penilaian'), button:has-text('Penilaian')", force=True)
                
                self.page_app.wait_for_load_state('networkidle')
                self.logger.log("✓ Entered Assessment (Penilaian) Page")
                
            except Exception as e:
                self.logger.log(f"❌ Failed to click Penilaian: {e}")
                return False

        # CASE 2b: Now we are likely on Penilaian Page (or were already there)
        # URL likely contains '/penilaian'
        # We need to find "TRIWULAN I" (current) and click "Progress Harian"
        
        try:
            # Check if we are on assessment page
            if "penilaian" in self.page_app.url or self.page_app.is_visible("text=Pelaksanaan Kinerja"):
                
                # STABILITY CHECK: Wait for the Quarter header to be visible
                self.logger.log(f"Waiting for '{qtr}' section to load...")
                try:
                    self.page_app.wait_for_selector(f"text={qtr}", timeout=10000)
                    time.sleep(2) # Extra stability buffer as requested
                except:
                    self.logger.log("⚠️ Quarter text not found immediately, proceeding anyway...")

                self.logger.log(f"Looking for 'Progress Harian' button for {qtr}...")
                
                # Attempt to click specifically associated with the Quarter
                # Using a broad locator that filters by text
                # We expect the button to be visible.
                
                # Attempt 1: XPath (Sibling/Container)
                xpath_selector = f"//tr[.//b[contains(text(), '{qtr}')]]/following-sibling::tr[1]//a[contains(., 'Progress Harian')]"
                
                clicked = False
                if self.page_app.is_visible(xpath_selector):
                    self.logger.log("Clicking via XPath...")
                    self.page_app.click(xpath_selector)
                    clicked = True
                else:
                    self.logger.log("XPath selector not visible or invalid. Trying simplified locators...")
                    # Attempt 2: Locator based on text "Progress Harian"
                    # We grab all of them, and if there's more than one, we might need logic.
                    # But usually the TOP one is the active one (Triwulan I).
                    
                    btn = self.page_app.locator("a", has_text="Progress Harian").first
                    if btn.is_visible():
                        self.logger.log("Found 'Progress Harian' button (Generic). Clicking...")
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
                    self.logger.log("Waiting for navigation to Calendar...")
                    try:
                        self.page_app.wait_for_url("**/kinerja_harian/**", timeout=15000)
                    except:
                        self.logger.log("⚠️ URL didn't change quickly. Checking manually...")
                        
        except Exception as e:
            self.logger.log(f"⚠️ Error in Penilaian step: {e}")

        # FINAL CHECK: Are we on Calendar page?
        # Image 1 shows "Progress Harian" header and a calendar view.
        try:
            time.sleep(2)
            if "progress" in self.page_app.url or self.page_app.is_visible("text=Total Jam Progress") or self.page_app.is_visible("text=Hari Ini"):
                self.logger.log("✅ Successfully reached Calendar Page!")
                self.logger.log(f"Calendar URL: {self.page_app.url}")
                return True
            else:
                self.logger.log("❌ Could not confirm Calendar page.")
                self.logger.log(f"Stuck at: {self.page_app.url}")
                return False
        except:
            return False

    def handler_2fa(self):
        """Waits for user to handle 2FA."""
        self.logger.log("⏸️  PAUSED: Please complete 2FA manually on the browser.")
        self.logger.log("Waiting for successful login (detecting URL change or dashboard)...")
        
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
            self.logger.log(f"Initial URL: {initial_url}")
            
            while time.time() - start_time < 180: # 3 mins
                # Check 1: "Selamat Datang" text (Strongest indicator)
                try:
                    if self.page_app.is_visible("text=Selamat Datang"):
                        self.logger.log("✅ Detected 'Selamat Datang'. Login successful!")
                        return True
                except:
                    pass
                
                # Check 2: URL Change (Fallback)
                # Ensure we are off the SSO/Login page
                current_url = self.page_app.url
                if current_url != initial_url and 'sso-siasn' not in current_url and 'login' not in current_url:
                    # Double check we aren't just on a loading state
                    self.logger.log(f"✅ Login appears successful! URL: {current_url}")
                    return True
                    
                time.sleep(1)
            
            self.logger.log("❌ 2FA/Login timeout.")
            return False
        except Exception as e:
            self.logger.log(f"❌ Error during 2FA wait: {str(e)}")
            return False

    def get_doc_text(self) -> str:
        """Extracts text content from the Google Doc tab."""
        if not self.page_doc:
            return ""
        
        self.logger.log("Extracting text from Google Doc...")
        try:
            self.page_doc.bring_to_front()
            
            # Wait for doc to load (Google Docs is canvas based but usually has a11y text)
            # .kix-appview-editor is the main container usually
            # But Playwright's page.inner_text('body') usually captures the accessible text content
            
            # Let's wait a bit for load
            # Google Docs content is dynamically loaded.
            # We need to wait for the main editor container
            
            # Skipped waiting for network idle as per user request to speed up
            self.logger.log("Assuming Doc is loaded (skipping strict waits)...")
            
            # Skipped waiting for specific selector
            # self.page_doc.wait_for_selector('.kix-appview-editor', timeout=10000)

            time.sleep(2) # Buffer for rendering
            
            # Google docs is tricky. simple inner_text might get a lot of UI noise.
            # Best approach for MVP without API: Select All + Copy? No, clipboard access is blocked usually.
            # Attempt to read 'body' text content via evaluate which sometimes captures a11y text better
            
            # STRATEGY: Scroll to Bottom to ensure recent entries (virtualized) are rendered
            self.logger.log("Scrolling to bottom of Doc to ensure text matches...")
            try:
                self.page_doc.click('body') # Focus
                self.page_doc.keyboard.press("Control+End")
                time.sleep(3) # Wait for virtualized render
            except Exception as e:
                self.logger.log(f"⚠️ Scroll failed: {e}")

            self.logger.log("Reading content...")
            
            # Simple body extraction after scroll is often best for a11y text
            content = self.page_doc.evaluate("document.body.innerText")
            
            self.logger.log(f"✓ Extracted {len(content)} chars")
            
            # If content is too short (just header), maybe wait more?
            # Or if it fails to get nodes, we might need to wait for render
            if len(content) < 200:
                self.logger.log("⚠️ Content seems short. Waiting and retrying...")
                time.sleep(5)
                # Retry with simple body access as safety net
                content = self.page_doc.evaluate("document.body.innerText")
                self.logger.log(f"✓ Retry extracted {len(content)} chars")
            
            return content
            
        except Exception as e:
            self.logger.log(f"❌ Error extracting doc text: {str(e)}")
            return ""
