import time
import json
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from difflib import get_close_matches
from selenium.webdriver.support.ui import Select
import os
import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import shutil
import config

# # Set up Chrome options to connect to the existing session
# chrome_options = Options()
# chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
#
# # Create a new driver instance that connects to the running browser
# driver = webdriver.Chrome(options=chrome_options)

# Define your OpenAI API key here

OPENAI_API_KEY = config.api_key





def apply_for_job(browser, internal_apply_button, resume_file_name):
    try:
        # Step 1: Store the original window handle and list of handles before clicking the button
        original_window = browser.current_window_handle  # Store the current window handle
        original_windows = browser.window_handles  # Store the list of current window handles

        # Step 2: Click the internal apply button to open the new window
        ActionChains(browser).move_to_element(internal_apply_button).click().perform()
        time.sleep(random.uniform(0.5, 1.5))  # Sleep to allow for the window to open
        print("Internal apply link clicked")

        # Step 3: Wait for the new window to appear and switch to it
        new_window = WebDriverWait(browser, 10).until(
            lambda d: [window for window in d.window_handles if window not in original_windows][0]
        )
        browser.switch_to.window(new_window)
        print("Switched to the new window")


        time.sleep(random.uniform(4.0, 5.0))
        # Step 3.5: Check if the URL has 'resume' in it
        current_url = browser.current_url
        previous_url = current_url
        if 'resume' in current_url:
            print("URL contains 'resume'. Proceeding with the steps.")
        else:
            print("URL does not contain 'resume'. Attempting to click 'Continue' buttons.")
            max_attempts = 5  # Maximum number of attempts
            attempt = 0

            while attempt < max_attempts and 'resume' not in current_url:
                attempt += 1
                print(f"Attempt {attempt}: Looking for 'Continue' buttons.")
                continue_buttons = browser.find_elements(By.XPATH, "//button//span[text()='Continue']")

                if continue_buttons:
                    button_clicked = False
                    for button in continue_buttons:
                        try:
                            # Smooth scroll to the button
                            browser.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                            ActionChains(browser).move_to_element(button).click().perform()
                            print("Continue button clicked.")
                            time.sleep(random.uniform(2.0, 3.0))

                            # Check if the URL has changed
                            current_url = browser.current_url
                            if current_url != previous_url:
                                print("URL has changed after clicking 'Continue' button.")
                                previous_url = current_url
                                button_clicked = True
                                break  # Exit the for loop after clicking one button
                        except Exception as e:
                            print(f"Could not click 'Continue' button: {e}")

                    if button_clicked:
                        # We have clicked a button, check if 'resume' is now in current_url
                        if 'resume' in current_url:
                            print("URL now contains 'resume'. Proceeding with the steps.")
                            break  # Exit the while loop
                        else:
                            # URL changed but doesn't contain 'resume', proceed to the next attempt
                            print("URL changed but does not contain 'resume'. Continuing to next attempt.")
                            continue  # Continue the while loop
                    else:
                        # No buttons could be clicked
                        print("No clickable 'Continue' buttons were successfully clicked. Waiting before retrying.")
                        time.sleep(random.uniform(2.0, 3.0))
                else:
                    # No 'Continue' buttons found on the page
                    print("No 'Continue' buttons found on the page.")
                    break  # Exit the while loop

                print("URL did not change to a 'resume' page after clicking 'Continue' button.")

            if 'resume' not in current_url:
                print("Unable to reach a URL containing 'resume' after maximum attempts.")
                # Handle this case as needed; for example, return a failure
                return None, "Failed"

        # Initialize gpt_answer and application_status
        gpt_answer = None
        application_status = "Failed"

        # Step 4: Wait until the specific element on the new page has loaded
        try:
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "label[for$='-file-resume-input']"))
            )
            print("Page loaded")
            time.sleep(5)
        except Exception as e:
            print(f"Element not found in Step 4: {e}")
            # Continue to next step

        # Step 5: Select the radio button to upload the resume file
        try:
            label_for_radio = browser.find_element(By.CSS_SELECTOR, "label[for$='-file-resume-input']")
            ActionChains(browser).move_to_element(label_for_radio).click().perform()
            time.sleep(random.uniform(2.0, 3.0))  # Wait for the next page to load
            print("Radio button selected successfully!")
        except Exception as e:
            print(f"Element not found in Step 5: {e}")
            # Continue to next step

        # Step 6: Click the "CV options" button
        try:
            cv_options_button = browser.find_element(By.ID, 'menu-button--menu--1')
            ActionChains(browser).move_to_element(cv_options_button).click().perform()
            time.sleep(random.uniform(1.0, 2.0))
            print("CV options button clicked successfully!")
        except Exception as e:
            print(f"Element not found in Step 6: {e}")
            # Continue to next step

        # Step 7: Upload the resume file
        try:
            file_path = os.path.abspath(resume_file_name)  # Get the absolute path of the file
            file_input = browser.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(file_path)
            print(f"File {file_path} uploaded successfully!")
            time.sleep(random.uniform(3.0, 4.0))  # Wait for the next page to load
        except Exception as e:
            print(f"Element not found in Step 7: {e}")
            # Continue to next step

        # Step 8: Select the second radio button
        try:
            label_for_radio = browser.find_element(By.CSS_SELECTOR, "label[for$='-resume-private-input']")
            ActionChains(browser).move_to_element(label_for_radio).click().perform()
            time.sleep(random.uniform(2.0, 4.0))
            print("Second radio button selected successfully!")
        except Exception as e:
            print(f"Element not found in Step 8: {e}")
            # Continue to next step

        # Step 9: Click the "Save" button
        try:
            save_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='ResumePrivacyModal-SaveBtn']"))
            )
            browser.execute_script("arguments[0].scrollIntoView(true);", save_button)
            time.sleep(1)  # Optional wait for stability
            ActionChains(browser).move_to_element(save_button).click().perform()
            time.sleep(random.uniform(3.0, 4.0))
            print("Save button clicked successfully!")
        except Exception as e:
            print(f"Element not found in Step 9: {e}")
            # Continue to next step

        # Step 10: Process forms (assuming process_forms is defined elsewhere)
        try:
            gpt_answer, application_status = process_forms(browser)
        except Exception as e:
            print(f"Error during form processing in Step 10: {e}")
            # application_status remains "Failed"

        # Step 11: Close the new tab and switch back to the original window
        try:
            browser.switch_to.window(new_window)
            browser.close()
            browser.switch_to.window(original_window)
            time.sleep(random.uniform(0.5, 1.5))
            print("Application process completed.")
        except Exception as e:
            print(f"Error during window switching in Step 11: {e}")

        return gpt_answer, application_status


    except Exception as e:
        print(f"An error occurred: {e}")
        return None, "Failed"




def human_like_delay(min_delay=0.5, max_delay=2.0):
    time.sleep(random.uniform(min_delay, max_delay))

def human_like_typing(element, text):
    for char in text:
        element.send_keys(char)
        human_like_delay(0.05, 0.3)  # Randomized delay between keystrokes

def smooth_scroll_to_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)
    human_like_delay(1, 2)  # Wait for the scroll to complete



# Existing functions, updated to use human-like behavior

def extract_headings(driver):
    headings = []

    # Extract the main heading, like "Answer these questions from the employer"
    try:
        main_heading_element = driver.find_element(By.CSS_SELECTOR, ".ia-BasePage-heading")
        main_heading = main_heading_element.text.strip()
        if main_heading:
            headings.append(main_heading)
    except NoSuchElementException:
        pass

    # Extract sub-headings within the form, for example, "Referee 2"
    form_items = driver.find_elements(By.CSS_SELECTOR, ".ia-Questions-item")

    for item in form_items:
        # Skip items that contain input, textarea, or select fields
        if item.find_elements(By.CSS_SELECTOR, 'input, textarea, select'):
            continue

        try:
            # Try to extract the group heading text
            group_heading_element = item.find_element(By.CSS_SELECTOR, "label .css-gnfkuw")
            group_heading = group_heading_element.text.strip()
            if group_heading:
                headings.append(group_heading)
        except NoSuchElementException:
            continue

    return headings


def detect_form_fields(driver):
    # Extract the headings first
    headings = extract_headings(driver)

    # Existing code to detect inputs, textareas, and selects
    inputs = driver.find_elements(By.TAG_NAME, 'input')
    textareas = driver.find_elements(By.TAG_NAME, 'textarea')
    selects = driver.find_elements(By.TAG_NAME, 'select')

    form_fields = []
    radio_groups = {}  # To hold the grouped radio buttons

    def find_common_label(element):
        # Try to find the fieldset or div associated with this element
        try:
            parent_fieldset = element.find_element(By.XPATH, "./ancestor::fieldset")
            aria_labelledby = parent_fieldset.get_attribute('aria-labelledby')
            if aria_labelledby:
                question_label = driver.find_element(By.ID, aria_labelledby).text.strip()
                return question_label
        except NoSuchElementException:
            pass
        # First, try to find the closest parent fieldset with a legend
        try:
            parent_fieldset = element.find_element(By.XPATH, "./ancestor::fieldset")
            try:
                legend_element = parent_fieldset.find_element(By.TAG_NAME, 'legend')
                if legend_element:
                    return legend_element.text.strip()  # Return the legend as the question label
            except NoSuchElementException:
                pass
        except NoSuchElementException:
            pass

        # If no fieldset/legend found, try finding the closest div with a label or legend
        try:
            parent_div = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'ia-Questions-item')]")
            try:
                label_element = parent_div.find_element(By.TAG_NAME, 'legend')
                if label_element:
                    return label_element.text.strip()
            except NoSuchElementException:
                pass

            try:
                label_element = parent_div.find_element(By.TAG_NAME, 'label')
                if label_element:
                    return label_element.text.strip()
            except NoSuchElementException:
                pass
        except NoSuchElementException:
            pass

        return None  # Return None if no label is found

    # Iterate through inputs, textareas, and selects
    for element in inputs + textareas + selects:
        element_type = element.get_attribute('type')
        field_id = element.get_attribute("id") or element.get_attribute("name")

        if element_type == "radio" or element_type == "checkbox":
            # Group radio buttons based on name attribute
            radio_group = element.get_attribute('name')
            group_label = find_common_label(element)  # Find the common question label

            if radio_group not in radio_groups:
                radio_groups[radio_group] = {
                    "group_label": group_label,  # Assign the common question label
                    "options": []
                }

            # Add individual radio options to the group
            option_label = element.find_element(By.XPATH, f".//following-sibling::span").text.strip()
            radio_groups[radio_group]["options"].append({
                "id": field_id,
                "label": option_label
            })
        else:
            # Handle non-radio fields (text, selects, textareas)
            label = find_common_label(element)
            if label:
                form_fields.append({
                    "id": field_id,
                    "label": label,
                    "type": element_type
                })

    # Add the radio button groups to the form fields list
    for group_name, group_data in radio_groups.items():
        form_fields.append({
            "group": group_name,
            "label": group_data["group_label"],  # Use the common question label for the group
            "type": "radio",
            "options": group_data["options"]
        })

    # Add the headings to the top of the form fields
    if headings:
        form_fields.insert(0, {"headings": headings})

    print(f"Detected form fields with headings: {form_fields}")
    return form_fields


def send_to_openai(profile_description, form_fields):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        }

        # Modify the content to handle radio button groups, checkboxes, and dropdowns
        field_descriptions = []
        for field in form_fields:
            if "headings" in field:
                continue
            if field["type"] == "radio":
                # Describe radio groups as a set of options
                options = ", ".join([f"{opt['label']} (ID: {opt['id']})" for opt in field["options"]])
                field_descriptions.append(f"Radio group '{field['label']}' with options: {options}")
            elif field["type"] == "checkbox":
                # Describe checkboxes
                field_descriptions.append(f"Checkbox '{field['label']}' (ID: {field['id']})")
            elif field["type"] == "select-one":
                # Describe dropdowns
                field_descriptions.append(f"Dropdown '{field['label']}' (ID: {field['id']})")
            else:
                # For other fields, describe them normally
                field_descriptions.append(f"'{field['label']}' (ID: {field['id']})")

        fields_text = "\n".join(field_descriptions)

        data = {
            "model": config.gpt_model,  # Replace with the model you have access to
            "messages": [
                {"role": "system",
                 "content": "You are a helpful assistant that fills in form fields based on a profile."},
                {
                    "role": "user",
                    "content": f"""
                    Given the following profile: {profile_description}
                    Here are the form fields with labels and IDs: {fields_text}.
                    Fill the appropriate values for each field based on the provided profile description. 
                    - If its a text field or text area, output the answer normally as text.
                    - For checkboxes, provide "checked" or "unchecked" depending on whether it should be selected.
                    - For dropdowns, if the exact value is not available, select the most similar option.
                    - If no value is available do not output the id.
                    - If it is a radio button, select and output only one answer which is most suitable from the radio group answers so that it could be selected.
                    - Do not give no for any answer that except if it is stated above to answer No, if it's a yes or no question, regardless of the question, answer yes. Do not leave empty.
                    Skip answering optional questions.
                    Output only the id:value pair in a structured format, one per line.
                    """
                }
            ],
            "max_tokens": 1200,
            "temperature": 1.0
        }
        print(data)
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise an exception for HTTP errors
        message = response.json()['choices'][0]['message']['content'].strip()
        print(message)
        return message

    except requests.exceptions.RequestException as e:
        print(f"Error in OpenAI API call: {e}")
        return None

def autofill_fields(driver, form_fields, response_data):
    structured_response = {}

    # Parse the response and map it to field IDs
    for entry in response_data.split("\n"):
        try:
            if entry and ":" in entry:
                field_id, value = entry.split(":", 1)
                structured_response[field_id.strip()] = value.strip()
        except ValueError:
            print(f"Skipping malformed line in response: {entry}")
            continue  # Continue processing other lines even if one fails

    # Fill fields with values from the response
    for field in form_fields:
        if 'id' in field:
            field_id = field['id']
            field_type = field['type']

            if field_id in structured_response:
                value = structured_response[field_id]

                try:
                    if field_type == 'radio':
                        # Select the radio button based on the field ID from OpenAI response
                        radio_button = driver.find_element(By.ID, field_id)
                        if not radio_button.is_selected():
                            smooth_scroll_to_element(driver, radio_button)
                            ActionChains(driver).move_to_element(radio_button).click().perform()
                            print(f"Selected radio button {field_id} with label: {value}")
                        else:
                            print(f"Radio button {field_id} is already selected")

                    elif field_type == 'checkbox':
                        # Handle checkboxes
                        checkbox = driver.find_element(By.ID, field_id)
                        if value.lower() == "checked" and not checkbox.is_selected():
                            smooth_scroll_to_element(driver, checkbox)
                            ActionChains(driver).move_to_element(checkbox).click().perform()
                            print(f"Checked checkbox {field_id}")
                        elif value.lower() == "unchecked" and checkbox.is_selected():
                            smooth_scroll_to_element(driver, checkbox)
                            ActionChains(driver).move_to_element(checkbox).click().perform()
                            print(f"Unchecked checkbox {field_id}")

                    elif field_type == 'select-one':
                        # Handle dropdowns (select elements)
                        select_element = driver.find_element(By.ID, field_id)
                        select = Select(select_element)
                        smooth_scroll_to_element(driver, select_element)

                        # Get all options and try to select the closest match
                        options = [option.text for option in select.options]
                        if value in options:
                            select.select_by_visible_text(value)
                            print(f"Selected dropdown option {value} for {field_id}")
                        else:
                            # Find the most similar option if exact match isn't available
                            closest_match = get_close_matches(value, options, n=1)
                            if closest_match:
                                select.select_by_visible_text(closest_match[0])
                                print(f"Selected closest dropdown option {closest_match[0]} for {field_id}")
                            else:
                                print(f"No similar option found for {value} in dropdown {field_id}")

                    else:
                        # Handle text input, textarea, etc.
                        input_element = driver.find_element(By.ID, field_id)
                        existing_value = input_element.get_attribute("value")

                        if existing_value.strip():  # If there is an existing value, skip this field
                            print(f"Skipping field {field_id} because it already has a value: {existing_value}")
                        else:
                            smooth_scroll_to_element(driver, input_element)
                            input_element.clear()  # Clear existing value if any
                            human_like_typing(input_element, value)  # Human-like typing for the value
                            print(f"Filled field {field_id} with value: {value}")

                except NoSuchElementException:
                    print(f"Element with ID {field_id} not found on the page.")
                except Exception as e:
                    print(f"Failed to fill field {field_id}: {e}")

        # Handle radio button groups (unchanged from the previous implementation)
        elif 'group' in field and 'options' in field:
            group_name = field['group']
            options = field['options']

            for option in options:
                option_id = option['id']
                if option_id in structured_response:
                    value = structured_response[option_id]
                    try:
                        radio_button = driver.find_element(By.ID, option_id)
                        if not radio_button.is_selected():
                            smooth_scroll_to_element(driver, radio_button)
                            ActionChains(driver).move_to_element(radio_button).click().perform()
                            print(f"Selected radio button {option_id} with label: {value}")
                        else:
                            print(f"Radio button {option_id} is already selected")
                    except NoSuchElementException:
                        print(f"Radio button with ID {option_id} not found.")
                    except Exception as e:
                        print(f"Failed to select radio button {option_id}: {e}")
                    break  # Stop after finding the matching radio button


def extract_question_answer_pairs(form_fields, response_data):
    # Create a dictionary to map the form field ID to its label
    id_to_label = {}
    for field in form_fields:
        if 'id' in field:
            field_id = field['id']
            field_label = field['label']
            id_to_label[field_id] = field_label
        elif 'group' in field and 'options' in field:
            for option in field['options']:
                id_to_label[option['id']] = field['label']

    # Create a dictionary to map field IDs to answers
    answers = {}
    for entry in response_data.split("\n"):
        if entry and ":" in entry:
            field_id, answer = entry.split(":", 1)
            field_id = field_id.strip()
            answer = answer.strip()
            if field_id in id_to_label:
                question_label = id_to_label[field_id]
                answers[question_label] = answer

    return answers

def process_forms(driver):
    form_fields_storage = []
    forward_steps = 0
    application_status = "Failed"  # Default status
    response_data = None  # To store the OpenAI response
    accumulated_question_answer_pairs = {}  # To accumulate question and answer pairs across all requests
    processed_urls = set()  # To track processed URLs
    max_continue_attempts = 5  # Max attempts to press 'Continue' before marking as failed
    retry_attempts = 0  # To count the attempts to click the 'Continue' button
    openai_retry_done = False  # Flag to track if OpenAI retry was done once

    while True:
        try:
            current_url = driver.current_url
            print(f"Current URL: {current_url}")

            # Check if we've reached the retry limit
            if retry_attempts >= max_continue_attempts:
                print("Reached maximum retry limit for clicking 'Continue'. Marking as Failed.")
                application_status = "Failed"
                return accumulated_question_answer_pairs, application_status

            # If the current URL contains "question" and hasn't been processed yet
            if ("question" in current_url.lower() or "document" in current_url.lower())  and current_url not in processed_urls:
                print("The URL contains 'question'. Detecting form fields and filling them.")
                form_fields = detect_form_fields(driver)
                form_fields_storage.append(form_fields)

                # Send form fields to OpenAI for autofill
                profile_description = config.profile_answer_questions
                response_data = send_to_openai(profile_description, form_fields)

                if not response_data:
                    print("No response from OpenAI. Skipping autofill.")
                else:
                    # Extract and store question-answer pairs
                    extracted_pairs = extract_question_answer_pairs(form_fields, response_data)

                    # Merge the extracted pairs with accumulated pairs
                    accumulated_question_answer_pairs.update(extracted_pairs)
                    print(f"Accumulated Question-Answer Pairs: {accumulated_question_answer_pairs}")

                    # Autofill the form fields based on OpenAI response
                    autofill_fields(driver, form_fields, response_data)

                # Mark the current URL as processed immediately after filling the form
                processed_urls.add(current_url)

                # Reset retry attempts after successfully processing the question page
                retry_attempts = 0

            # Now, try to find and click 'Continue' buttons on the page
            continue_buttons = driver.find_elements(By.XPATH, "//button//span[text()='Continue']")
            continue_clicked = False

            if continue_buttons:
                # Get the current URL before clicking any 'Continue' button
                previous_url = current_url

                for button in continue_buttons:
                    try:
                        smooth_scroll_to_element(driver, button)
                        ActionChains(driver).move_to_element(button).click().perform()
                        print(f"Continue button clicked! (Step {forward_steps})")
                        forward_steps += 1
                        time.sleep(random.uniform(2.0, 3.0))  # Short wait after clicking

                        # Check if the URL has changed after clicking
                        current_url = driver.current_url
                        if current_url != previous_url:
                            print("URL has changed! Continue button clicked successfully.")
                            continue_clicked = True
                            retry_attempts = 0  # Reset retry attempts since click was successful
                            break
                        else:
                            # If URL hasn't changed and it's on a question page, retry OpenAI once
                            if ("question" in current_url.lower() or "document" in current_url.lower())  and not openai_retry_done:
                                print("URL has not changed. Retrying OpenAI once.")
                                openai_retry_done = True  # Only retry once
                                form_fields = detect_form_fields(driver)
                                response_data = send_to_openai(profile_description, form_fields)
                                if response_data:
                                    autofill_fields(driver, form_fields, response_data)
                                    extracted_pairs = extract_question_answer_pairs(form_fields, response_data)

                                    # Merge the extracted pairs with accumulated pairs
                                    accumulated_question_answer_pairs.update(extracted_pairs)
                                    print(
                                        f"Accumulated Question-Answer Pairs (Retry): {accumulated_question_answer_pairs}")
                                break
                            else:
                                print("URL has not changed, waiting 7 seconds before retrying.")
                                time.sleep(7)  # Wait for 7 seconds before retrying
                                retry_attempts += 1
                    except Exception as e:
                        print(f"Error pressing 'Continue' button, trying the next one")
                        retry_attempts += 1  # Increment retry attempts if the click fails

            # If no 'Continue' button is found
            if not continue_buttons:
                print("No 'Continue' button found. Checking for review page...")

                # # If no 'Continue' button is found, check if the current URL contains 'review'
                # if "review" in current_url.lower():
                #     application_status = "Success"
                #     print(f"Application status: {application_status}")  # Ensure status is printed
                #     return accumulated_question_answer_pairs, application_status

                    # Check for 'Continue applying' or 'Review your application' button before marking as failed
                alternate_buttons = driver.find_elements(By.XPATH,
                                                         "//button//span[text()='Continue applying' or text()='Review your application']")

                if alternate_buttons:
                    print("'Continue applying' or 'Review your application' button found. Attempting to click.")
                    previous_url = current_url  # Get the current URL before clicking
                    for button in alternate_buttons:
                        try:
                            smooth_scroll_to_element(driver, button)
                            ActionChains(driver).move_to_element(button).click().perform()
                            print("Continue applying or Review your application button clicked!")
                            time.sleep(random.uniform(2.0, 3.0))  # Short wait after clicking

                            # Check if the URL has changed
                            current_url = driver.current_url
                            if current_url != previous_url:
                                print("URL has changed! Button clicked successfully.")
                                retry_attempts = 0  # Reset retry attempts
                                break
                            else:
                                print("URL has not changed after clicking the button, retrying.")
                                time.sleep(7)
                                retry_attempts += 1
                        except Exception as e:
                            print(f"Error pressing the button: {e}")
                            retry_attempts += 1

                    continue  # Skip to next iteration after clicking 'Continue applying' or 'Review your application'

                # If no progress can be made, increase the retry attempts and try again
                retry_attempts += 1
                if retry_attempts >= max_continue_attempts:
                    print("No progress made after multiple attempts to click 'Continue'. Marking as Failed.")
                    application_status = "Failed"
                    return accumulated_question_answer_pairs, application_status

            # Wait after attempting to click a 'Continue' button, then recheck the page
            time.sleep(1)

            # If the new URL contains "question", process the form again, but ensure it hasn't been processed before
            if ("question" in current_url.lower() or "document" in current_url.lower())  and current_url not in processed_urls:
                print("New 'question' page detected. Processing again...")
                continue  # Restart the loop to process this new question page

            # If the new URL contains "review", set the application status as success
            if "review" in current_url.lower():
                # Check for 'Submit your application' button
                html_source = driver.page_source
                with open("Gautham - Answers.html", "w", encoding="utf-8") as f:
                    f.write(html_source)
                print("Page saved as 'Gautham - Answers.html'")
                submit_buttons = driver.find_elements(By.XPATH, "//button//span[text()='Submit your application']")
                if submit_buttons and config.final_apply_button.lower() == "yes":
                    print("Submit button found. Attempting to click.")
                    previous_url = current_url  # Get the current URL before clicking
                    for button in submit_buttons:
                        try:
                            smooth_scroll_to_element(driver, button)
                            ActionChains(driver).move_to_element(button).click().perform()
                            print("Submit button clicked!")
                            time.sleep(random.uniform(2.0, 3.0))  # Short wait after clicking
                            time.sleep(10)

                            # Check if the URL has changed
                            current_url = driver.current_url
                            if current_url != previous_url:
                                print("URL has changed! Submit Button clicked successfully.")
                                retry_attempts = 0  # Reset retry attempts
                                print(f"Submit button clicked! ")
                                application_status = "Success"
                                print(f"Application status: {application_status}")  # Ensure status is printed
                                return accumulated_question_answer_pairs, application_status
                                break
                            else:
                                print("URL has not changed after clicking the button, retrying.")
                                time.sleep(7)
                                retry_attempts += 1
                        except Exception as e:
                            print(f"Error pressing the button: {e}")
                            retry_attempts += 1

                    continue  # Skip to next iteration after clicking 'Continue applying' or 'Review your application'
                else:
                    "Submission turned off or No submit button"


        except NoSuchElementException:
            print("No 'Continue' buttons found on the page.")
            break

    print("Stored form field details:", form_fields_storage)
    print("Application status:", application_status)
    print("Accumulated Question-Answer Pairs: ", accumulated_question_answer_pairs)

    # Return the accumulated question-answer pairs and the application status
    return accumulated_question_answer_pairs, application_status

def move_html(job_title: str, job_id: str):
    try:
        current_resume = "Gautham - Answers.html"
        # Define the paths
        html_folder = config.submissions_folder
        os.makedirs(html_folder, exist_ok=True)

        new_html_name = f"{job_title} - {job_id}.html"
        new_html_path = os.path.join(html_folder, new_html_name)

        # Check if "Gautham - resume.docx" exists and rename it to the last job's title and ID
        if os.path.exists(current_resume):
            shutil.move(current_resume, new_html_path)
            print(f"Renamed template resume to {new_html_name} and moved it to {html_folder}")
            return new_html_path
    except:
        print("Move error or already file moved")
        return None
#
    # return form_fields_storage


# if __name__ == "__main__":
#     process_forms(driver)
