import requests
import json
import csv
from selenium import webdriver
import time
import random
from selenium.webdriver.common.action_chains import ActionChains
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from docx import Document
import re
import shutil
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    MoveTargetOutOfBoundsException, TimeoutException, StaleElementReferenceException
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from form_processor import apply_for_job  # Import the function
from form_processor import move_html
from selenium.webdriver.chrome.service import Service
import sys
import platform as py_platform
import config

template_path = config.template_path


def get_chrome_version() -> str | None:
    """
    Returns the installed Chrome version string, e.g. '140.0.7339.128', or None if not found.
    Windows: tries the default path; else falls back to 'chrome --version'.
    Mac/Linux: runs 'google-chrome --version' or 'chrome --version'.
    """
    import subprocess, shutil

    candidates = []
    if sys.platform.startswith("win"):
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            shutil.which("chrome"),
            shutil.which("google-chrome"),
        ]
    else:
        candidates = [
            shutil.which("google-chrome"),
            shutil.which("chrome"),
            shutil.which("chromium"),
        ]

    for p in candidates:
        if not p:
            continue
        try:
            out = subprocess.check_output([p, "--version"], stderr=subprocess.STDOUT, text=True).strip()
            ver = next((tok for tok in out.split() if tok[0].isdigit()), None)
            if ver:
                return ver
        except Exception:
            pass
    return None


def platform_tag():
    """
    Returns (folder_tag, exe_name) for ChromeDriver by OS/arch.
    """
    sysname = sys.platform
    machine = py_platform.machine().lower()

    if sysname.startswith("win"):
        return ("win64", "chromedriver.exe")
    if sysname == "darwin":
        if "arm" in machine or "aarch64" in machine:
            return ("mac-arm64", "chromedriver")
        else:
            return ("mac-x64", "chromedriver")
    return ("linux64", "chromedriver")


def local_driver_path_for(chrome_version: str):
    """
    Returns the expected local driver path like ./drivers/<platform>/<major>/chromedriver[.exe]
    """
    major = chrome_version.split(".", 1)[0]
    folder_tag, exe_name = platform_tag()
    driver_dir = os.path.join(os.getcwd(), "drivers", folder_tag, major)
    os.makedirs(driver_dir, exist_ok=True)
    return os.path.join(driver_dir, exe_name), major


def cache_downloaded_driver(src_path: str, major: str):
    """
    Copy a successfully-downloaded driver into the local cache folder so future runs work offline.
    """
    try:
        folder_tag, exe_name = platform_tag()
        dest_dir = os.path.join(os.getcwd(), "drivers", folder_tag, major)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, exe_name)
        if os.path.abspath(src_path) != os.path.abspath(dest_path):
            shutil.copyfile(src_path, dest_path)
            print(f"[Driver] Cached driver -> {dest_path}")
    except Exception as e:
        print(f"[Driver] Could not cache driver: {e}")


def apply_proxy_env_if_any():
    """
    If config has 'driver_download_proxy', apply it to environment so
    Selenium Manager / webdriver-manager / autoinstaller can use it.
    """
    proxy = getattr(config, "driver_download_proxy", None)
    if proxy:
        os.environ.setdefault("HTTPS_PROXY", proxy)
        os.environ.setdefault("HTTP_PROXY", proxy)
        print(f"[Driver] Using proxy from config.driver_download_proxy")


def build_chrome_driver(chrome_options: webdriver.ChromeOptions) -> webdriver.Chrome:
    """
    Order of strategies:
      0) Use CHROMEDRIVER env var if set (explicit override)
      0b) Use a locally cached driver: ./drivers/<platform>/<major>/chromedriver[.exe]
      1) Selenium Manager (built into Selenium)
      2) webdriver-manager (downloads and caches)
      3) chromedriver-autoinstaller
    - If (2) or (3) succeeds, we copy the driver into ./drivers/... for offline reuse.
    """
    chrome_ver = get_chrome_version()
    if chrome_ver:
        local_path, major = local_driver_path_for(chrome_ver)
        print(f"[Driver] Detected Chrome {chrome_ver} (major {major})")
    else:
        local_path, major = (None, None)
        print("[Driver] Could not detect Chrome version")

    apply_proxy_env_if_any()

    # 0) explicit env var override
    env_path = os.environ.get("CHROMEDRIVER")
    if env_path and os.path.exists(env_path):
        print(f"[Driver] Using CHROMEDRIVER from env: {env_path}")
        return webdriver.Chrome(service=Service(env_path), options=chrome_options)

    # 0b) local offline cache
    if local_path and os.path.exists(local_path):
        print(f"[Driver] Using locally cached driver: {local_path}")
        return webdriver.Chrome(service=Service(local_path), options=chrome_options)

    # 1) Selenium Manager
    try:
        print("[Driver] Trying Selenium Manager (default)...")
        drv = webdriver.Chrome(options=chrome_options)
        return drv
    except Exception as e1:
        print(f"[Driver] Selenium Manager failed: {e1}")

    # 2) webdriver-manager
    try:
        print("[Driver] Trying webdriver-manager fallback...")
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        print(f"[Driver] webdriver-manager installed: {driver_path}")
        drv = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
        if major:
            cache_downloaded_driver(driver_path, major)
        return drv
    except Exception as e2:
        print(f"[Driver] webdriver-manager failed: {e2}")

    # 3) chromedriver-autoinstaller
    try:
        print("[Driver] Trying chromedriver-autoinstaller fallback...")
        import chromedriver_autoinstaller
        driver_path = chromedriver_autoinstaller.install(cwd=True)
        print(f"[Driver] autoinstaller installed: {driver_path}")
        drv = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
        if major:
            cache_downloaded_driver(driver_path, major)
        return drv
    except Exception as e3:
        print(f"[Driver] chromedriver-autoinstaller failed: {e3}")

    # Manual instructions if all strategies fail
    if chrome_ver:
        folder_tag, exe_name = platform_tag()
        manual_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_ver}/{folder_tag}/chromedriver-{folder_tag}.zip"
        msg = (
            "Could not obtain a compatible ChromeDriver with any strategy.\n"
            "Your network seems to block downloads. Options:\n"
            f"  • Manually download the driver zip for your Chrome version from:\n"
            f"    {manual_url}\n"
            f"  • Unzip and place '{exe_name}' at:\n"
            f"    {local_path}\n"
            "  • Or set config.driver_download_proxy to your corporate proxy (https://user:pass@host:port),\n"
            "    or set HTTPS_PROXY/HTTP_PROXY env vars, then re-run.\n"
        )
        raise RuntimeError(msg)

    raise RuntimeError(
        "Could not obtain a compatible ChromeDriver with any strategy, and Chrome version could not be detected.\n"
        "Please ensure you have Chrome installed, or provide CHROMEDRIVER env var to a local driver."
    )


def extract_json_from_text(text: str) -> str:
    """Extract the first JSON object found in a string."""
    try:
        # Use regular expression to find a JSON object in the string
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            print(json_match.group(0))
            return json_match.group(0)
        else:
            return None
    except re.error as e:
        print(f"Regex error: {e}")
        return None
    
def _extract_openai_output_text(resp_json: dict) -> str:
    """
    Get the plain text answer from a Responses API JSON.
    Prefer 'output_text'; if it's empty/missing, fall back to
    concatenating any content blocks of type 'output_text' in 'output'.
    """
    # Primary (when present)
    txt = (resp_json.get("output_text") or "").strip()
    if txt:
        return txt

    # Fallback: walk the 'output' array
    parts = []
    for item in resp_json.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    t = c.get("text", "")
                    if t:
                        parts.append(t)
    return "\n".join(parts).strip()



def ask_chatgpt(job_description: str) -> dict:
    """Call OpenAI Responses API and return ONLY the JSON object we asked for, with simple prints."""
    try:
        if not getattr(config, "api_key", None):
            print("[GPT] Missing API key.")
            return {"error": "Missing API key", "message": "Set config.api_key or OPENAI_API_KEY."}

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        system = "You decide fit and reply ONLY with valid JSON. No prose."
        user = (
            f"Profile:\n{config.profile}\n\n"
            f"Job description:\n{job_description}\n\n"
            "If not a match, return exactly: {\"suitable\":\"No\"}.\n"
            "If a match, return exactly: "
            "{\"suitable\":\"Yes\",\"profile\":\"...\",\"skills\":\"...\"}.\n"
            "Keep 'profile' and 'skills' concise."
        )

        payload = {
            "model": config.gpt_model,  # e.g. "gpt-5-mini"
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # JSON mode for Responses API
            "text": {"format": {"type": "json_object"}, "verbosity": "low"},
            "reasoning": {"effort": "low"},
          
            "max_output_tokens": 600,
        }

        resp = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=60
        )

        print(f"[GPT] HTTP {resp.status_code}")
        if not resp.ok:
            print(f"[GPT] Body: {resp.text}")
            return {"error": "HTTP error", "message": resp.text}

        j = resp.json()
        print(f"[GPT] model={j.get('model')} status={j.get('status')} usage={j.get('usage')}")

        # Extract text: prefer 'output_text', else collect from 'output' blocks
        text = (j.get("output_text") or "").strip()
        if not text:
            parts = []
            for item in j.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            t = c.get("text", "")
                            if t:
                                parts.append(t)
            text = "\n".join(parts).strip()

        print(f"[GPT] raw_text: {text}")

        if not text:
            print("[GPT] Empty output_text.")
            return {"error": "Empty output", "message": j}

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[GPT] JSON decode failed: {e}")
            return {"error": "JSON decode error", "message": text}

        print(f"[GPT] parsed: {parsed}")
        return parsed

    except requests.Timeout:
        print("[GPT] Request timeout.")
        return {"error": "Request timeout", "message": "OpenAI request timed out"}
    except Exception as e:
        print(f"[GPT] Exception: {e}")
        return {"error": "Request error", "message": str(e)}








def update_resume_with_json(data: dict, template_path: str):
    """Update the Word document with profile and skills from the JSON output, and manage resume file renaming."""
    if "profile" not in data or "skills" not in data:
        print("Invalid JSON data")
        return

    profile = data["profile"]
    skills = data["skills"]

    current_resume = config.current_resume

    # Create a new resume from the template
    shutil.copy(template_path, current_resume)

    # Load the new Word document (Current - resume.docx)
    doc = Document(current_resume)

    # Define a function to set font to Times New Roman, size 12, and remove bold formatting
    def format_paragraph(paragraph):
        if config.modify_font.lower() == "yes":
            for run in paragraph.runs:
                run.font.name = config.font
                run.font.size = Pt(config.size)
                run.font.bold = config.bold
                # Ensure Times New Roman for each run by modifying the font element
                rFonts = OxmlElement('w:rFonts')
                rFonts.set(qn('w:ascii'), config.font)
                rFonts.set(qn('w:hAnsi'), config.font)
                run._r.get_or_add_rPr().append(rFonts)

    # Iterate through paragraphs and replace placeholders, then apply formatting
    for paragraph in doc.paragraphs:
        if "<*profile*>" in paragraph.text:
            paragraph.text = paragraph.text.replace("<*profile*>", profile)
            format_paragraph(paragraph)
        if "<*skills*>" in paragraph.text:
            paragraph.text = paragraph.text.replace("<*skills*>", skills)
            format_paragraph(paragraph)

    # Save the modified document
    doc.save(current_resume)
    print(f"Resume updated successfully as {current_resume}")


def move_resume(job_title: str, job_id: str):
    try:
        current_resume = config.current_resume
        # Define the paths
        resume_folder = config.resume_folder
        os.makedirs(resume_folder, exist_ok=True)

        new_resume_name = f"{job_title} - {job_id}.docx"
        new_resume_path = os.path.join(resume_folder, new_resume_name)

        # Check if "Current - resume.docx" exists and rename it to the last job's title and ID
        if os.path.exists(current_resume):
            shutil.move(current_resume, new_resume_path)
            print(f"Renamed template to {new_resume_name} and moved it to {resume_folder}")
            return new_resume_path
    except:
        print("Move error or already file moved")
        return None


def parse_gpt_response(data: dict) -> str:
    """
    Return 'Yes' or 'No'. Print the normalization so you can see the decision.
    """
    if isinstance(data, dict) and data.get("error"):
        print(f"[GPT] treating as No due to error: {data.get('message')}")
        return "No"

    raw = data.get("suitable", "")
    norm = str(raw).strip().lower()
    decision = "Yes" if norm in {"yes", "y", "true", "1"} else "No"
    print(f"[GPT] suitability raw={raw!r} norm={norm!r} -> {decision}")
    return decision






class IndeedAutoApplyBot:
    def __init__(self) -> None:
        chrome_options = webdriver.ChromeOptions()

        # Define the profile directory
        profile_dir = os.path.join(os.getcwd(), 'chrome_profile')

        # Create the profile directory if it doesn't exist
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            print(f"Created new Chrome profile directory at {profile_dir}")

        # Add the user-data-dir option to ChromeOptions
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")

        # Prevent automation detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # Keep the browser open after the script ends
        chrome_options.add_experimental_option("detach", True)

        # Initialize the browser with the specified options
        self.browser = build_chrome_driver(chrome_options)
        url = config.indeed_homepage_url
        self.browser.get(url)
        time.sleep(random.uniform(2, 3.0))  # Random delay

        # Load or create the master CSV file
        self.master_csv = config.master_csv
        self.latest_csv = config.latest_csv
        self.processed_jobs = self.load_master_csv()

        # Prepare the latest run CSV file
        self.prepare_latest_csv()

    def close_popups(self):
        """Close popups by sending ESCAPE and ENTER keys only if a close button is visible."""
        try:
            # Locate the close button using its aria-label attribute
            close_button_selector = "//button[@aria-label='close' and @type='button']"

            # Check if the close button exists and is visible
            close_button = self.browser.find_element(By.XPATH, close_button_selector)

            # Only send ESCAPE and ENTER if the close button is visible
            if close_button.is_displayed():
                # Send the Escape key to close popups
                self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(0.5)
                # Send the Enter key if needed (in case a confirmation dialog appears)
                self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
                time.sleep(0.5)
        except NoSuchElementException:
            pass
        except Exception as e:
            print(f"Error while sending keys to close popup: {e}")

    def simulate_typing(self, locator, text, per_char=True):
        """
        Types into an element found by `locator` (e.g., (By.NAME, "q")).
        Re-finds the element if it goes stale while typing.
        """
        wait = WebDriverWait(self.browser, 15)
        retries = 3
        for attempt in range(1, retries + 1):
            try:
                el = wait.until(EC.element_to_be_clickable(locator))
                # Focus & robust clear
                el.click()
                time.sleep(random.uniform(0.2, 0.5))
                el.send_keys(Keys.CONTROL, 'a')
                el.send_keys(Keys.DELETE)
                time.sleep(random.uniform(0.1, 0.3))
                # Type
                if per_char:
                    for ch in text:
                        el.send_keys(ch)
                        time.sleep(random.uniform(0.03, 0.12))
                else:
                    el.send_keys(text)
                return
            except StaleElementReferenceException:
                print(f"Search element went stale; retrying ({attempt}/{retries})...")
                time.sleep(0.5)
            except Exception as e:
                print(f"Typing failed (attempt {attempt}/{retries}): {e}")
                time.sleep(0.8)
        raise RuntimeError("Could not type into the search box after multiple attempts.")

    def find_job(self, job_search_keyword: str) -> None:
        """Search for a job with the specified keyword (stale-safe)."""
        # Close any cookie/consent popups first to avoid DOM reshuffles
        self.close_popups()

        # 1) Wait for the search input and type (stale-safe)
        what_locator = (By.NAME, "q")
        self.simulate_typing(what_locator, job_search_keyword, per_char=True)

        # 2) Submit the form: ENTER first (most reliable), then button as fallback
        submitted = False
        try:
            el = WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable(what_locator))
            el.send_keys(Keys.ENTER)
            submitted = True
        except Exception as e:
            print(f"ENTER submit failed: {e}")

        if not submitted:
            # Fallback: click the "Find jobs" button by text; support nested span/button structures
            try:
                find_btn = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(., 'Find jobs') or .//span[contains(., 'Find jobs')]]")
                    )
                )
                self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", find_btn)
                ActionChains(self.browser).move_to_element(find_btn).click().perform()
                submitted = True
            except Exception as e:
                print(f"Find button click fallback failed: {e}")

        time.sleep(random.uniform(1.5, 3.0))
        self.close_popups()

        # 3) Wait for results to be present (don’t hard-fail; just try)
        try:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, config.job_listings_element))
            )
        except Exception:
            print("Results not detected yet; continuing anyway.")

        # 4) Optional: try opening the date filter if available
        try:
            date_btn = WebDriverWait(self.browser, 5).until(
                EC.element_to_be_clickable((By.ID, "dateLabel"))
            )
            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_btn)
            ActionChains(self.browser).move_to_element(date_btn).click().perform()
            time.sleep(random.uniform(1.0, 2.0))
        except Exception:
            print("Date sort error")

    def try_click(self, element, retries=3):
        """Try to click an element, handle MoveTargetOutOfBoundsException by retrying after closing popups."""
        attempt = 0
        while attempt < retries:
            try:
                # Try to scroll to and click the element
                self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                ActionChains(self.browser).move_to_element(element).click().perform()
                return True
            except (MoveTargetOutOfBoundsException, ElementClickInterceptedException) as e:
                print(f"Error encountered: {e}. Attempting to close popups and retry...")
                self.close_popups()  # Attempt to close popups
                attempt += 1
                time.sleep(2)  # Give some time for the popup to close
        return False  # Return False if all retries fail

    def load_master_csv(self):
        """Load the master CSV file if it exists, otherwise create it."""
        if os.path.exists(self.master_csv):
            with open(self.master_csv, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                return set(row["Job ID"] for row in reader)
        else:
            with open(self.master_csv, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["Job Title", "Company Name", "Location", "Job Description", "Posting Date", "Apply Link",
                     "Job Listing URL", "Job ID", "Date Recorded", "Internal apply", "Resume path", "AI answer",
                     "Suitability", "Application status"])
            return set()

    def prepare_latest_csv(self):
        """Create the latest run CSV file with headers."""
        with open(self.latest_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Job Title", "Company Name", "Location", "Job Description", "Posting Date", "Apply Link",
                             "Job Listing URL", "Job ID", "Date Recorded", "Internal apply", "Resume path",
                             "AI answer", "Suitability", "Application status"])

    def extract_job_id(self, url):
        """Extract the job ID from the Indeed job URL."""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        job_id = query_params.get(config.url_query_keword, [None])[0]  # Extract the 'jk' parameter value
        return job_id

    def click_reject_all_button(self):
        """Wait for the page to load and click the 'Reject All' button if it exists."""
        try:
            # Wait for the page to finish loading and for the button to be present in the DOM
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "onetrust-reject-all-handler")))

            # Check if the "Reject All" button is present and visible
            reject_all_button = self.browser.find_element(By.ID, "onetrust-reject-all-handler")

            if reject_all_button.is_displayed() and reject_all_button.is_enabled():
                reject_all_button.click()
                print("Clicked the 'Reject All' button.")
            else:
                print("The 'Reject All' button is not visible or enabled.")

        except TimeoutException:
            print("Timed out waiting for the 'Reject All' button to appear.")
        except NoSuchElementException:
            print("No 'Reject All' button found.")
        except Exception as e:
            print(f"An error occurred while trying to click the 'Reject All' button: {e}")

    def scrape_job_listings(self, job_search_keywords: list) -> None:
        """Scrape each job listing and save details to the CSV files."""
        # Attempt to click the "Reject All" button if it appears
        self.click_reject_all_button()
        for keyword in job_search_keywords:
            self.find_job(keyword)  # Search for the current keyword
            is_next_page = True
            page_count = 0  # Counter to track the number of pages processed

            while is_next_page and page_count < config.pagination_limit:
                job_listings = self.browser.find_elements(By.CSS_SELECTOR, config.job_listings_element)
                if not job_listings:
                    print("Could not find any job listings. Please check the 'job_listings_element' in config.py.")
                    break  # Exit the pagination loop since there's nothing to process

                for job in job_listings:
                    try:
                        job_title_element = job.find_element(By.CSS_SELECTOR, config.job_title_element)
                        job_listing_url = job_title_element.get_attribute("href")
                    except NoSuchElementException:
                        print("Could not find the job title element. Modify config.py with the updated element.")
                        continue

                    job_id = self.extract_job_id(job_listing_url)
                    if job_id is None:
                        print("Could not extract the job ID from the URL. Skipping this job.")
                        continue
                    if job_id in self.processed_jobs:
                        print(f"Skipping already processed job ID: {job_id}")
                        continue

                    job_title = job_title_element.text

                    try:
                        company_name = job.find_element(By.CSS_SELECTOR, config.company_name_element).text
                    except NoSuchElementException:
                        print("Could not find the company name element. Modify config.py with the updated element.")
                        continue

                    try:
                        location = job.find_element(By.CSS_SELECTOR, config.location_element).text
                    except NoSuchElementException:
                        print("Could not find the location element. Modify config.py with the updated element.")
                        continue

                    # Try clicking the job title element with retries
                    if not self.try_click(job_title_element):
                        print(f"Failed to click job title after multiple retries: {job_title}")
                        continue

                    time.sleep(random.uniform(2.0, 3.0))  # Random delay after clicking

                    try:
                        job_description = self.browser.find_element(By.ID, config.job_description_element).text
                    except NoSuchElementException:
                        print("Could not find the job description element. Modify config.py with the updated element.")
                        continue

                    # Extract the posting date
                    try:
                        date_element = job.find_element(By.CSS_SELECTOR, config.posted_date_element).text
                        today = datetime.today()
                        days_ago = [int(s) for s in date_element.split() if s.isdigit()]

                        if len(days_ago) > 0:
                            date_t = timedelta(days=days_ago[0])
                            final_date = (today - date_t).strftime('%Y-%m-%d')
                        elif "just posted" in date_element.lower():
                            final_date = today.strftime('%Y-%m-%d')
                        else:
                            print(f"Failed to parse date: defaulting to today's date")
                            final_date = today.strftime('%Y-%m-%d')

                        posting_date = final_date
                    except NoSuchElementException:
                        print("Could not find the date element. Modify config.py with the updated element.")
                        posting_date = "Not available"

                    internal_apply_button_found = "No"  # Flag to track if the internal apply button is found
                    apply_link = "Apply link not found"
                    internal_apply_button = None  # Initialize variable

                    # Try to find the internal apply button
                    try:
                        time.sleep(random.uniform(2.0, 3.0))
                        internal_apply_button = self.browser.find_element(By.XPATH, config.internal_apply_button_element)
                        internal_apply_button_found = "Yes"
                        apply_link = self.browser.current_url  # Assuming internal apply redirects to the current URL
                    except NoSuchElementException:
                        print("Could not find the internal apply button.")
                        # Try to find the external apply button
                        try:
                            external_apply_button = self.browser.find_element(By.XPATH,
                                                                              config.external_apply_button_element)
                            apply_link = external_apply_button.get_attribute("href")
                            if not apply_link:
                                apply_link = "Apply link not available"
                        except NoSuchElementException:
                            print("Could not find the external apply button using XPath.")
                            # Try alternative CSS selector for external apply button
                            try:
                                external_apply_button = self.browser.find_element(
                                    By.CSS_SELECTOR, "div#applyButtonLinkContainer button"
                                )
                                apply_link = external_apply_button.get_attribute("href")
                                if not apply_link:
                                    apply_link = "Apply link not available"
                            except NoSuchElementException:
                                print("Could not find the external apply button using CSS selector.")
                                apply_link = "Apply link not found"

                    data = ask_chatgpt(job_description)
                    suitability = parse_gpt_response(data)
                    print(suitability)

                    date_recorded = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    resume_path = None
                    gpt_answer = None
                    application_status = None
                    if suitability.strip().lower() == "yes":
                        update_resume_with_json(data, template_path)

                        if internal_apply_button_found == "Yes" and config.auto_apply.lower() == "yes":
                            if internal_apply_button is not None:
                                gpt_answer, application_status = apply_for_job(
                                    self.browser, internal_apply_button, resume_file_name=config.current_resume
                                )
                            else:
                                print("Internal apply button is None, cannot proceed with application.")
                                gpt_answer = None
                                application_status = "Failed to apply - internal apply button not found"
                        else:
                            gpt_answer = None
                            application_status = "Not applied"

                        resume_path = move_resume(job_title, job_id)
                        html_path = move_html(job_title, job_id)

                    with open(self.master_csv, mode='a', newline='', encoding='utf-8') as master_file:
                        master_writer = csv.writer(master_file)
                        master_writer.writerow(
                            [
                                job_title, company_name, location, job_description, posting_date, apply_link,
                                job_listing_url, job_id, date_recorded, internal_apply_button_found, resume_path,
                                gpt_answer, suitability, application_status
                            ]
                        )

                    with open(self.latest_csv, mode='a', newline='', encoding='utf-8') as latest_file:
                        latest_writer = csv.writer(latest_file)
                        latest_writer.writerow(
                            [
                                job_title, company_name, location, job_description, posting_date, apply_link,
                                job_listing_url, job_id, date_recorded, internal_apply_button_found, resume_path,
                                gpt_answer, suitability, application_status
                            ]
                        )

                    self.processed_jobs.add(job_id)

                    # Close any popup that might appear
                    self.close_popups()

                page_count += 1

                if page_count < config.pagination_limit:
                    try:
                        next_page_button = self.browser.find_element(By.XPATH,
                                                                     config.next_page_element)
                        self.browser.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", next_page_button
                        )
                        ActionChains(self.browser).move_to_element(next_page_button).click().perform()
                        time.sleep(random.uniform(2.0, 3.0))  # Wait for the next page to load
                    except NoSuchElementException:
                        print("Could not find the next page button. Check elements in config.py. Ending pagination.")
                        is_next_page = False  # If no next page, exit the loop
                else:
                    is_next_page = False  # Stop after reaching the pagination limit


if __name__ == "__main__":
    if not config.api_key:
        print("Error: The API key is empty. The program wont identify sutiable jobs, it will only scrape")

    JOB_SEARCH = config.job_search_keywords
    bot = IndeedAutoApplyBot()
    bot.scrape_job_listings(JOB_SEARCH)
