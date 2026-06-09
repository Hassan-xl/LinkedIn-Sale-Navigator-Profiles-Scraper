# 🔍 LinkedIn Sales Navigator Profiles Scraper

A Python automation tool that scrapes **LinkedIn Sales Navigator** search results using **AdsPower** browser profiles and **Playwright**, then saves extracted profile data directly to **Google Sheets**.

---

## ✨ Features

- 🚀 Connects to an existing AdsPower browser session (bypasses LinkedIn bot detection)
- 📄 Auto-detects the starting page from the pasted Sales Navigator URL
- 👤 Extracts **full name** and converts Sales Navigator leads into **regular LinkedIn profile URLs** (`linkedin.com/in/...`) — viewable by anyone, no LinkedIn Premium required
- 📊 Saves data to one of **4 configurable Google Sheets**
- 🔁 Handles **pagination** automatically
- 📌 Adds **batch separator markers** every 2 pages for easy tracking
- ⚠️ Gracefully handles timeouts, missing elements, and keyboard interrupts

---

## 🛠️ Requirements

### Python packages
```bash
pip install playwright requests gspread google-auth
playwright install chromium
```

### External dependencies
- [AdsPower](https://www.adspower.com/) — anti-detect browser running locally on port `50325`
- A **Google Cloud service account** with Sheets + Drive API access
- A `credentials.json` file placed in the **same folder** as the script

---

## ⚙️ Setup

### 1. Google Sheets credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a service account and download your `credentials.json` key file
3. Share your target Google Sheets with the service account email
4. Rename the included `credentials.example.json` to `credentials.json` and fill in your values
5. Place it in the same directory as the script

> ✅ A blank `credentials.example.json` template is included in the repo.

### 2. Configure your Sheet IDs
Edit the `sheet_ids` dictionary in the script to point to your own Google Sheet IDs:
```python
sheet_ids = {
    1: "your_sheet_id_here",
    2: "your_sheet_id_here",
    3: "your_sheet_id_here",
    4: "your_sheet_id_here"
}
```

### 3. AdsPower setup
- Make sure AdsPower is running locally
- Update `user_id` and `api_key` in `start_adspower_browser()` with your own credentials:
```python
def start_adspower_browser(user_id="your_user_id"):
    api_key = "your_api_key"
```

---

## ▶️ Usage

```bash
python scraper.py
```

You'll be prompted to:
1. **Paste your Sales Navigator search URL** — the script auto-detects the starting page
2. **Choose a Google Sheet** (1–4) to store results into — prompted every 2 pages

---

## 📁 Output Format

Data is written to the selected Google Sheet with the following columns:

| Name         | Profile-Link                          |
|--------------|---------------------------------------|
| John Doe     | https://www.linkedin.com/in/johndoe/  |
| Jane Smith   | https://www.linkedin.com/in/janesmith/|

> 💡 **No LinkedIn Premium needed to view profiles.** The scraper converts internal Sales Navigator lead URLs into standard `linkedin.com/in/` profile links — anyone with a free LinkedIn account can open them directly.

Every 2-page batch ends with a separator row for easy visual tracking:

```
==================================================
🌟 LAST SCRAPE ENDED HERE (Pages: 1, 2) 🌟
==================================================
```

---

## 📝 Notes

- The AdsPower browser is **intentionally left open** after the script finishes to preserve the session
- LinkedIn limits Sales Navigator search results to **100 pages** (2,500 results)
- If a page times out or returns no results, the scraper stops gracefully

---

## ⚠️ Disclaimer

This tool is intended for **personal or research use only**. Make sure your usage complies with [LinkedIn's Terms of Service](https://www.linkedin.com/legal/user-agreement). The authors are not responsible for any misuse or account restrictions.

---

## 📄 License

MIT License
