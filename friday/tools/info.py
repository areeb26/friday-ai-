"""
Info tools — weather, Wikipedia, currency conversion for FRIDAY's briefings.
"""

import httpx
import wikipedia
import logging

logger = logging.getLogger("friday.tools.info")


def register(mcp):

    @mcp.tool()
    async def get_weather(location: str = "local") -> str:
        """Get current weather for a location (uses Open-Meteo, free)."""
        try:
            # Coordinates for major cities
            coords = {
                "london": (51.5074, -0.1278),
                "new york": (40.7128, -74.0060),
                "tokyo": (35.6762, 139.6503),
                "paris": (48.8566, 2.3522),
                "mumbai": (19.0760, 72.8777),
                "sydney": (-33.8688, 151.2093),
            }
            
            # Default to London if "local" or unknown
            loc_key = location.lower().strip()
            if loc_key in coords:
                lat, lon = coords[loc_key]
                location_name = location.title()
            else:
                lat, lon = 51.5074, -0.1278  # Default: London
                location_name = "your area (default: London)"
            
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&timezone=auto"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                data = response.json()
            
            current = data.get("current", {})
            temp = current.get("temperature_2m", "?")
            weather_code = current.get("weather_code", 0)
            
            # WMO Weather code to condition
            conditions = {
                0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
                45: "foggy", 48: "foggy",
                51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
                61: "slight rain", 63: "moderate rain", 65: "heavy rain",
                71: "slight snow", 73: "moderate snow", 75: "heavy snow",
            }
            condition = conditions.get(weather_code, f"weather code {weather_code}")
            
            # Convert to Fahrenheit
            temp_f = round((temp * 9/5) + 32, 1)
            
            return f"It's {temp_f}°F and {condition} in {location_name}, boss. Perfect night for a flight."
            
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return "Weather data is unavailable right now, boss. Check your windows?"

    @mcp.tool()
    def quick_wikipedia(query: str) -> str:
        """Get a quick summary from Wikipedia."""
        try:
            # Set language and get summary
            wikipedia.set_lang("en")
            
            # Search for the topic
            search_results = wikipedia.search(query, results=1)
            if not search_results:
                return f"Couldn't find anything on Wikipedia about '{query}', boss."
            
            # Get the page
            page = wikipedia.page(search_results[0], auto_suggest=False)
            summary = page.summary[:500]  # First 500 chars
            
            return f"Here's the gist on {page.title}: {summary}..."
            
        except wikipedia.exceptions.DisambiguationError as e:
            options = e.options[:3]
            return f"That could mean a few things, boss. Try: {', '.join(options)}"
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{query}', boss."
        except Exception as e:
            logger.error(f"Wikipedia failed: {e}")
            return "Wikipedia is having trouble, boss. Try again?"

    @mcp.tool()
    def currency_convert(amount: float, from_currency: str, to_currency: str) -> str:
        """Convert between currencies (e.g., USD to EUR)."""
        try:
            # Common rates (approximate, updated periodically)
            rates = {
                "USD": {"EUR": 0.92, "GBP": 0.79, "JPY": 150.0, "INR": 83.0, "CAD": 1.35},
                "EUR": {"USD": 1.09, "GBP": 0.86, "JPY": 163.0, "INR": 90.0},
                "GBP": {"USD": 1.27, "EUR": 1.16, "INR": 105.0},
            }
            
            from_c = from_currency.upper()
            to_c = to_currency.upper()
            
            if from_c == to_c:
                return f"That's {amount} {to_c}, boss. Same currency."
            
            # Direct rate
            if from_c in rates and to_c in rates[from_c]:
                rate = rates[from_c][to_c]
                converted = round(amount * rate, 2)
                return f"That's approximately {converted} {to_c}, boss. ({rate} rate)"
            
            # Try reverse
            if to_c in rates and from_c in rates[to_c]:
                rate = 1 / rates[to_c][from_c]
                converted = round(amount * rate, 2)
                return f"That's approximately {converted} {to_c}, boss."
            
            return f"I don't have the exchange rate from {from_c} to {to_c}, boss. Try USD, EUR, GBP, JPY, INR, or CAD."
            
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            return "Currency converter is down, boss. Try a calculator?"
