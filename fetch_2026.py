import cloudscraper
import json
import os
from datetime import datetime

def fetch_idx_april_2026():
    # Final IDX API URL for 2026
    url = "https://www.idx.co.id/primary/ListedCompany/GetAnnouncement"
    
    # JSON parameters for the POST request
    data = {
        "indexFrom": 0,
        "pageSize": 20,
        "dateFrom": "20260401",
        "dateTo": "20260409",
        "key": "Laporan Kepemilikan atau Setiap Perubahan Kepemilikan Saham Perusahaan Terbuka",
        "language": "id"
    }
    
    print(f"Fetching from {url} with data {data}")
    
    # Use cloudscraper to bypass Cloudflare
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    try:
        # Use POST instead of GET
        response = scraper.post(url, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                res_json = response.json()
                print("Successfully fetched JSON data.")
                with open("/home/sckirl/IdxInsider/april_2026_data.json", "w") as f:
                    json.dump(res_json, f, indent=2)
                
                # Check results
                replies = res_json.get("Replies", [])
                print(f"Total Replies: {len(replies)}")
                for i, reply in enumerate(replies[:5]):
                    print(f"Item {i+1}: {reply.get('Title')} - {reply.get('PublishedDate')}")
                    print(f"FullSizeUrl: {reply.get('FullSizeUrl')}")
            except Exception as json_err:
                print(f"JSON Parse Error: {json_err}")
                print(f"Response text (first 1000 chars): {response.text[:1000]}")
        else:
            print(f"Response Body (first 1000 chars): {response.text[:1000]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_idx_april_2026()
