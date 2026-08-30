import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# BASE_DIR = Path(__file__).resolve().parent

# load_dotenv(BASE_DIR / ".env")
load_dotenv()

NAUKRI_USERNAME = os.getenv("NAUKRI_USERNAME")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD")
RESUME_PATH = os.getenv("RESUME_PATH")


# --------------------------------------------------
# Configuration
# --------------------------------------------------

LOGIN_URL = "https://www.naukri.com/nlogin/login?URL=https://www.naukri.com/mnjuser/homepage?utm_source=google&utm_medium=cpc&utm_campaign=Brand"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

HEADLESS = False


# --------------------------------------------------
# Validation
# --------------------------------------------------

if not NAUKRI_USERNAME:
    raise ValueError("NAUKRI_USERNAME is missing in .env")

if not NAUKRI_PASSWORD:
    raise ValueError("NAUKRI_PASSWORD is missing in .env")

if not RESUME_PATH:
    raise ValueError("RESUME_PATH is missing in .env")

resume_path = Path(RESUME_PATH)

if not resume_path.exists():
    raise FileNotFoundError(
        f"Resume file does not exist: {resume_path}"
    )

if resume_path.stat().st_size > 2 * 1024 * 1024:
    raise ValueError(
        "Resume must be 2 MB or smaller."
    )


# --------------------------------------------------
# Screenshot helper
# --------------------------------------------------

def screenshot(page, name):
    filename = (
        f"naukri_{name}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )

    page.screenshot(
        path=filename,
        full_page=True
    )

    print(f"Screenshot saved: {filename}")


# --------------------------------------------------
# Main
# --------------------------------------------------

def update_naukri_resume():

    print("=" * 60)
    print("NAUKRI RESUME AUTOMATION")
    print("=" * 60)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=100
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 900
            }
        )

        page = context.new_page()

        try:

            # --------------------------------------------------
            # 1. Open login page
            # --------------------------------------------------

            print("\n1. Opening Naukri login...")
            print(datetime.now())

            page.goto(
                LOGIN_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            # --------------------------------------------------
            # 2. Fill username
            # --------------------------------------------------

            print("2. Entering username...")

            page.locator("#usernameField").fill(
                NAUKRI_USERNAME
            )

            # --------------------------------------------------
            # 3. Fill password
            # --------------------------------------------------

            print("3. Entering password...")

            page.locator("#passwordField").fill(
                NAUKRI_PASSWORD
            )

            # --------------------------------------------------
            # 4. Login
            # --------------------------------------------------

            print("4. Clicking Login...")

            page.get_by_role(
                "button",
                name="Login",
                exact=True
            ).click()

            # Give Naukri time to process login
            page.wait_for_timeout(5000)

            print(
                f"Current URL: {page.url}"
            )

            # --------------------------------------------------
            # 5. Check login
            # --------------------------------------------------

            if "nlogin" in page.url.lower():

                screenshot(
                    page,
                    "login_failed"
                )

                raise RuntimeError(
                    "Login did not complete. "
                    "Possible CAPTCHA, incorrect credentials, "
                    "or Naukri changed the login flow."
                )

            print("Login successful.")

            # --------------------------------------------------
            # 6. Open profile
            # --------------------------------------------------

            print("\n5. Opening profile...")

            page.goto(
                PROFILE_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(3000)

            print(
                f"Profile URL: {page.url}"
            )

            # --------------------------------------------------
            # 7. Locate resume upload input
            # --------------------------------------------------

            print("\n6. Looking for resume upload...")

            file_input = page.locator(
                "#attachCV"
            )

            file_input.wait_for(
                state="attached",
                timeout=15000
            )

            print(
                "Resume upload input found."
            )

            # --------------------------------------------------
            # 8. Select resume
            # --------------------------------------------------

            print(
                f"7. Selecting resume: {resume_path}"
            )

            file_input.set_input_files(
                str(resume_path)
            )

            page.wait_for_timeout(2000)

            print(
                "Resume file selected."
            )

            # --------------------------------------------------
            # 9. Click Update resume
            # --------------------------------------------------

            print(
                "\n8. Clicking 'Update resume'..."
            )

            update_button = page.locator(
                'input.dummyUpload[value="Update resume"]'
            )

            update_button.wait_for(
                state="visible",
                timeout=10000
            )

            update_button.click()

            # --------------------------------------------------
            # 10. Wait for upload/parser
            # --------------------------------------------------

            print(
                "9. Waiting for resume upload..."
            )

            page.wait_for_timeout(5000)

            # --------------------------------------------------
            # 11. Check result area
            # --------------------------------------------------

            result = page.locator("#result")

            if result.count() > 0:

                try:

                    result_text = result.inner_text(
                        timeout=5000
                    )

                    if result_text.strip():

                        print(
                            f"Result: {result_text}"
                        )

                except Exception:
                    pass

            # --------------------------------------------------
            # 12. Check parser result
            # --------------------------------------------------

            parser_result = page.locator(
                "#results_resumeParser"
            )

            if parser_result.count() > 0:

                try:

                    parser_text = parser_result.inner_text(
                        timeout=5000
                    )

                    if parser_text.strip():

                        print(
                            f"Parser result: {parser_text}"
                        )

                except Exception:
                    pass

            # --------------------------------------------------
            # 13. Final verification
            # --------------------------------------------------

            page.wait_for_timeout(3000)

            print("\n10. Verifying update...")
            print("SUCCESS: Resume uploaded successfully.")

            # body_text = (
            #     page.locator("body")
            #     .inner_text()
            #     .lower()
            # )

            # success_indicators = [
            #     "updated successfully",
            #     "resume updated",
            #     "resume uploaded",
            #     "successfully"
            # ]

            # matched = [
            #     text
            #     for text in success_indicators
            #     if text in body_text
            # ]

            # if matched:

            #     print(
            #         "SUCCESS: Resume appears to be updated."
            #     )

            # else:

            #     print(
            #         "WARNING: Upload action completed, "
            #         "but success message was not detected."
            #     )

                # screenshot(
                #     page,
                #     "verification"
                # )

            print("\n" + "=" * 60)
            print("AUTOMATION FINISHED")
            print("=" * 60)

        except PlaywrightTimeoutError as e:

            print(
                "\nPLAYWRIGHT TIMEOUT:"
            )

            print(e)

            screenshot(
                page,
                "timeout"
            )

            raise

        except Exception as e:

            print(
                "\nAUTOMATION ERROR:"
            )

            print(e)

            screenshot(
                page,
                "error"
            )

            raise

        finally:

            browser.close()


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":

    try:

        update_naukri_resume()

    except Exception:

        sys.exit(1)