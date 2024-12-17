import streamlit as st
import requests
from comparison.compare import select_comparison_model
from databse.sqlite_helper import initialize_candidates_table, save_candidate, count_candidates
from PIL import Image
import time
import io

# Inicializar banco de dados
initialize_candidates_table()

# Variável de controle para parar a busca
if "stop_search" not in st.session_state:
    st.session_state["stop_search"] = False

# Título da aplicação
st.title("Busca de Candidatas com Modelos de Comparação")

# Filtros da busca
collection = st.selectbox(
    "Escolha a coleção:",
    ["Todas", "tobacco", "pharma", "food", "chemical", "fossil"]
)
collection_param = None if collection == "Todas" else collection

max_results = st.number_input("Resultados por busca:", min_value=1, step=1, value=10)
start_page = st.number_input("Início da busca (página):", min_value=0, step=1, value=0)
max_pages = st.number_input("Número máximo de páginas do documento:", min_value=1, step=1, value=1)

# Seleção do modelo para comparação
comparison_model = select_comparison_model()

# Contadores dinâmicos
comparison_status = st.empty()
results_saved = st.empty()
stop_button = st.button("Parar Busca")

# Funções auxiliares
def search_documents(collection=None, max_results=10, start=0):
    """
    Busca documentos na API com base nos filtros.
    """
    base_url = "https://metadata.idl.ucsf.edu/solr/ltdl3/query"
    query = f"collection:{collection}" if collection else "*:*"
    params = {
        "q": query,
        "wt": "json",
        "rows": max_results,
        "start": start
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return [doc for doc in response.json().get("response", {}).get("docs", []) if doc.get("pages", 0) <= max_pages]
    else:
        st.error(f"Erro na busca de documentos: {response.status_code}")
        return []

def get_tif_url(doc_id):
    """Gera o URL do arquivo TIF."""
    return f"https://download.industrydocuments.ucsf.edu/{doc_id[0]}/{doc_id[1]}/{doc_id[2]}/{doc_id[3]}/{doc_id}/{doc_id}.tif"

def load_tif(doc_id):
    """Carrega e retorna a primeira página de um arquivo TIF."""
    tif_url = get_tif_url(doc_id)
    response = requests.get(tif_url, stream=True)
    if response.status_code == 200:
        img = Image.open(io.BytesIO(response.content))
        return img.copy()
    else:
        return None

# Lógica principal
if st.button("Iniciar Busca"):
    st.session_state["stop_search"] = False  # Reseta o controle de parada
    total_comparisons = 0
    total_saved = 0

    start = start_page * max_results  # Define o início da busca
    st.info("Iniciando busca sequencial e comparação de documentos...")

    while not st.session_state["stop_search"]:
        documents = search_documents(collection=collection_param, max_results=max_results, start=start)

        if not documents:
            st.warning("Nenhum documento encontrado. Encerrando a busca.")
            break

        # Realiza comparações entre os documentos
        for i, doc1 in enumerate(documents):
            for doc2 in documents[i+1:]:
                if st.session_state["stop_search"]:
                    st.warning("Busca interrompida pelo usuário.")
                    break

                try:
                    doc1_id = doc1.get("id")
                    doc2_id = doc2.get("id")

                    # Carrega imagens
                    img1 = load_tif(doc1_id)
                    img2 = load_tif(doc2_id)

                    if img1 and img2:
                        # Usa o modelo selecionado para comparar imagens
                        result = comparison_model(img1, img2)

                        # Salva se a saída for relevante (output == 4)
                        if result["output"] == 4:
                            save_candidate(doc1_id, doc2_id, result["score"], comparison_model.__name__)
                            total_saved += 1
                    total_comparisons += 1

                    # Atualiza contadores dinâmicos
                    comparison_status.markdown(f"### Comparações realizadas: **{total_comparisons}**")
                    results_saved.markdown(f"### Comparações salvas: **{total_saved}**")

                except Exception as e:
                    st.error(f"Erro ao processar documentos: {e}")

        # Avança para a próxima página
        start += max_results
        time.sleep(1)  # Adiciona pausa para evitar sobrecarga

    st.success("Processo concluído ou interrompido.")

# Botão para parar a busca
def stop_search():
    st.session_state["stop_search"] = True

if stop_button:
    stop_search()

# Exibe contagem inicial
comparison_status.markdown(f"### Comparações realizadas: **0**")
results_saved.markdown(f"### Comparações salvas: **{count_candidates()}**")

# Rodapé
st.sidebar.markdown("**Desenvolvido por João Paulo Vieira Costa**\n\nEntre em contato: [jpcosta1990@gmail.com](mailto:jpcosta1990@gmail.com)")
