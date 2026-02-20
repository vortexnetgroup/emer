import requests
import json

def fetch_all_alerts():
    url = "https://alerts.globaleas.org/api/v1/alerts/all"
    
    try:
        print(f"Fetching all alerts from {url}...")
        response = requests.get(url)
        response.raise_for_status() # Raises an error for bad status codes (4xx, 5xx)
        
        alerts = response.json()
        
        if not alerts:
            print("No alerts found.")
            return

        print(f"Found {len(alerts)} alerts:\n")

        for alert in alerts:
            severity = alert.get("severity", "N/A")
            translation = alert.get("translation", "No text available")
            start_time = alert.get("startTime", "N/A")
            end_time = alert.get("endTime", "N/A")
            callsign = alert.get("callsign", "N/A")
            fips_codes = alert.get("fipsCodes", [])

            print("-" * 60)
            print(f"Severity:    {severity}")
            print(f"Translation: {translation}")
            print(f"Start Time:  {start_time}")
            print(f"End Time:    {end_time}")
            print(f"Call Sign:   {callsign}")
            print(f"FIPS Codes:  {', '.join(fips_codes)}")
            print("-" * 60)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching alerts: {e}")

if __name__ == "__main__":
    fetch_all_alerts()