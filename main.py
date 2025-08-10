import argparse
import os
import sys
import time
from pathlib import Path
from getpass import getpass
import subprocess
import re
import json

from dotenv import load_dotenv, set_key
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchWindowException


ENV_FILE_PATH = Path(__file__).resolve().parent / ".env"


def load_env_values() -> dict:
    load_dotenv(dotenv_path=ENV_FILE_PATH)
    env_values = {
        "LI_AT": os.getenv("LI_AT") or "",
        "PROFILE_URL": os.getenv("PROFILE_URL") or "",
    }
    return env_values


def prompt_and_save_missing_values(existing: dict) -> dict:
    updated = dict(existing)

    if not updated.get("LI_AT"):
        print("Enter your LinkedIn session cookie 'li_at' (input hidden):")
        try:
            li_at_value = getpass(prompt="LI_AT: ")
        except Exception:
            # Fallback for environments where getpass is not supported
            li_at_value = input("LI_AT (visible input fallback): ")
        if not li_at_value:
            print("Error: LI_AT cannot be empty.")
            sys.exit(1)
        set_key(str(ENV_FILE_PATH), "LI_AT", li_at_value)
        updated["LI_AT"] = li_at_value

    # No longer persist PROFILE_URL here; we'll ask at runtime each run

    return updated


def ensure_env_values(
    reset: bool = False,
) -> dict:
    if reset and ENV_FILE_PATH.exists():
        try:
            ENV_FILE_PATH.unlink()
            print("Reset: removed existing .env file. You'll be prompted for fresh values.")
        except OSError as exc:
            print(f"Warning: could not delete .env ({exc}). We'll overwrite values instead.")

    # Ensure .env exists so set_key has a file to write to
    if not ENV_FILE_PATH.exists():
        ENV_FILE_PATH.touch()

    env_values = load_env_values()
    env_values = prompt_and_save_missing_values(env_values)
    return env_values


def build_driver() -> uc.Chrome:
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-infobars")

    # On macOS, prefer the standard Chrome binary if present
    mac_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(mac_chrome):
        try:
            chrome_options.binary_location = mac_chrome
        except Exception:
            pass

    major_version = get_chrome_major_version()
    try:
        driver = uc.Chrome(options=chrome_options, version_main=major_version) if major_version else uc.Chrome(options=chrome_options)
        # Ensure window is large if start-maximized is ignored
        try:
            driver.set_window_size(1400, 900)
        except Exception:
            pass
        # Give Chrome a moment to stabilize
        time.sleep(0.5)
        return driver
    except WebDriverException as exc:
        print(f"Failed to launch Chrome: {exc}")
        sys.exit(2)

def get_chrome_major_version() -> int | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "google-chrome",
        "chromium",
        "chrome",
    ]
    for cmd in candidates:
        try:
            out = subprocess.check_output([cmd, "--version"], stderr=subprocess.STDOUT, text=True).strip()
            m = re.search(r"(\d+)\.", out)
            if m:
                return int(m.group(1))
        except Exception:
            continue
    return None


def add_linkedin_cookie(driver: uc.Chrome, li_at_value: str) -> None:
    driver.get("https://www.linkedin.com/")
    # Give the browser a moment to establish the domain context
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Clear any existing cookies to avoid conflicts
    try:
        driver.delete_all_cookies()
    except Exception:
        pass

    cookie_dict = {
        "name": "li_at",
        "value": li_at_value,
        "domain": ".linkedin.com",
        "path": "/",
        "secure": True,
        "httpOnly": True,
    }
    try:
        driver.add_cookie(cookie_dict)
    except WebDriverException as exc:
        # Some drivers can be picky about optional keys
        try:
            minimal_cookie = {"name": "li_at", "value": li_at_value}
            driver.add_cookie(minimal_cookie)
        except Exception as exc2:
            print(f"Could not set LinkedIn cookie: {exc2}")
            raise exc


def is_logged_in(driver: uc.Chrome) -> bool:
    current_url = driver.current_url or ""
    if any(token in current_url for token in ["/login", "/checkpoint/", "/authwall"]):
        return False
    # Heuristic: When logged in, feed loads and URL typically contains '/feed' or stays on a non-login page
    return True


def validate_session_with_cookie(driver: uc.Chrome) -> bool:
    try:
        driver.get("https://www.linkedin.com/feed/")
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1.0)
        return is_logged_in(driver)
    except TimeoutException:
        return False


    


def navigate_to_profile(driver: uc.Chrome, profile_url: str) -> None:
    try:
        driver.get(profile_url)
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Briefly keep the window open
        time.sleep(5)
    except TimeoutException:
        print("Timed out waiting for profile page to load. The page may still be open in the browser.")


def _get_text_safe(element):
    try:
        return element.text.strip()
    except Exception:
        return ""


def _first_or_none(elements):
    return elements[0] if elements else None


def slow_scroll(driver: uc.Chrome, steps: int = 6, delay_sec: float = 0.5) -> None:
    for _ in range(steps):
        try:
            driver.execute_script("window.scrollBy(0, 1000);")
        except Exception:
            pass
        time.sleep(delay_sec)


def scrape_profile(driver: uc.Chrome, profile_url: str) -> dict:
    data: dict = {
        "full_name": None,
        "linkedin_url": profile_url,
        "education": {"major": None, "minor": None},
        "experiences": [],
    }

    # Name
    try:
        name_el = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        data["full_name"] = _get_text_safe(name_el)
    except TimeoutException:
        print("Could not locate profile name <h1>.")

    # Ensure content is loaded
    slow_scroll(driver)

    # Education: attempt to parse major/minor from the first entry
    try:
        edu_section = _first_or_none(
            driver.find_elements(By.XPATH, "//section[.//h2[contains(normalize-space(.), 'Education')]]")
        )
        if edu_section:
            first_item = _first_or_none(edu_section.find_elements(By.XPATH, ".//li"))
            if first_item:
                # Collect relevant text parts
                text_bits = [t for t in _get_text_safe(first_item).split("\n") if t.strip()]
                joined = " | ".join(text_bits)
                major = None
                minor = None
                # Heuristics: look for 'Minor' and split on commas / pipes
                if "Minor" in joined:
                    # e.g., "Bachelor of Science, Computer Science | Minor in Mathematics"
                    parts = re.split(r"\||,", joined)
                    for p in parts:
                        p_stripped = p.strip()
                        if p_stripped.lower().startswith("minor"):
                            minor = p_stripped
                        else:
                            # Take the first part that looks like a subject as major
                            if major is None and any(k in p_stripped.lower() for k in ["science", "arts", "engineering", "computer", "business", "economics", "biology", "mathematics", "design", "studies", "degree", "bachelor", "master"]):
                                major = p_stripped
                else:
                    # Attempt a simpler split: degree, major
                    m = re.search(r",\s*([^|]+)", joined)
                    if m:
                        major = m.group(1).strip()

                data["education"]["major"] = major
                data["education"]["minor"] = minor
    except Exception:
        pass

    # Experience section
    try:
        exp_section = _first_or_none(
            driver.find_elements(By.XPATH, "//section[.//h2[contains(normalize-space(.), 'Experience')]]")
        )
        if exp_section:
            # Expand any "Show more" toggles to reveal descriptions
            try:
                for btn in exp_section.find_elements(By.XPATH, ".//button[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'see more')]]"):
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.2)
                    except Exception:
                        continue
            except Exception:
                pass

            items = exp_section.find_elements(By.XPATH, 
                ".//li[contains(@class,'pvs-list__paged-list-item') or contains(@class,'artdeco-list__item')]"
            )
            for li in items:
                try:
                    # Prefer visible text spans (aria-hidden='true') which avoid a11y duplicates
                    role_xpath_candidates = [
                        ".//span[contains(@class,'t-bold') and @aria-hidden='true']",
                        ".//div[contains(@class,'t-bold') and @aria-hidden='true']",
                        ".//span[contains(@class,'t-bold')]",
                        ".//div[contains(@class,'t-bold')]",
                    ]
                    company_xpath_candidates = [
                        ".//span[contains(@class,'t-14') and contains(@class,'t-normal') and @aria-hidden='true']",
                        ".//span[contains(@class,'t-14') and contains(@class,'t-normal')]",
                    ]

                    def get_first_text_by_xpaths(root, xpaths):
                        for xp in xpaths:
                            node = _first_or_none(root.find_elements(By.XPATH, xp))
                            text = _get_text_safe(node)
                            if text:
                                return text
                        return None

                    role_raw = get_first_text_by_xpaths(li, role_xpath_candidates)
                    company_raw = get_first_text_by_xpaths(li, company_xpath_candidates)

                    # Prefer aria-hidden='true' to avoid duplicate a11y text
                    desc_el = _first_or_none(li.find_elements(
                        By.XPATH,
                        ".//div[(contains(@class,'show-more-less-text__text') or contains(@class,'inline-show-more-text')) and @aria-hidden='true']"
                    ))
                    if not desc_el:
                        # fallback if aria-hidden not present
                        desc_el = _first_or_none(li.find_elements(
                            By.XPATH,
                            ".//div[contains(@class,'show-more-less-text__text') or contains(@class,'inline-show-more-text')]"
                        ))

                    description = _get_text_safe(desc_el) if desc_el else None

                    # Safety: remove duplicate lines like "Text\nText"
                    if description:
                        parts = [p.strip() for p in description.split('\n') if p.strip()]
                        if len(parts) == 2 and parts[0] == parts[1]:
                            description = parts[0]
                    
                    def _normalize_label(raw: str | None) -> str | None:
                        if not raw:
                            return None
                        # Take first non-empty line
                        first_line = next((p.strip() for p in raw.splitlines() if p.strip()), "")
                        if not first_line:
                            first_line = raw.strip()
                        # Cut off after separators used by LinkedIn lines, but PRESERVE intra-word hyphens
                        # e.g., keep 'Co-Director', only split on spaced hyphens like ' - '
                        first_line = re.split(r"\s*[·\|—]\s*|\s-\s", first_line)[0]
                        return first_line.strip() or None

                    role = _normalize_label(role_raw)
                    company = _normalize_label(company_raw)
                    # Filter empty entries
                    if role or company or description:
                        data["experiences"].append({
                            "company": company,
                            "role": role,
                            "description": description,
                        })
                except Exception:
                    continue
    except Exception:
        pass

    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Open Chrome, log into LinkedIn with li_at cookie, and navigate to your profile.")
    parser.add_argument("--reset", action="store_true", help="Delete saved values and re-prompt.")
    args = parser.parse_args()

    env_values = ensure_env_values(reset=args.reset)
    li_at = env_values.get("LI_AT", "").strip()
    saved_default = env_values.get("PROFILE_URL", "").strip()
    while True:
        entered = input("Enter a LinkedIn URL to open (press Enter to use saved default if available): ").strip()
        if not entered and saved_default:
            profile_url = saved_default
            break
        if entered:
            if not entered.startswith("http://") and not entered.startswith("https://"):
                entered = "https://" + entered
            profile_url = entered
            break
        print("A URL is required if no saved default exists. Please try again.")

    if not li_at or not profile_url:
        print("Error: LI_AT and PROFILE_URL are required.")
        sys.exit(1)

    driver = build_driver()

    try:
        print("Launching LinkedIn and injecting cookie...")
        try:
            add_linkedin_cookie(driver, li_at)
        except NoSuchWindowException:
            # Recreate the driver once if the initial window closed unexpectedly
            try:
                driver.quit()
            except Exception:
                pass
            driver = build_driver()
            add_linkedin_cookie(driver, li_at)
        if not validate_session_with_cookie(driver):
            print("Your LinkedIn cookie appears invalid or expired. You'll be prompted to update it now.")
            # Prompt for a new cookie securely
            try:
                fresh_li_at = getpass(prompt="Enter a NEW LI_AT (input hidden): ")
            except Exception:
                fresh_li_at = input("Enter a NEW LI_AT (visible input fallback): ")
            if not fresh_li_at:
                print("No cookie provided. Exiting.")
                sys.exit(1)
            set_key(str(ENV_FILE_PATH), "LI_AT", fresh_li_at)

            # Re-apply cookie in a clean context
            add_linkedin_cookie(driver, fresh_li_at)
            if not validate_session_with_cookie(driver):
                print("Login still failed with the new cookie. Please verify the value and try again.")
                sys.exit(1)

        print("Login successful. Navigating to your profile page...")
        navigate_to_profile(driver, profile_url)

        # Scrape
        print("Scraping profile...")
        data = scrape_profile(driver, profile_url)
        # Save JSON next to the script
        out_path = Path(__file__).resolve().parent / "profile.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved: {out_path}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()

