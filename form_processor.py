import time
import json
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from difflib import get_close_matches
from selenium.webdriver.support.ui import Select
import os
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import shutil
import config
import re

# Define your OpenAI API key here
OPENAI_API_KEY = config.api_key


# ----------------------------
# Small helper: normalize LLM output and keep colon-rich IDs intact
# ----------------------------
def normalize_openai_response(text: str) -> str:
    """
    Normalize LLM output to 'id:value' lines.
    - Strips code fences/backticks.
    - Accepts both 'id:value' and 'id::value'.
    - If a line looks like a radio OPTION ID (e.g., single-select-question-...-2),
      append ':selected' so downstream parsing is trivial.
    """
    if not text:
        return text

    radio_option_line = re.compile(r"^single-select-question-.*-\d+$")
    out = []
    for raw in text.strip().splitlines():
        s = raw.strip().strip("`")
        if not s or s.startswith("```") or s.lower().startswith("plaintext"):
            continue

        if radio_option_line.match(s):
            out.append(f"{s}:selected")
            continue

        # normalize double-colon to single for consistency
        if "::" in s:
            k, v = s.split("::", 1)
            out.append(f"{k.strip()}:{v.strip()}")
        elif ":" in s:
            out.append(s)
        else:
            # no value provided -> treat as toggle/selection
            out.append(f"{s}:selected")

    normalized = "\n".join(out)
    if normalized != text:
        print("Normalized OpenAI response to id:value pairs (radio-safe).")
    return normalized


# ----------------------------
# React-safe value setting helpers
# ----------------------------
def js_set_value(driver, element, value: str):
    driver.execute_script(
        """
        const el = arguments[0], val = arguments[1];
        if (!el) return;
        const setVal = (node, v) => {
          const last = node.value;
          node.value = v;
          const e1 = new Event('input', {bubbles:true});
          const e2 = new Event('change', {bubbles:true});
          node.dispatchEvent(e1);
          node.dispatchEvent(e2);
        };
        if ('value' in el) setVal(el, val);
        if (el.isContentEditable) {
          el.textContent = val;
          el.dispatchEvent(new Event('input', {bubbles:true}));
          el.dispatchEvent(new Event('change', {bubbles:true}));
        }
        """,
        element, value
    )

def ensure_value(driver, element, value: str):
    current = (element.get_attribute("value") or "").strip()
    if current != (value or "").strip():
        js_set_value(driver, element, value)

def human_like_delay(min_delay=0.5, max_delay=2.0):
    time.sleep(random.uniform(min_delay, max_delay))

def human_like_typing(element, text):
    try:
        element.clear()
    except Exception:
        pass
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.03, 0.08))

def smooth_scroll_to_element(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'instant', block: 'center' });", element)
    except Exception:
        pass
    human_like_delay(0.2, 0.5)


# ----------------------------
# Application router and core flow (unchanged except for logs)
# ----------------------------
def apply_for_job(browser, internal_apply_button, resume_file_name):
    """
    Opens the internal apply flow in a new tab/window and runs a URL-driven state machine
    until success/fail.
    """
    try:
        original_window = browser.current_window_handle
        original_windows = set(browser.window_handles)

        ActionChains(browser).move_to_element(internal_apply_button).click().perform()
        time.sleep(random.uniform(0.5, 1.5))
        print("Internal apply link clicked")

        new_window = WebDriverWait(browser, 10).until(
            lambda d: [w for w in d.window_handles if w not in original_windows][0]
        )
        browser.switch_to.window(new_window)
        print("Switched to the new window")
        time.sleep(random.uniform(2.0, 3.0))

        # >>> pass resume path into process_forms <<<
        gpt_answer, application_status = process_forms(browser, os.path.abspath(resume_file_name))

        try:
            browser.switch_to.window(new_window)
            browser.close()
        except Exception as e:
            print(f"[Router] Could not close new window: {e}")
        try:
            browser.switch_to.window(original_window)
        except Exception as e:
            print(f"[Router] Could not switch back to original window: {e}")

        print("Application process completed.")
        return gpt_answer, application_status

    except Exception as e:
        print(f"An error occurred in apply_for_job: {e}")
        return None, "Failed"




def click_review_your_application_button(browser):
    current_url = browser.current_url
    if 'documents' in current_url.lower():
        print("URL contains 'documents'. Attempting to click 'Review your application' button.")
        review_buttons = browser.find_elements(By.XPATH, "//button//span[text()='Review your application']")
        if review_buttons:
            previous_url = current_url
            for button in review_buttons:
                try:
                    smooth_scroll_to_element(browser, button)
                    ActionChains(browser).move_to_element(button).click().perform()
                    print("Review your application button clicked.")
                    time.sleep(random.uniform(2.0, 3.0))
                    # Check if URL has changed
                    current_url = browser.current_url
                    if current_url != previous_url:
                        print("URL has changed after clicking 'Review your application' button.")
                        return True
                    else:
                        print("URL did not change after clicking 'Review your application' button.")
                except Exception as e:
                    print(f"Could not click 'Review your application' button: {e}")
        else:
            print("No 'Review your application' buttons found on the page.")
    else:
        print("URL does not contain 'documents'.")
    return False



# ----------------------------
# FIELD DETECTION (rewritten for Indeed)
# ----------------------------

def _label_text_for_id(driver, field_id: str) -> str:
    # 1) label[for=<id>]
    try:
        lbl = driver.find_element(By.XPATH, f"//label[@for={repr(field_id)}]")
        t = (lbl.text or "").strip()
        if t:
            return t
    except Exception:
        pass

    # 2) nearest container label
    try:
        el = driver.find_element(By.ID, field_id)
        container = el.find_element(By.XPATH, "./ancestor::*[contains(@class,'ia-Questions-item')][1]")
        lbl = container.find_element(By.XPATH, ".//label")
        t = (lbl.text or "").strip()
        if t:
            return t
    except Exception:
        pass

    return field_id  # fallback

def detect_form_fields(driver):
    """
    Robustly detect Indeed question fields:
      - Text inputs: id starts with 'text-question-input-'
      - Textareas: id starts with 'rich-text-question-input-'
      - Selects: id starts with 'single-select-question-' (rare on Indeed)
      - Radios: inputs type=radio id like 'single-select-question-:rn:-0' grouped by name
    """
    form_fields = []

    # Text inputs
    for inp in driver.find_elements(By.XPATH, "//input[starts-with(@id,'text-question-input-')]"):
        fid = inp.get_attribute("id") or ""
        if not fid:
            continue
        form_fields.append({
            "id": fid,
            "label": _label_text_for_id(driver, fid),
            "type": "text",
        })

    # Textareas
    for ta in driver.find_elements(By.XPATH, "//textarea[starts-with(@id,'rich-text-question-input-')]"):
        fid = ta.get_attribute("id") or ""
        if not fid:
            continue
        form_fields.append({
            "id": fid,
            "label": _label_text_for_id(driver, fid),
            "type": "textarea",
        })

    # Select (if present)
    for sel in driver.find_elements(By.XPATH, "//select[starts-with(@id,'single-select-question-')]"):
        fid = sel.get_attribute("id") or ""
        if not fid:
            continue
        opts = []
        for opt in sel.find_elements(By.TAG_NAME, "option"):
            opts.append({
                "id": opt.get_attribute("id") or "",
                "label": (opt.get_attribute("label") or opt.text or "").strip(),
                "value": opt.get_attribute("value") or "",
            })
        form_fields.append({
            "id": fid,
            "label": _label_text_for_id(driver, fid),
            "type": "select-one",
            "options": opts,
        })

    # Radios: group by name
    radios = driver.find_elements(By.XPATH, "//input[@type='radio' and starts-with(@id,'single-select-question-')]")
    by_group = {}
    for rb in radios:
        name = rb.get_attribute("name") or ""
        by_group.setdefault(name, []).append(rb)

    for group_name, rbs in by_group.items():
        options = []
        group_label = ""
        for rb in rbs:
            rbid = rb.get_attribute("id") or ""
            opt_label = ""
            try:
                lbl = driver.find_element(By.XPATH, f"//label[@for={repr(rbid)}]//span[normalize-space()]")
                opt_label = (lbl.text or "").strip()
            except Exception:
                pass
            options.append({"id": rbid, "label": opt_label})

            # compute group label once via known pattern
            if not group_label and rbid:
                try:
                    # rbid like single-select-question-:rn:-0 -> prefix "single-select-question-:rn:"
                    prefix = rbid.rsplit("-", 1)[0] + ":"
                    label_id = "single-select-question-label-" + prefix
                    gl = driver.find_element(By.ID, label_id)
                    group_label = (gl.text or "").strip()
                except Exception:
                    pass

        # final fallback for group label
        if not group_label:
            try:
                container = rbs[0].find_element(By.XPATH, "./ancestor::*[contains(@class,'ia-Questions-item')][1]")
                gl = container.find_element(By.XPATH, ".//label")
                group_label = (gl.text or "").strip()
            except Exception:
                group_label = group_name

        form_fields.append({
            "group": group_name,
            "label": group_label,
            "type": "radio",
            "options": options
        })

    print(f"Detected form fields with headings: {form_fields}")
    return form_fields


# ----------------------------
# OpenAI call (truthful, radio by OPTION ID)
# ----------------------------
def send_to_openai(profile_description, form_fields):
    """
    Calls OpenAI Responses API and returns a dict:
      {"answers":[{"id": <field_id_or_radio_option_id>, "value": <string|boolean|number>}, ...]}
    Uses Responses API's text.format=json_schema (with required 'name' at text.format level).
    """
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        # Build compact context + allowed ID enum (include text/select ids and all radio OPTION ids)
        ctx_fields = []
        id_enum = []
        for f in form_fields:
            ftype = f.get("type")
            base = {
                "id": f.get("id") or f.get("group") or "",
                "type": ftype,
                "label": f.get("label", ""),
            }
            if ftype in ("text", "textarea", "select-one"):
                if f.get("id"):
                    id_enum.append(f["id"])
                if ftype == "select-one":
                    base["options"] = [
                        (o.get("label") or "").strip()
                        for o in f.get("options", [])
                        if (o.get("label") or "").strip()
                    ]
            elif ftype == "radio":
                base["options"] = [
                    {"id": o.get("id", ""), "label": (o.get("label") or "").strip()}
                    for o in f.get("options", [])
                ]
                for o in f.get("options", []):
                    if o.get("id"):
                        id_enum.append(o["id"])
            ctx_fields.append(base)

        # dedupe / drop empties
        id_enum = [s for s in dict.fromkeys([s for s in id_enum if s])]

        # Strict JSON schema — NOTE: name/strict/schema live directly under text.format
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["answers"],
            "properties": {
                "answers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "value"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "enum": id_enum if id_enum else ["__none__"]
                            },
                            "value": {
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "boolean"},
                                    {"type": "number"}
                                ]
                            }
                        }
                    }
                }
            }
        }

        system = (
            "You fill job application forms truthfully from the given profile. "
            "Return ONLY valid JSON that matches the provided schema."
        )
        user = (
            "PROFILE:\n"
            f"{profile_description}\n\n"
            "FORM FIELDS CONTEXT (IDs, labels, options):\n"
            f"{json.dumps(ctx_fields, ensure_ascii=False)}\n\n"
            "INSTRUCTIONS:\n"
            "- Produce JSON with 'answers': [{id, value}, ...].\n"
            "- TEXT/TEXTAREA: id = field id; value = short truthful answer.\n"
            "- DROPDOWN: id = select id; value = one of the VISIBLE option labels from context.\n"
            "- RADIO: choose exactly one option; use that OPTION's id as 'id'. "
            "  Value can be true/'selected'/or the option label (we ignore it and use id).\n"
            "- If the answer to a question is not available in the profile, make up a suitable answer based on the profile details."
        )

        payload = {
            "model": config.gpt_model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "FormAnswers",     # <-- REQUIRED at this level
                    "strict": True,            # <-- REQUIRED at this level
                    "schema": schema           # <-- REQUIRED at this level
                },
                "verbosity": "low"
            },
            "reasoning": {"effort": "low"},
            "max_output_tokens": 1200,
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
            return None

        j = resp.json()
        print(f"[GPT] model={j.get('model')} status={j.get('status')} usage={j.get('usage')}")

        # Extract structured JSON
        result = None
        ot = (j.get("output_text") or "").strip()
        if ot.startswith("{") or ot.startswith("["):
            try:
                result = json.loads(ot)
            except Exception:
                result = None

        if result is None:
            # Fallback walk
            for item in j.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            txt = (c.get("text") or "").strip()
                            if txt.startswith("{") or txt.startswith("["):
                                try:
                                    result = json.loads(txt)
                                except Exception:
                                    pass
                    if result is not None:
                        break

        if not isinstance(result, dict) or "answers" not in result:
            print("[GPT] No structured JSON found or missing 'answers'.")
            return None

        print(f"[GPT] output_json: {json.dumps(result, ensure_ascii=False)[:800]}...")
        return result

    except requests.Timeout:
        print("[GPT] Request timeout.")
        return None
    except Exception as e:
        print(f"[GPT] Exception: {e}")
        return None






# ----------------------------
# Autofill
# ----------------------------
def autofill_fields(driver, form_fields, response_json):
    """
    - Consumes JSON: {"answers":[{"id":..., "value":...}, ...]}
    - Skip filling any control that already has a value/selection.
    - Dropdown: case-insensitive exact match; else closest match.
    - Radio: id must be the OPTION id; value is ignored, presence is enough.
    """
    # ---- convert JSON to a mapping {id -> value_str} ----
    def answers_map(j):
        out = {}
        if isinstance(j, dict) and isinstance(j.get("answers"), list):
            for a in j["answers"]:
                fid = str(a.get("id", "")).strip()
                val = a.get("value", "")
                if isinstance(val, bool):
                    val = "true" if val else "false"
                elif val is None:
                    val = ""
                else:
                    val = str(val)
                if fid:
                    out[fid] = val
        return out

    structured = answers_map(response_json)

    # ---- helpers ----
    def input_has_value(el) -> bool:
        v = (el.get_attribute("value") or "").strip()
        if not v and el.tag_name.lower() == "textarea":
            v = (el.text or "").strip()
        return bool(v)

    def select_has_value(el) -> bool:
        try:
            sel = Select(el)
            opt = sel.first_selected_option
            if opt is None:
                return False
            val = (opt.get_attribute("value") or "").strip()
            return bool(val)  # empty value = placeholder
        except Exception:
            return False

    from difflib import get_close_matches, SequenceMatcher
    def pick_best_label(target: str, labels: list[str]) -> str | None:
        if not labels:
            return None
        t = (target or "").strip()
        if not t:
            return None
        low = [s.lower() for s in labels]
        t_low = t.lower()
        if t_low in low:
            return labels[low.index(t_low)]
        close = get_close_matches(t_low, low, n=1, cutoff=0.6)
        if close:
            return labels[low.index(close[0])]
        best = max(labels, key=lambda s: SequenceMatcher(None, s.lower(), t_low).ratio())
        return best

    # ---- fill text/textarea/select ----
    for field in form_fields:
        fid = field.get("id")
        ftype = field.get("type")

        # TEXT/TEXTAREA/SELECT expect their own field id in answers
        if not fid or ftype not in ("text", "textarea", "select-one"):
            continue

        value = structured.get(fid)
        if value is None:
            continue

        try:
            if ftype == "select-one":
                el = driver.find_element(By.ID, fid)
                if select_has_value(el):
                    print(f"Skip select {fid}: already has a selection.")
                    continue
                sel = Select(el)
                smooth_scroll_to_element(driver, el)

                option_pairs = [(o.text.strip(), (o.get_attribute("value") or "").strip()) for o in sel.options]
                valid_labels = [txt for (txt, val) in option_pairs if val != "" and txt]

                chosen = pick_best_label(value, valid_labels)
                if chosen:
                    sel.select_by_visible_text(chosen)
                    print(f"Selected dropdown option '{chosen}' for {fid}")
                else:
                    print(f"No similar option found for '{value}' in dropdown {fid}")
                human_like_delay(1, 3)

            elif ftype in ("text", "textarea"):
                el = driver.find_element(By.ID, fid)
                if input_has_value(el):
                    print(f"Skip {ftype} {fid}: already has a value.")
                    continue
                smooth_scroll_to_element(driver, el)
                try:
                    el.click()
                except Exception:
                    pass
                human_like_delay(0.2, 0.5)
                human_like_typing(el, value)
                ensure_value(driver, el, value)
                print(f"Filled field {fid} with value: {value}")
                human_like_delay(1, 3)

        except NoSuchElementException:
            print(f"Element with ID {fid} not found on the page.")
        except Exception as e:
            print(f"Failed to fill field {fid}: {e}")

    # ---- handle radio groups (presence of option id in answers triggers selection) ----
    for field in form_fields:
        if field.get("type") != "radio" or "options" not in field:
            continue

        # Skip group if any option is already selected
        already_selected = False
        for o in field["options"]:
            try:
                rb = driver.find_element(By.ID, o["id"])
                if rb.is_selected():
                    already_selected = True
                    break
            except Exception:
                pass
        if already_selected:
            print(f"Skip radio group '{field.get('label','')}' (already selected).")
            continue

        # Find any option id present in structured answers
        selected_option_id = None
        for o in field["options"]:
            if o["id"] in structured:
                selected_option_id = o["id"]
                break

        if selected_option_id:
            try:
                rb = driver.find_element(By.ID, selected_option_id)
                if not rb.is_selected():
                    smooth_scroll_to_element(driver, rb)
                    ActionChains(driver).move_to_element(rb).click().perform()
                print(f"Selected radio button {selected_option_id}")
                human_like_delay(1, 3)
            except Exception as e:
                print(f"Failed to select radio button {selected_option_id}: {e}")
        else:
            print(f"No matching radio option resolved for group '{field.get('label','')}'.")




def extract_question_answer_pairs(form_fields, response_json):
    """
    Build {question_label: answer_text} from the JSON answers.
    For radios, map the selected OPTION id back to its visible label.
    """
    # Map field/option ids -> question labels, and option ids -> option labels
    id_to_question = {}
    option_id_to_label = {}
    for field in form_fields:
        if 'id' in field:
            id_to_question[field['id']] = field.get('label', '')
        if field.get('type') == 'radio':
            qlabel = field.get('label', '')
            for opt in field.get('options', []):
                oid = opt.get('id', '')
                option_id_to_label[oid] = (opt.get('label') or '').strip()
                id_to_question[oid] = qlabel  # option id maps to the group label

    answers = {}
    if isinstance(response_json, dict) and isinstance(response_json.get("answers"), list):
        for a in response_json["answers"]:
            fid = str(a.get("id", "")).strip()
            val = a.get("value", "")
            if fid in id_to_question:
                qlabel = id_to_question[fid]
                # For radios, prefer the option's visible label
                if fid in option_id_to_label:
                    answers[qlabel] = option_id_to_label[fid]
                else:
                    if isinstance(val, bool):
                        val = "Yes" if val else "No"
                    elif val is None:
                        val = ""
                    else:
                        val = str(val)
                    answers[qlabel] = val
    return answers

def click_cv_options_and_upload(driver, resume_file_path: str, timeout: int = 15) -> bool:
    """
    Clicks CV options -> 'Upload a different file' -> uploads `resume_file_path`.
    Sends ESC after upload to close any picker/overlay.
    Returns True on apparent success.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import os, time, random

    try:
        # 1) Open the CV options menu
        cv_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='ResumeOptionsMenu']"))
        )
        ActionChains(driver).move_to_element(cv_btn).click().perform()
        time.sleep(random.uniform(0.4, 0.9))
        print("[Resume] CV options opened")

        # 2) Click "Upload a different file"
        upload_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='ResumeOptionsMenu-upload']")))
        ActionChains(driver).move_to_element(upload_btn).click().perform()
        time.sleep(random.uniform(0.4, 0.9))
        print("[Resume] 'Upload a different file' clicked")

        # 3) Send the file to the <input type=file>
        file_input = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        file_input.send_keys(os.path.abspath(resume_file_path))
        print(f"[Resume] File uploaded -> {os.path.abspath(resume_file_path)}")
        time.sleep(random.uniform(1.2, 2.0))

        # 4) Dismiss any native/overlay picker (if shown) with ESC
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(random.uniform(0.3, 0.7))
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            print("[Resume] ESC sent to close upload dialog/overlay")
            time.sleep(random.uniform(0.3, 0.7))
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"[Resume] click_cv_options_and_upload failed: {e}")
        return False




# ----------------------------
# Main processing loop
# ----------------------------
def process_forms(driver, resume_file_path):
    """
    URL-driven state machine with JSON answers:
      - Any 'resume' URL: attempt resume actions once per URL.
      - If URL has 'privacy-settings', select the opt-out radio ('Employers can’t find you on Indeed') then Continue.
      - Questions/documents/review logic unchanged.
    """
    def url_state(url: str) -> str:
        u = url.lower()
        if "review" in u: return "review"
        if "question" in u or "questions" in u: return "questions"
        if "resume" in u: return "resume"
        if "documents" in u: return "documents"
        return "other"

    def click_any_continue_variant() -> bool:
        start = driver.current_url
        buttons = driver.find_elements(By.XPATH, "//button[.//span[normalize-space()='Continue']]")
        if not buttons:
            buttons = driver.find_elements(
                By.XPATH,
                "//button//span[normalize-space()='Continue applying' or normalize-space()='Review your application']"
            )
        if not buttons:
            return False
        for btn in buttons:
            try:
                smooth_scroll_to_element(driver, btn)
                ActionChains(driver).move_to_element(btn).click().perform()
                print("[Router] Clicked a continue-like button")
                time.sleep(random.uniform(3.0, 5.0))
                if driver.current_url != start:
                    print("[Router] URL changed after continue click")
                    return True
            except Exception as e:
                print(f"[Router] Continue click failed on a button: {e}")
        return False

    form_fields_storage = []
    accumulated_question_answer_pairs = {}
    application_status = "Failed"

    processed_urls = set()
    resume_urls_attempted = set()
    max_stagnant = 10
    stagnant = 0
    openai_retry_done = False

    while True:
        current_url = driver.current_url
        state = url_state(current_url)
        print(f"[Router] State={state} -> {current_url}")

        if stagnant >= max_stagnant:
            print("[Router] No progress after multiple attempts. Marking as Failed.")
            return accumulated_question_answer_pairs, "Failed"

        # ===== RESUME (per-URL) =====
        if state == "resume" and current_url not in resume_urls_attempted:
            resume_urls_attempted.add(current_url)

            # If this resume URL is the privacy settings page, handle opt-out and continue
            if "privacy-settings" in current_url.lower():
                try:
                    print("[Resume] Privacy settings detected – selecting 'Employers can’t find you on Indeed'")
                    optout_label = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "label[data-testid='privacy-settings-optout-label']"))
                    )
                    smooth_scroll_to_element(driver, optout_label)
                    ActionChains(driver).move_to_element(optout_label).click().perform()
                    time.sleep(random.uniform(0.6, 1.2))
                    print("[Resume] Opt-out selected")

                except Exception as e:
                    print(f"[Resume] Could not select privacy opt-out: {e}")

                # Continue after privacy choice
                if not click_any_continue_variant():
                    stagnant += 1
                else:
                    stagnant = 0
                time.sleep(random.uniform(1.2, 2.0))
                continue

            # Otherwise: normal resume page – try CV options -> upload
            try:
                # Best-effort wait for the CV options button (may not exist on every resume page)
                try:
                    WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='ResumeOptionsMenu']"))
                    )
                    print("Page loaded (resume step)")
                    human_like_delay(0.8, 1.6)
                except Exception:
                    print("[Resume] 'CV options' button not found quickly; will still try upload if present.")

                # Attempt upload if menu exists
                try:
                    cv_btns = driver.find_elements(By.CSS_SELECTOR, "button[data-testid='ResumeOptionsMenu']")
                    if cv_btns:
                        ok = click_cv_options_and_upload(driver, resume_file_path, timeout=15)
                        if ok:
                            # Optional: set Private and save if the modal appears
                            try:
                                privacy_label = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "label[for$='-resume-private-input']"))
                                )
                                smooth_scroll_to_element(driver, privacy_label)
                                ActionChains(driver).move_to_element(privacy_label).click().perform()
                                print("[Resume] Privacy radio selected (Private)")
                                human_like_delay(0.4, 0.9)

                                save_button = WebDriverWait(driver, 8).until(
                                    EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='ResumePrivacyModal-SaveBtn']"))
                                )
                                driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
                                time.sleep(0.2)
                                ActionChains(driver).move_to_element(save_button).click().perform()
                                print("[Resume] Privacy saved")
                                human_like_delay(0.8, 1.4)
                            except Exception:
                                pass
                    else:
                        print("[Resume] No CV options UI on this resume page; skipping upload here.")
                except Exception as e:
                    print(f"[Resume] Upload attempt failed: {e}")

                # Try to move forward after resume step
                if not click_any_continue_variant():
                    stagnant += 1
                else:
                    stagnant = 0
                time.sleep(random.uniform(1.5, 2.5))
            except Exception as e:
                print(f"[Resume] Unexpected error on resume page: {e}")
            continue

        # ===== QUESTIONS =====
        if state == "questions" and current_url not in processed_urls:
            print("[Questions] Detecting fields...")
            time.sleep(random.uniform(3.0, 4.0))
            form_fields = detect_form_fields(driver)
            form_fields_storage.append(form_fields)

            profile_description = config.profile_answer_questions
            response_json = send_to_openai(profile_description, form_fields)

            if not response_json:
                print("[Questions] No response from OpenAI (JSON). Skipping autofill this round.")
                stagnant += 1
            else:
                extracted_pairs = extract_question_answer_pairs(form_fields, response_json)
                accumulated_question_answer_pairs.update(extracted_pairs)
                print(f"[Questions] Accumulated Q/A: {accumulated_question_answer_pairs}")
                autofill_fields(driver, form_fields, response_json)
                stagnant = 0
                openai_retry_done = False

            processed_urls.add(current_url)

            if not click_any_continue_variant():
                time.sleep(random.uniform(2.0, 3.0))
                if not openai_retry_done:
                    print("[Questions] URL unchanged. Retrying OpenAI once (JSON).")
                    openai_retry_done = True
                    form_fields = detect_form_fields(driver)
                    response_json = send_to_openai(config.profile_answer_questions, form_fields)
                    if response_json:
                        autofill_fields(driver, form_fields, response_json)
                        extracted_pairs = extract_question_answer_pairs(form_fields, response_json)
                        accumulated_question_answer_pairs.update(extracted_pairs)
                        print(f"[Questions] Accumulated Q/A (Retry): {accumulated_question_answer_pairs}")
                        stagnant = 0
                    else:
                        stagnant += 1
                else:
                    stagnant += 1
            time.sleep(1)
            continue

        # ===== DOCUMENTS =====
        if state == "documents" and current_url not in processed_urls:
            print("[Documents] Trying 'Review your application'...")
            review_clicked = click_review_your_application_button(driver)
            processed_urls.add(current_url)
            stagnant = 0 if review_clicked else stagnant + 1
            time.sleep(1)
            continue

        # ===== REVIEW =====
        if state == "review":
            html_source = driver.page_source
            with open("Gautham - Answers.html", "w", encoding="utf-8") as f:
                f.write(html_source)
            print("Page saved as 'Gautham - Answers.html'")

            submit_buttons = driver.find_elements(By.XPATH, "//button//span[normalize-space()='Submit your application']")
            if submit_buttons and config.final_apply_button.lower() == "yes":
                print("[Review] Submit button found. Attempting to click.")
                prev = driver.current_url
                for button in submit_buttons:
                    try:
                        smooth_scroll_to_element(driver, button)
                        ActionChains(driver).move_to_element(button).click().perform()
                        print("[Review] Submit clicked")
                        time.sleep(random.uniform(2.0, 3.0))
                        time.sleep(5)
                        if driver.current_url != prev:
                            application_status = "Success"
                            print(f"Application status: {application_status}")
                            return accumulated_question_answer_pairs, application_status
                    except Exception as e:
                        print(f"[Review] Error pressing submit: {e}")
                print("[Review] Submission skipped or failed. Returning partial.")
                return accumulated_question_answer_pairs, "Review"
            else:
                print("[Review] Submission turned off or button missing.")
                return accumulated_question_answer_pairs, "Review"

        # ===== OTHER =====
        moved = click_any_continue_variant()
        stagnant = 0 if moved else stagnant + 1
        time.sleep(random.uniform(2.0, 3.0))








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

    # return form_fields_storage
