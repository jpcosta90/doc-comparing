import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
from comparison.compare import compare_pil_images

# Função para buscar documentos
def search_documents(max_results=10, start=0, collection=None, max_pages=None):
    base_url = "https://metadata.idl.ucsf.edu/solr/ltdl3/query"
    
    # Configurar query para a coleção selecionada
    query = f"collection:{collection}" if collection else "*:*"
    if max_pages:
        query += f" AND pages:[* TO {max_pages}]"
    
    # Log do query no console para depuração
    st.write(f"Query enviado: {query}")

    params = {
        "q": query,  # Palavra-chave
        "wt": "json",  # Formato JSON
        "rows": max_results,
        "start": start
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erro ao buscar dados: {response.status_code}")
        return None
    
# Função para gerar URL do arquivo TIF
def get_tif_url(doc_id):
    return f"https://download.industrydocuments.ucsf.edu/{doc_id[0]}/{doc_id[1]}/{doc_id[2]}/{doc_id[3]}/{doc_id}/{doc_id}.tif"

# Função para gerar URL de visualização no site
def view_document(doc_id):
    return f"https://www.industrydocuments.ucsf.edu/docs/#id={doc_id}"