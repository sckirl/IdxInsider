import cloudscraper
import json

def test_idx_api():
    url = "https://www.idx.co.id/umbraco/Surface/ListedCompany/GetAnnouncement"
    params = {
        "indexFrom": 0,
        "pageSize": 10,
        "keyword": "Laporan Kepemilikan atau Setiap Perubahan Kepemilikan Saham Perusahaan Terbuka",
        "dateFrom": "20240101",
        "dateTo": "20241231"
    }
    
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_idx_api()
