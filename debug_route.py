import asyncio
from scraper import scrub_headlines, scrub_cartoons, scrub_popular
import json

async def main():
    print("--- Testing HOME headlines ---")
    headlines = await scrub_headlines("HOME")
    if headlines:
        print(json.dumps(headlines[0].model_dump(), indent=2))
    
    print("\n--- Testing Cartoons ---")
    cartoons = await scrub_cartoons()
    if cartoons:
        print(json.dumps(cartoons[0].model_dump(), indent=2))
        
    print("\n--- Testing Popular ---")
    popular = await scrub_popular()
    if popular:
        print(json.dumps(popular[0].model_dump(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
