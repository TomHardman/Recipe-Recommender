from pydantic import BaseModel, Field
from functools import partial
from langchain_core.tools.simple import Tool

from recipe_scraper import RecipeScraper


def scrape_recipe(url: str, scraper: RecipeScraper) -> str:
    data = scraper.get_metadata(url)
    return data


async def ascrape_recipe(url: str, scraper: RecipeScraper) -> str:
    data = await scraper.aget_metadata(url)
    return data


class ScraperInput(BaseModel):
    """Input to the recipe scraper"""
    url: str = Field(description="URL of the recipe to scrape")


def create_recipe_scraper_tool(scraper: RecipeScraper) -> Tool:
    func = partial(
        scrape_recipe,
        scraper=scraper,
    )
    
    afunc = partial(
        ascrape_recipe,
        scraper=scraper,
    )
    return Tool(
        name="recipe_scraper",
        description="Given a recipe URL, scrapes and returns recipe metadata and method",
        func=func,
        coroutine=afunc,
        args_schema=ScraperInput,
    )