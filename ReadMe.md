# Habit Tracker Report (weekly)

A weekly habit tracking report that **reads Google Sheets data**, **deduplicates by day**, and **summarizes habit completion** for the last 7 days. Built for automation, dashboards, and progress insights.

---

## Links
- **Google Form (Survey)** — Habit input form used for daily logging  
  <https://docs.google.com/forms/d/e/1FAIpQLSet-9f0PVHtqay5NKQBkuS0cRItcOEDoh26LLsx5NyB44cOzA/viewform>

- **Google Sheets (Raw Data)** — Source for processing and reporting  
  <https://docs.google.com/spreadsheets/d/1gT_m6xnpEQ3YEIE44bwokKZJgsLn66nMo3MifTa4GGc/edit>

---

## Features
- Automatic **Timestamp parsing**
- **Daily dedup** using column-wise `max()` (keeps `1` if any habit was completed that day)
- **Calendar gap filling** (missing days → all `0`)
- **Weekly pivot summary** (`Habit | Sum`)
- Gmail-safe **static chart export** (PNG via **Kaleido/Kaleido**)
- Clean, reusable structure for notebooks, scripts, or UI dashboards

---

## Data Format
Expected DataFrame structure:

| Column | Type | Values |
|---|---|---|
| `Timestamp` | `datetime` | Submission date + time |
| Habit columns | `int` | `1` = completed, `0` = not completed |

Tracked habits include:
no_food, no_fast_food, sleep_without_phone, no_nut, gt_130BPM, gt_180BPM, weighted_walk, vitamins


---

## Usage (Python)

Make sure to:
1. Enable **Google Sheets API** in your Google Cloud project
2. Create a **Service Account**
3. Download the **JSON Key**
4. Share the target Google Sheet with your service account email
5. Reference the sheet by **Spreadsheet ID** or **tab name**

---

## Dependencies
```bash
pip install gspread oauth2client pandas plotly kaleido

---

## Notes

* A **service account can only access sheets shared with its email** (it cannot browse Drive like a normal user).
* **Interactive Plotly charts will not render in Gmail on iPhone** — export as static images instead.

---

## Future Ideas

* Normalized scoring (0.0 → 1.0 like Justin’s media dashboards)
* Calendar heatmaps
* Mobile-friendly HTML dashboards hosted via Cloudflare
* Automated weekly email reports with image attachments
* GSheet → DuckDB sync for local analytics

---

## License
Fair Source License
