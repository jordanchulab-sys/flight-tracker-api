import urllib.request
import json
import os

# Fetch the API key safely from the system environment
API_KEY = os.environ.get("AVIATIONSTACK_API_KEY")

# Check if the key exists before running
if not API_KEY:
    print("Error: AVIATIONSTACK_API_KEY environment variable is not set!")
    exit(1)

flight_number = input("Enter the flight number (e.g., UA123 or DL456): ").strip()
url = f"http://api.aviationstack.com/v1/flights?access_key={API_KEY}&flight_iata={flight_number}"

print(f"\nSearching Aviationstack for flight {flight_number}...")

try:
    with urllib.request.urlopen(url) as response:
        data = response.read().decode('utf-8')
        json_data = json.loads(data)
        
        flights = json_data.get("data", [])
        if len(flights) > 0:
            flight = flights[0]
            print(f"\n✈️ Airline: {flight.get('airline', {}).get('name', 'Unknown')}")
            print(f"📊 Status: {flight.get('status', 'Unknown').upper()}")
        else:
            print(f"\nNo active flights found for '{flight_number}'.")
        
except Exception as e:
    print(f"\nAn error occurred: {e}")

# Only wait for input if running in an interactive terminal
if os.isatty(0):
    input("\nPress Enter to exit...")