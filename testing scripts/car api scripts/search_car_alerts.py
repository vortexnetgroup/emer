import requests
import json

def search_alerts():
    query = input("Enter search query: ").strip()
    if not query:
        print("Search query cannot be empty.")
        return

    # Endpoint for searching alerts
    url = "https://alerts.globaleas.org/api/v1/alerts/search"
    
    # Parameters for the request
    params = {
        "query": query,
        "page": 0
    }
    
    try:
        print(f"Searching for '{query}'...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        alerts = response.json()
        
        if not alerts:
            print("No alerts found matching your query.")
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
        print(f"Error searching alerts: {e}")

if __name__ == "__main__":
    search_alerts()