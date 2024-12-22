import streamlit as st
import requests
import time
from PIL import Image
from comparison.compare import select_comparison_model
from databse.sqlite_helper import initialize_candidates_table, save_candidate, count_candidates
from utils.document_utils import load_tif
from industry_docs.industry_docs import search_documents
import sqlite3
import pandas as pd

# Caminho para o banco de dados
DB_PATH = "document_comparisons.db"
BASE_URL = "https://metadata.idl.ucsf.edu/solr/ltdl3/query"

# Inicializar banco de dados
initialize_candidates_table()

# Função para carregar collections e types
@st.cache_data
def load_filters():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT collection, type FROM Collections_Types", conn)
    conn.close()
    return df

# Função para buscar quantidade de documentos
def fetch_document_count(collection, doc_type, max_pages):
    query_parts = []

    # Filtros de collection e type
    if collection:
        query_parts.append(f"collection:\"{collection}\"")
    if doc_type:
        query_parts.append(f"type:\"{doc_type}\"")

    # Filtro de número máximo de páginas
    query_parts.append(f"pages:[* TO {max_pages}]")

    # Construção da query final
    query = " AND ".join(query_parts) if query_parts else "*:*"

    params = {
        "q": query,
        "wt": "json",
        "rows": 0  # Apenas queremos o número total de documentos
    }

    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json().get("response", {}).get("numFound", 0)
    else:
        st.error(f"Erro ao buscar documentos: {response.status_code}")
        return 0

# Variável de controle para parar a busca
if "stop_search" not in st.session_state:
    st.session_state["stop_search"] = False

# Título da aplicação
st.title("Busca de Candidatas com Modelos de Comparação")

# Carregar filtros
df_filters = load_filters()

# Seleção de collection
distinct_collections = df_filters["collection"].unique()
collection = st.selectbox("Escolha a coleção:", ["Todas"] + list(distinct_collections))

# Seleção de type (dependente de collection)
if collection == "Todas":
    distinct_types = df_filters["type"].unique()
else:
    distinct_types = df_filters[df_filters["collection"] == collection]["type"].unique()
doc_type = st.selectbox("Escolha o tipo de documento:", ["Todos"] + list(distinct_types))

# Filtro para número máximo de páginas
max_pages = st.number_input("Número máximo de páginas do documento:", min_value=1, step=1, value=1)

# Seleção do modelo para comparação
comparison_model = select_comparison_model()

# Botão para buscar a quantidade de documentos
if st.button("Contar Documentos"):
    with st.spinner("Buscando quantidade de documentos..."):
        total_documents = fetch_document_count(
            collection if collection != "Todas" else None,
            doc_type if doc_type != "Todos" else None,
            max_pages
        )
        st.success(f"Total de documentos encontrados: {total_documents}")

# Placeholders para mensagens dinâmicas
status_placeholder = st.empty()  # Placeholder para mensagens gerais
status_comparisons_placeholder = st.empty()  # Placeholder para comparações realizadas
status_saved_placeholder = st.empty()  # Placeholder para comparações salvas

# Botão para iniciar a busca
if st.button("Iniciar Busca"):
    st.session_state["stop_search"] = False  # Reseta o controle de parada
    total_comparisons = 0
    total_saved = 0

    start = 0  # Define o início da busca
    status_placeholder.info("Iniciando busca sequencial e comparação de documentos...")

    while not st.session_state["stop_search"]:
        try:
            documents = search_documents(
                collection=collection if collection != "Todas" else None,
                doc_type=doc_type if doc_type != "Todos" else None,
                max_results=10, start=start
            )

            if len(documents) < 2:
                status_placeholder.warning("Número insuficiente de documentos para comparação. Encerrando a busca.")
                break

            # Realiza comparações entre os documentos
            for i, doc1 in enumerate(documents):
                for j in range(i + 1, len(documents)):
                    doc2 = documents[j]
                    if st.session_state["stop_search"]:
                        status_placeholder.warning("Busca interrompida pelo usuário.")
                        break

                    try:
                        doc1_id = doc1.get("id")
                        doc2_id = doc2.get("id")

                        # Carrega imagens
                        img1 = load_tif(doc1_id)
                        img2 = load_tif(doc2_id)

                        if isinstance(img1, Image.Image) and isinstance(img2, Image.Image):
                            # Usa o modelo selecionado para comparar imagens
                            result = comparison_model(img1, img2)

                            # Salva se a saída for relevante (output == 4)
                            if result["output"] == 4:
                                save_candidate(doc1_id, doc2_id, result["score"], comparison_model.__name__)
                                total_saved += 1

                        total_comparisons += 1

                        # Atualiza contadores dinâmicos no mesmo espaço
                        status_comparisons_placeholder.markdown(
                            f"### Comparações realizadas: **{total_comparisons}**"
                        )
                        status_saved_placeholder.markdown(
                            f"### Comparações salvas: **{total_saved}**"
                        )

                    except Exception as e:
                        status_placeholder.error(f"Erro ao processar documentos: {e}")

            # Avança para a próxima página
            start += 10
            time.sleep(1)  # Adiciona pausa para evitar sobrecarga

        except Exception as e:
            status_placeholder.error(f"Erro ao buscar documentos: {e}")
            break

    status_placeholder.success("Processo concluído ou interrompido.")

# Placeholders para mensagens dinâmicas
status_placeholder_group = st.empty()  # Placeholder para mensagens gerais sobre o processo por grupamento
status_comparisons_placeholder_group = st.empty()  # Placeholder para comparações realizadas
status_saved_placeholder_group = st.empty()  # Placeholder para comparações salvas

# Botão para busca por grupamento
if st.button("Buscar por Grupamento"):
    st.session_state["stop_search"] = False
    total_comparisons = 0
    total_saved = 0

    status_placeholder_group.info("Iniciando busca por grupamento...")

    # Itera sobre todas as combinações de collection e type
    for _, row in df_filters.iterrows():
        if st.session_state["stop_search"]:
            status_placeholder_group.warning("Busca interrompida pelo usuário.")
            break

        current_collection = row["collection"]
        current_type = row["type"]

        # Verifica a quantidade de documentos para o grupo
        document_count = fetch_document_count(current_collection, current_type, max_pages)
        if document_count < 2:
            status_placeholder_group.warning(f"Número insuficiente de documentos para o grupo: {current_collection} - {current_type}")
            continue

        # Exibe a query enviada e o número de documentos encontrados na categoria
        status_placeholder_group.markdown(
            f"**Query enviada:** `collection:\"{current_collection}\" AND type:\"{current_type}\"`\n"
            f"**Documentos encontrados nesta categoria:** {document_count}"
        )

        start = 0

        while not st.session_state["stop_search"]:
            try:
                documents = search_documents(collection=current_collection, doc_type=current_type, max_results=10, start=start)

                if len(documents) < 2:
                    break

                # Realiza comparações dentro do grupamento
                for i, doc1 in enumerate(documents):
                    for j in range(i + 1, len(documents)):
                        doc2 = documents[j]
                        if st.session_state["stop_search"]:
                            status_placeholder_group.warning("Busca interrompida pelo usuário.")
                            break

                        try:
                            doc1_id = doc1.get("id")
                            doc2_id = doc2.get("id")

                            # Carrega imagens
                            img1 = load_tif(doc1_id)
                            img2 = load_tif(doc2_id)

                            if isinstance(img1, Image.Image) and isinstance(img2, Image.Image):
                                # Usa o modelo selecionado para comparar imagens
                                result = comparison_model(img1, img2)

                                # Salva se a saída for relevante (output == 4)
                                if result["output"] == 4:
                                    save_candidate(doc1_id, doc2_id, result["score"], comparison_model.__name__)
                                    total_saved += 1
                            total_comparisons += 1

                            # Atualiza contadores dinâmicos no mesmo espaço
                            status_comparisons_placeholder_group.markdown(
                                f"### Comparações realizadas: **{total_comparisons}**"
                            )
                            status_saved_placeholder_group.markdown(
                                f"### Comparações salvas: **{total_saved}**"
                            )

                        except Exception as e:
                            status_placeholder_group.error(f"Erro ao processar documentos: {e}")

                # Avança para a próxima página
                start += 10

            except Exception as e:
                status_placeholder_group.error(f"Erro ao buscar documentos para o grupo {current_collection} - {current_type}: {e}")
                break

    status_placeholder_group.success("Busca por grupamento concluída ou interrompida.")


# Botão para parar a busca
def stop_search():
    st.session_state["stop_search"] = True

if st.button("Parar Busca"):
    stop_search()

# Rodapé
st.sidebar.markdown("**Desenvolvido por João Paulo Vieira Costa**\n\nEntre em contato: [jpcosta1990@gmail.com](mailto:jpcosta1990@gmail.com)")
