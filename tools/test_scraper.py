import asyncio
import time
from tools.recipe_scraper import GoodFoodScraper

scraper = GoodFoodScraper()


def test_sync_scrape():
    print("Testing synchronous scrape...")
    start_time = time.time()
    data = scraper.scrape(start_page=1, end_page=20)
    end_time = time.time()
    print(f"Synchronous scrape took {end_time - start_time:.2f} seconds")
    return data


async def test_async_scrape():
    print("Testing asynchronous scrape...")
    start_time = time.time()
    data = await scraper.ascrape(start_page=1, end_page=20)
    end_time = time.time()
    print(f"Asynchronous scrape took {end_time - start_time:.2f} seconds")
    return data


def test_mp_scrape():
    print("Testing MP scrape...")
    start_time = time.time()
    data = scraper.scrape_mp(start_page=1, end_page=20)
    end_time = time.time()
    print(f"MP scrape took {end_time - start_time:.2f} seconds")
    return data


# Run both tests and compare times
def main():
    url = 'https://www.bbcgoodfood.com/recipes/chorizo-mozzarella-gnocchi-bake'

    # Test synchronous function
    sync_data = test_sync_scrape()
    
    # Test asynchronous function
    async_data = asyncio.run(test_async_scrape())

    # Test multiprocessing function
    mp_data = test_mp_scrape()

    assert sync_data.keys() == async_data.keys() and sync_data.keys() == mp_data.keys()

if __name__ == "__main__":
    main()