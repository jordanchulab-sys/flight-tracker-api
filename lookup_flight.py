import urllib.request
import json
import os
from dotenv import load_dotenv

# Load variables from the local .env file
load_dotenv()

# Pull the API key securely from the environment
API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

if not API_KEY:
    print("Error: AVIATIONSTACK_API_KEY is not set in the .env file!")
    exit(1)

# Ask for flight number input
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
            print(f"\n--- Found Result for {flight_number} ---")
            print(f"✈️ Airline: {flight.get('airline', {}).get('name', 'Unknown Airline')}")
            print(f"📊 Status: {flight.get('status', 'Unknown Status').upper()}")
            print(f"🛫 Departure Airport: {flight.get('departure', {}).get('airport', 'Unknown')}")
            print(f"🛬 Arrival Airport: {flight.get('arrival', {}).get('airport', 'Unknown')}")
        else:
            print(f"\nNo active flights found for '{flight_number}'.")
            
except Exception as e:
    print(f"\nAn error occurred: {e}")

input("\nPress Enter to exit...")