import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain.tools.retriever import create_retriever_tool

load_dotenv()
pinecone_index = os.getenv("PINECONE_INDEX")


def create_retriever(k=5):
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
    )
    vectorstore = PineconeVectorStore(index_name=pinecone_index, embedding=embedding_model, text_key='title')
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return retriever


def create_recipe_retriever_tool(k):
    retriever = create_retriever(k)
    doc_prompt = PromptTemplate.from_template(
    'Recipe Title: {page_content}, '
    'Ingredients: {ingredients}, '
    'Nutritional Information: {nutritional_info}, '
    'Prep Time: {prep_time} '
    'Cooking Time: {cooking_time} '
    'Average Rating: {avg_rating}, '
    'Serves: {serves}, '
    'URL: {url}, ')
    retriever_tool = create_retriever_tool(retriever, 
                                           "recipe_retriever", 
                                           f"Searches for relevant recipes and returns data for the top {k} results. "
                                           "Input should be a generic recipe description that could be matched to the user's query.", 
                                           document_prompt=doc_prompt)

    return retriever_tool