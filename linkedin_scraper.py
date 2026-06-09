# pip install playwright requests
# playwright install chromium

import requests
import time
import sys
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import gspread
from google.oauth2.service_account import Credentials
from urllib.parse import urlparse, parse_qs

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def start_adspower_browser(user_id="k1cl2tog"):
    url = f"http://local.adspower.net:50325/api/v1/browser/start?user_id={user_id}"
    api_key = "384321b50a1f65a030463eea0cbf967a008d824e5895fa9b"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get("code") == 0 and "ws" in data["data"] and "puppeteer" in data["data"]["ws"]:
            return data["data"]["ws"]["puppeteer"]
        else:
            print(f"Failed to start AdsPower browser. Response: {data}")
            return None
    except Exception as e:
        print(f"Error starting AdsPower browser: {e}")
        return None

def main():
    total_profiles = 0
    p = None
    
    try:
        print("Starting LinkedIn Sales Navigator Scraper...")
        
        search_url = input("Paste your Sales Navigator search URL: ").strip()
        if not search_url:
            print("URL cannot be empty. Exiting.")
            return

        # Automatically determine starting page from URL
        parsed_url = urlparse(search_url)
        query_params = parse_qs(parsed_url.query)
        if 'page' in query_params:
            try:
                start_page_num = int(query_params['page'][0])
                print(f"Automatically detected starting page: {start_page_num}")
            except ValueError:
                start_page_num = 1
        else:
            start_page_num = 1

        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Initialize Google Sheets - Look for credentials.json in the same folder as the script
        print("Connecting to Google Sheets...")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(script_dir, "credentials.json")
        
        # Check if credentials file exists
        if not os.path.exists(creds_path):
            print(f"❌ Error: credentials.json not found at {creds_path}")
            print("Please make sure credentials.json is in the same folder as the scraper script.")
            return
        
        print(f"✅ Found credentials at: {creds_path}")
        credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        sheet_ids = {
            1: "1_cHXqBjdh0t_T9SJpQQoCtp1bBoZvL-poLPQUXzJNaM",
            2: "1j9RYNBQtJGTpYo_1yxWr9sevyHLJBRZaasAaAVci2nI",
            3: "1-fwZWWoKcCfkiQ-X7zHHqmrNdnN5KiDRuvB46scimls",
            4: "1Owf1rv755CTr9ftDIkJiq5ru3IV-CGiILFyc1kQ1WUk"
        }
        worksheet = None
        current_sheet_choice = None
        records_since_separator = 0
        pages_in_current_batch = set()

        # Start AdsPower
        print("Connecting to AdsPower browser...")
        ws_url = start_adspower_browser()
        if not ws_url:
            sys.exit(1)

        print(f"WebSocket URL: {ws_url}")

        # Start Playwright manually to prevent automatic stopping
        p = sync_playwright().start()
        browser = p.chromium.connect_over_cdp(ws_url)
        
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
        else:
            context = browser.new_context()
            
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = context.new_page()

        print(f"Navigating to {search_url}...")
        page.goto(search_url, wait_until="domcontentloaded")

        page_num = start_page_num

        while True:
            if (page_num - 1) % 2 == 0 or current_sheet_choice is None:
                print(f"\n--- Preparing to scrape page {page_num} and {page_num+1} ---")
                while True:
                    choice = input("Which Google Sheet do you want to store data to? (1, 2, 3, or 4): ").strip()
                    if choice in ['1', '2', '3', '4']:
                        choice = int(choice)
                        break
                    print("Invalid choice. Please enter 1, 2, 3, or 4.")
                
                if choice != current_sheet_choice:
                    sh = gc.open_by_key(sheet_ids[choice])
                    worksheet = sh.sheet1
                    current_sheet_choice = choice
                    records_since_separator = 0
                    pages_in_current_batch = set()
                    
                    # Ensure headers exist
                    first_row = worksheet.row_values(1)
                    if not first_row or first_row[0] != 'Name':
                        if not worksheet.get_all_values():
                            worksheet.append_row(['Name', 'Profile-Link'])
                        else:
                            worksheet.insert_row(['Name', 'Profile-Link'], index=1)
                print(f"Data will be saved to Sheet {choice}.")

            print(f"Waiting for results to load on page {page_num}...")
            try:
                # Wait for results to load
                page.wait_for_selector('a[data-control-name="view_lead_panel_via_search_lead_name"]', timeout=20000)
            except Exception as e:
                print(f"Timeout or no results found on page {page_num}.")
                break

            # Scroll the results container, not the page body
            container_selector = '#search-results-container'
            page.wait_for_selector(container_selector, timeout=10000)

            print("Scrolling through results...")
            for _ in range(10):
                page.evaluate("document.querySelector('#search-results-container').scrollTop += 800")
                time.sleep(3)

            print("Waiting 5 seconds for everything to load...")
            time.sleep(5)

            elements = page.locator('a[data-control-name="view_lead_panel_via_search_lead_name"]').all()
            
            if not elements:
                print("No profiles found on this page. Stopping.")
                break

            print(f"Found {len(elements)} profile links to process. Extracting data...")
            page_results_count = 0
            
            for i, element in enumerate(elements):
                try:
                    print(f"  Processing profile {i+1}/{len(elements)}...", end="\r")
                    href = element.get_attribute('href', timeout=1000) or ""
                    profile_link = ""
                    try:
                        ancestor_div = element.locator('xpath=ancestor::div[@data-scroll-into-view]').first
                        if ancestor_div.count() > 0:
                            urn = ancestor_div.get_attribute('data-scroll-into-view', timeout=1000) or ""
                            if 'fs_salesProfile:(' in urn:
                                member_id = urn.split('fs_salesProfile:(')[1].split(',')[0]
                                profile_link = f"https://www.linkedin.com/in/{member_id}/"
                    except Exception:
                        pass
                        
                    if not profile_link and '/sales/lead/' in href:
                        lead_part = href.split('/sales/lead/')[-1]
                        member_id = lead_part.split(',')[0]
                        profile_link = f"https://www.linkedin.com/in/{member_id}/"
                    if not profile_link:
                        profile_link = href
                        
                    # Try to find the closest container (usually a list item)
                    container = element.locator('xpath=ancestor::li').first
                    if container.count() == 0:
                        container = element.locator('xpath=ancestor::div[contains(@class, "artdeco-list__item")]').first
                    
                    name = ""

                    if container.count() > 0:
                        name_loc = container.locator('span[data-anonymize="person-name"]')
                        if name_loc.count() > 0:
                            name = name_loc.first.inner_text(timeout=1000).strip()
                    else:
                        name_loc = element.locator('span[data-anonymize="person-name"]')
                        if name_loc.count() > 0:
                            name = name_loc.first.inner_text(timeout=1000).strip()

                    if not name:
                        name = element.inner_text(timeout=1000).strip()

                    worksheet.append_row([name, profile_link])
                    page_results_count += 1
                    total_profiles += 1
                    
                    records_since_separator += 1
                    pages_in_current_batch.add(page_num)
                except Exception as e:
                    print(f"\nError extracting profile {i+1}: {e}")
                    continue

            print(f"\n✅ Page {page_num} scraped — {page_results_count} results")

            # Add separator at the end of every 2nd page (batch completion)
            if page_num % 2 == 0 and pages_in_current_batch:
                pages_str = ", ".join(map(str, sorted(list(pages_in_current_batch))))
                worksheet.append_row(["==================================================", "=================================================="])
                worksheet.append_row([f"🌟 LAST SCRAPE ENDED HERE (Pages: {pages_str}) 🌟", ""])
                worksheet.append_row(["==================================================", "=================================================="])
                records_since_separator = 0
                pages_in_current_batch.clear()

            # Pagination
            try:
                next_button = page.locator('button.artdeco-pagination__button--next')
                if next_button.count() == 0:
                    next_button = page.locator('button[aria-label="Next"]')

                if next_button.count() > 0 and not next_button.first.is_disabled():
                    next_button.first.click()
                    time.sleep(2)
                    page_num += 1
                else:
                    break
            except Exception as e:
                print(f"Error clicking Next button: {e}")
                break

    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print(f"🎉 Done! Total {total_profiles} profiles saved to Google Sheets")
        # Intentionally not calling p.stop() or browser.close() to keep AdsPower managed browser open

if __name__ == "__main__":
    main()