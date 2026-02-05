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
            self.logger.log(f"❌ Error launching browser: {str(e)}")
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

    def login(self):
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
            
            try:
                # The menu is hidden behind #start button and revealed on hover (group-hover)
                # We need to hover the container or the start button to "expand" the menu.
                if self.page_app.is_visible('#start'):
                    self.logger.log("Hovering main menu to expand...")
                    self.page_app.hover('#start')
                    time.sleep(1) # Wait for animation
                
                # Now try clicking the button
                if self.page_app.is_visible('#btn-layanan-public'):
                    self.page_app.click('#btn-layanan-public', force=True)
                elif self.page_app.is_visible('#btn-layanan-login-mobile'):
                    self.page_app.click('#btn-layanan-login-mobile', force=True)
                else:
                    self.logger.log("Attempting fallback click for Login menu...")
                    # Fallback: force click specific text or try clicking start on mobile
                    self.page_app.click('#start', force=True) # Mobile toggle?
                    time.sleep(1)
                    self.page_app.click('text=Login', force=True)
                    
            except Exception as e:
                self.logger.log(f"⚠️ Initial click failed (might already be open?): {e}")

            # 2. Click 'Masuk' in Modal to redirect to SSO
            self.logger.log("Waiting for 'Masuk' button...")
            try:
                self.page_app.wait_for_selector('#btn-login', state='visible', timeout=5000)
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
            except Exception as e:
                self.logger.log(f"⚠️ Error filling/submitting SSO: {e}")
                
            # 2FA Pause Logic
            self.handler_2fa()

        except Exception as e:
            self.logger.log(f"❌ Login specific error: {str(e)}")
            return # Stop if critical failure
                
            # 2FA Pause Logic
            self.handler_2fa()

        except Exception as e:
            self.logger.log(f"❌ Login navigation specific error: {str(e)}")

    def navigate_to_dashboard(self):
        """Navigates from the portal to the specific Kinerja application."""
        if not self.page_app:
            return

        self.logger.log("Navigating to Kinerja Dashboard...")
        try:
            # 1. Click 'Layanan Individu ASN'
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
            self.logger.log(f"❌ Error navigating to dashboard: {str(e)}")
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
            while time.time() - start_time < 120: # 2 mins
                if self.page_app.url != initial_url and 'login' not in self.page_app.url:
                    self.logger.log(f"✅ Login appears successful! URL: {self.page_app.url}")
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
            
            self.logger.log("Waiting for Doc to fully load...")
            try:
                 self.page_doc.wait_for_load_state('networkidle', timeout=120000)
            except:
                 self.logger.log("⚠️ Network idle timeout, proceeding...")
            
            # Wait for specific editor element usually present in Google Docs
            try:
                self.page_doc.wait_for_selector('.kix-appview-editor', timeout=60000)
                self.logger.log("✓ Editor loaded")
            except:
                self.logger.log("⚠️ Editor selector invalid, waiting generic time...")
                time.sleep(5)
            
            time.sleep(5) # Extra buffer for text rendering
            
            # Google docs is tricky. simple inner_text might get a lot of UI noise.
            # Best approach for MVP without API: Select All + Copy? No, clipboard access is blocked usually.
            # Attempt to read 'body' text content via evaluate which sometimes captures a11y text better
            
            self.logger.log("Reading content...")
            
            # Helper to get text from all pages/sections
            content = self.page_doc.evaluate("""() => {
                return document.body.innerText;
            }""")
            
            self.logger.log(f"✓ Extracted {len(content)} chars")
            
            # If content is too short (just header), maybe wait more?
            if len(content) < 200:
                self.logger.log("⚠️ Content seems short. Waiting and retrying...")
                time.sleep(5)
                content = self.page_doc.evaluate("document.body.innerText")
                self.logger.log(f"✓ Retry extracted {len(content)} chars")
            
            return content
            
        except Exception as e:
            self.logger.log(f"❌ Error extracting doc text: {str(e)}")
            return ""
