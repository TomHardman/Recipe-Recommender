import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib
from abc import ABC, abstractmethod
from decimal import Decimal

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from pinecone import Pinecone
from dotenv import load_dotenv
from tqdm import tqdm
from requests.exceptions import HTTPError


class RecipeScraper(ABC):
    @abstractmethod
    def get_metadata(self, url):
        pass

    @abstractmethod
    def scrape(self, search_url, start_page, end_page):
        pass


class GoodFoodScraper(RecipeScraper):
    def __init__(self, base_url="https://www.bbcgoodfood.com"):
        self.base_url = base_url
        
    def get_recipe_links_on_page(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        recipe_links = set()
        
        for link in soup.find_all('a'):
            url = (link.get('href'))
            if url and '/recipes/' in url and 'category' not in url and 'collection' not in url:
                recipe_links.add(self.base_url + link.get('href'))
        
        return list(recipe_links)

    def process_method_steps(self, steps: list[dict]):
        processed_steps = []
        for i, step in enumerate(steps):
            step_content = step['content'][0]['data']['value'].replace('\xa0', ' ')
            processed_steps.append(f'Step {i+1}: {step_content}')
        return processed_steps

    def get_metadata(self, url) -> dict:
        response = requests.get(url)
        metadata = {}

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            json_txt_recipe = soup.find('script', id='__AD_SETTINGS__').string
            json_recipe = json.loads(json_txt_recipe)['permutiveConfig']['permutiveModel']
            json_cuisine = json.loads(json_txt_recipe)['targets']
            
            json_txt_ratings = soup.find('script', id='__POST_CONTENT__').string
            json_ratings = json.loads(json_txt_ratings)['userRatings']
            json_steps = json.loads(json_txt_ratings)['methodSteps']

            metadata['title'] = json_recipe['title']
            metadata['url'] = url
            metadata['description'] = json_recipe['article']['description'].replace('\xa0', ' ')
            metadata['ingredients'] = list(json_recipe['recipe']['ingredients'])
            metadata['nutritional_info'] = json_recipe['recipe']['nutrition_info']
            metadata['cooking_time'] = str(int(json_recipe['recipe']['cooking_time'])//60) + 'minutes'
            metadata['prep_time'] = str(int(json_recipe['recipe']['prep_time'])//60) + 'minutes'
            metadata['diet_types'] = json_recipe['recipe']['diet_types']
            metadata['no_of_ratings'] = int(json_ratings['total'])
            metadata['avg_rating'] = json_ratings['avg']
            metadata['method_steps'] = self.process_method_steps(json_steps)

            serves = json_recipe['recipe']['serves']
            if serves:
                metadata['serves'] = int(json_recipe['recipe']['serves'])
            else:
                metadata['serves'] = 2
            
            if 'cuisine' in json_cuisine.keys():
                metadata['cuisine'] = json_cuisine['cuisine']
            else:
                metadata['cuisine'] = []
        
        return metadata
    
    def scrape(self, search_url='/search?tab=recipe&mealType=dinner&sort=rating&page=', 
               start_page=1, end_page=10) -> dict:
        data = {}

        for pg in range(start_page, end_page+1):
            url = self.base_url + search_url + str(pg)
            recipe_links = self.get_recipe_links_on_page(url)
            for link in recipe_links:
                metadata = self.get_metadata(link)
                id_ = hashlib.md5(metadata['url'].encode()).hexdigest()

                metadata['id'] = id_
                data[id_] = metadata
        
        return data
    
    def scrape_and_upsert(self, embedding_model, vector_index, llm, prompt_template, search_url='/search?tab=recipe&mealType=dinner&sort=rating&page=',
                          start_page=1, end_page=50, chunk_size=2):
        """
        Scrapes recipes from the GoodFood website and upserts them into a Pinecone Vector Index. Uses an LLM to
        rewrite the recipe descriptions taking in recipe metadata as input.
        """
        
        for start in tqdm(range(start_page, end_page+1-chunk_size, chunk_size)):
            data = self.scrape(search_url, start, start+chunk_size-1)
            vectors = []

            for item in data.values():
                prompt = prompt_template.format(data=item)
                description = llm.invoke(prompt)
      
                # Insert vectors and relevant metadata into Pinecone Vector Index
                vec_item = {}
                vec_item['id'] = item['id']
                vec_item['values'] = embedding_model.embed_query(description.content)
                metadata = {k: v for k, v in item.items() if k != 'id'}
                vec_item['metadata'] = metadata
                vectors.append(vec_item)

            try:
                vector_index.upsert(vectors)
            except Exception as e:
                print(f"Bad Request: - Ignoring this chunk.")
        

if __name__ == "__main__":
    scraper = GoodFoodScraper()

    prompt_template = PromptTemplate.from_template(
        "Given the following recipe data, rewrite the description to be more informative, "
        "in a way that would easily allow the recipe to be found through matching its description to "
        "a user query. Make sure to include information such as key ingredients, key dietary information, "
        "and the relevant cuisine if available. Output only the description and nothing else. Limit your "
        "output to one or two sentences and don't include a url or any quantitative data\n\n"
        "{data}"
    )

    load_dotenv()
    pinecone_key = os.getenv("PINECONE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    llm = ChatOpenAI(model="gpt-4o-mini")

    pc = Pinecone(api_key=pinecone_key)
    vector_index = pc.Index("recipe-db")

    scraper.scrape_and_upsert(embedding_model, vector_index, llm, prompt_template, 
                              start_page=1, end_page=200, chunk_size=1)



