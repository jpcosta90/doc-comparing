import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
from comparison.compare import compare_pil_images

# Função para buscar documentos
# Função para buscar documentos
def search_documents(max_results=10, start=0, collection=None, doc_type=None, max_pages=None):
    """
    Busca documentos na API com base nos filtros.
    """
    base_url = "https://metadata.idl.ucsf.edu/solr/ltdl3/query"
    query_parts = []

    # Filtros
    if collection:
        query_parts.append(f"collection:\"{collection}\"")
    if doc_type:
        query_parts.append(f"type:\"{doc_type}\"")
    if max_pages:
        query_parts.append(f"pages:[* TO {max_pages}]")

    # Construção da query final
    query = " AND ".join(query_parts) if query_parts else "*:*"
    st.write(f"Query enviado: {query}")  # Log da query para depuração

    params = {
        "q": query,
        "wt": "json",
        "rows": max_results,
        "start": start
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json().get("response", {}).get("docs", [])
    else:
        st.error(f"Erro na busca de documentos: {response.status_code}")
        return []


    
# Função para gerar URL do arquivo TIF
def get_tif_url(doc_id):
    return f"https://download.industrydocuments.ucsf.edu/{doc_id[0]}/{doc_id[1]}/{doc_id[2]}/{doc_id[3]}/{doc_id}/{doc_id}.tif"

# Função para gerar URL de visualização no site
def view_document(doc_id):
    return f"https://www.industrydocuments.ucsf.edu/docs/#id={doc_id}"