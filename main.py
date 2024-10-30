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
    MoveTargetOutOfBoundsException, TimeoutException
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from form_processor import apply_for_job  # Import the function
from form_processor import move_html
import config

template_path = config.template_path


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


def ask_chatgpt(job_description: str) -> dict:
    """Send the job description and profile to GPT and get a structured response."""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.api_key}'
        }

        data = {
            "model": config.gpt_model,  # Replace with the model you have access to
            "messages": [
                {"role": "system",
                 "content": "You are a helpful assistant that determines the suitability of my profile with the job description."},
                {
                    "role": "user",
                    "content": f"""
                    Given the following profile: {config.profile}
                    And the following job description:
                    {job_description}

                    Do you think I am a suitable match for this job? 
                    If No, respond with a structured JSON containing "suitable":"No". Strictly follow the schema.  Do not provide any other words "", json, or comma or anything other than this.
                    If Yes, 
                    Based on the job description  and profile write a small profile section for a cv. Make sure to include relevant keywords so that it will get detected by ATS.
                    Based on the job description and profile write a skill section for a cv. Make sure to include relevant skills so that the cv will get detected by ATS.
                    Respond with a structured JSON containing "suitable":"Yes", "profile":"", "skills":"".
                    Output only the json schema.  Do not provide any other words "", json, or comma or anything other than this.
                    """
                }
            ],
            "max_tokens": 1200,
            "n": 1,
            "temperature": 1.0
        }

        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data),
                                 timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        message = response.json()['choices'][0]['message']['content'].strip()
        # print(message)
        # Extract JSON from the message
        json_string = extract_json_from_text(message)
        if not json_string:
            return {"error": "No JSON found", "message": message}
        try:
            # Attempt to parse the JSON string
            data = json.loads(json_string)
            # print(data)
            return data

        except json.JSONDecodeError:
            return {"error": "JSON parsing error", "message": json_string}

    except requests.exceptions.RequestException as e:
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
    """Extract the 'suitable' value from the GPT response."""
    try:
        suitable_value = data["suitable"]
        print("Is it suitable?", suitable_value)
        return suitable_value
    except KeyError:
        return "API key Error"


# Path to the user profile directory
# user_profile = "C:/Users/user/AppData/Local/Google/Chrome/User Data/Profile 2"
# chrome_options.add_argument(f"user-data-dir={user_profile}")


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
        self.browser = webdriver.Chrome(options=chrome_options)
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
                # print("Sent ESCAPE key to close popup.")
                time.sleep(0.5)  # Wait briefly after sending escape key

                # Send the Enter key if needed (in case a confirmation dialog appears)
                self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
                # print("Sent ENTER key to confirm closing popup.")
                time.sleep(0.5)  # Wait briefly after sending enter key


        except NoSuchElementException:
            pass
        except Exception as e:
            print(f"Error while sending keys to close popup: {e}")

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

    def simulate_typing(self, element, text):
        """Simulate human-like typing in an input field."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes

    def find_job(self, job_search_keyword: str) -> None:
        """Search for a job with the specified keyword."""
        query_input = self.browser.find_element(By.NAME, value="q")
        query_input.clear()  # Clear the previous keyword

        self.simulate_typing(query_input, job_search_keyword)
        time.sleep(random.uniform(0.5, 1.5))

        clear_btn = self.browser.find_element(By.XPATH,
                                              value='//*[@id="jobsearch"]/div/div[1]/div[1]/div/div/span/span[2]')
        ActionChains(self.browser).move_to_element(clear_btn).click().perform()
        time.sleep(random.uniform(0.5, 1.5))

        self.simulate_typing(query_input, job_search_keyword)
        time.sleep(random.uniform(0.5, 1.5))

        find_btn = self.browser.find_element(By.XPATH, "//button[contains(text(), 'Find jobs')]")
        ActionChains(self.browser).move_to_element(find_btn).click().perform()
        time.sleep(random.uniform(1.5, 3.0))  # Random delay

        try:
            date_btn = self.browser.find_element(By.XPATH, value='//*[@id="dateLabel"]')
            ActionChains(self.browser).move_to_element(date_btn).click().perform()
            time.sleep(random.uniform(1.5, 3.0))  # Random delay

        except NoSuchElementException:
            print("Date sort error")

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

                    date_recorded = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    resume_path = None
                    gpt_answer = None
                    application_status = None
                    if suitability == "Yes":
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



