import streamlit as st
from utils.document_utils import load_tif
from comparison.compare import select_comparison_model
from industry_docs.industry_docs import search_documents, get_tif_url, view_document
from databse.sqlite_helper import initialize_database, initialize_candidates_table, save_comparison, update_comparison, comparison_exists, get_new_comparison, fetch_candidates


# Inicializa o banco de dados
initialize_database()
initialize_candidates_table()

# Função para visualizar documento TIF com navegação interativa por páginas
def display_tif_with_arrows(doc_id):
    if f"frames_{doc_id}" not in st.session_state:
        st.session_state[f"frames_{doc_id}"] = load_tif(doc_id)
        st.session_state[f"page_{doc_id}"] = 0

    frames = st.session_state[f"frames_{doc_id}"]
    if frames:
        total_pages = len(frames)
        current_page = st.session_state[f"page_{doc_id}"]

        col_left, col_middle, col_right = st.columns([1, 6, 1])

        # Botão para voltar página
        with col_left:
            if st.button("⬅", key=f"prev_{doc_id}"):
                st.session_state[f"page_{doc_id}"] = max(0, current_page - 1)

        # Exibir página atual
        with col_middle:
            st.write(f"Página {current_page + 1} de {total_pages}")

        # Botão para avançar página
        with col_right:
            if st.button("➡", key=f"next_{doc_id}"):
                st.session_state[f"page_{doc_id}"] = min(total_pages - 1, current_page + 1)

        # Exibir imagem da página atual
        st.image(frames[st.session_state[f"page_{doc_id}"]], caption=f"Visualizando documento {doc_id}", use_column_width=True)
    else:
        st.error("Erro ao carregar o documento. Verifique o ID e tente novamente.")

# Função para atualizar automaticamente a imagem com novo ID
def update_document(doc_key):
    new_id = st.text_input(f"Alterar ID do documento {doc_key}", value=st.session_state["docs"][doc_key]['id'], key=f"id_input_{doc_key}")
    if new_id != st.session_state["docs"][doc_key]["id"]:
        new_frames = load_tif(new_id)
        if new_frames:
            st.session_state[f"frames_{new_id}"] = new_frames
            st.session_state[f"page_{new_id}"] = 0
            st.session_state["docs"][doc_key]["id"] = new_id
            st.success(f"Documento {doc_key} atualizado com sucesso!")
        else:
            st.error(f"Documento com ID {new_id} não encontrado.")
# Função para carregar nova comparação ignorando as existentes
def load_new_comparison():
    results = search_documents(2, st.session_state.get("current_start", 0), collection_param, max_pages)
    if results:
        docs = results['response']['docs']
        new_comparison = get_new_comparison(docs)
        if new_comparison:
            st.session_state["docs"] = new_comparison
            st.session_state["current_start"] += 2
        else:
            st.warning("Nenhuma nova comparação disponível.")
            
# Escala de comparação de documentos com cálculo e botão salvar/atualizar
# Escala de comparação de documentos com cálculo e botão salvar/atualizar
def display_comparison_scale(doc_ids, img1=None, img2=None):
    scale_labels = [
        "Totalmente Diferente",
        "Pouco Relacionado",
        "Semelhanças Moderadas",
        "Semelhança Considerável",
        "Exatamente o Mesmo Layout",
        "Exatamente o Mesmo Documento"
    ]

    # Calcular similaridade
    comparison_model = select_comparison_model()
    if img1 and img2 and st.button("Calcular Similaridade", key=f"calc_{doc_ids[0]}_{doc_ids[1]}"):
        similarity_score = comparison_model(img1, img2)
        st.session_state[f"similarity_{doc_ids[0]}_{doc_ids[1]}"] = similarity_score
        st.success(f"**Similaridade Calculada:** {similarity_score:.2f}")

    # Slider de avaliação
    level = st.slider(
        f"Avalie a similaridade entre os documentos {doc_ids[0]} e {doc_ids[1]}",
        min_value=0,
        max_value=5,
        value=0,
        key=f"scale_{doc_ids[0]}_{doc_ids[1]}"
    )

    st.write(f"**Descrição da avaliação:** {scale_labels[level]}")
    detailed_descriptions = [
        "Layout completamente diferente. Nenhum elemento em comum (ex.: um recibo e uma página de livro). O conteúdo não está relacionado.",
        "Documentos têm objetivos ou finalidades similares, mas os layouts são incompatíveis. Pouca sobreposição nos elementos estruturais (ex.: um formulário e uma planilha de cálculo).",
        "Apresentam algumas semelhanças visuais ou estruturais, como uso de caixas de texto ou cabeçalhos. A relação entre os documentos ainda é fraca em termos de layout e conteúdo.",
        "Estruturas de layout próximas (ex.: tabelas organizadas de maneira similar ou formulários com campos equivalentes). Diferenças no conteúdo predominam, mas os layouts começam a apresentar mais pontos de correspondência.",
        "Documentos têm layouts idênticos, mas o conteúdo é completamente diferente (ex.: mesmo formulário com preenchimentos distintos).",
        "Layout e conteúdo idênticos, sem nenhuma modificação perceptível. Pode incluir cópias ou reimpressões de um mesmo documento."
    ]
    st.write(detailed_descriptions[level])

    # Caixa de texto para comentários
    comments = st.text_area("Adicione comentários (opcional):", key=f"comments_{doc_ids[0]}_{doc_ids[1]}")

    # Verificar se já existe uma comparação para os documentos
    if st.button("Salvar/Atualizar Comparação", key=f"save_{doc_ids[0]}_{doc_ids[1]}"):
        if comparison_exists(doc_ids[0], doc_ids[1]):
            update_comparison(
                doc1_id=doc_ids[0],
                doc2_id=doc_ids[1],
                user_feedback=level,
                comments=comments
            )
            st.success("Comparação atualizada com sucesso!")
        else:
            save_comparison(
                doc1_id=doc_ids[0],
                doc2_id=doc_ids[1],
                user_feedback=level,
                comments=comments
            )
            st.success("Comparação salva com sucesso!")

        # Carregar a próxima comparação automaticamente
        with st.spinner("Carregando próxima comparação..."):
            load_candidates_comparison()


# Função para carregar documentos da tabela Candidatas, ignorando os que já existem em Comparacoes
def load_candidates_comparison():
    """
    Carrega documentos da tabela Candidatas que ainda não estão na tabela Comparacoes.
    """
    candidates = fetch_candidates(limit=2)  # Buscar apenas 2 novos candidatos

    if candidates:
        st.session_state["docs"] = [{"id": candidates[0][1]}, {"id": candidates[0][2]}]
    else:
        st.warning("Nenhuma nova comparação disponível na tabela Candidatas.")





# Aplicação Streamlit
st.title("Industry Documents Library - Comparação de Documentos")

# Manter o estado da consulta
if "docs" not in st.session_state:
    st.session_state["docs"] = None

if "current_start" not in st.session_state:
    st.session_state["current_start"] = 0

# Seleção de coleções
collection = st.selectbox(
    "Escolha a coleção:",
    ["Todas", "tobacco", "pharma", "food", "chemical", "fossil"]
)
collection_param = None if collection == "Todas" else collection

# Parâmetros
start_page = st.number_input("Página inicial:", min_value=0, step=1, value=0)
max_pages = st.number_input("Número máximo de páginas:", min_value=1, step=1, value=1)

# Botão de busca direta na API
if st.button("Buscar da API"):
    with st.spinner("Buscando documentos..."):
        load_new_comparison()

# Botão adicional para carregar da tabela Candidatas
if st.button("Buscar da Tabela Candidatas"):
    with st.spinner("Buscando documentos da tabela..."):
        load_candidates_comparison()

# Exibir os documentos armazenados
if st.session_state["docs"]:
    docs = st.session_state["docs"]

    # Exibindo os resultados lado a lado para comparação
    if len(docs) >= 2:
        col1, col2 = st.columns(2)

        with col1:
            doc1 = docs[0]
            update_document(0)
            st.write(f"Data: {doc1.get('documentdate', 'Desconhecida')}")
            st.write(f"Tipo: {', '.join(doc1.get('type', []))}")
            st.write(f"Páginas: {doc1.get('pages', 'N/A')}")
            img1 = load_tif(doc1['id'])[0]  # Usar a primeira página como referência
            display_tif_with_arrows(doc1['id'])

        with col2:
            doc2 = docs[1]
            update_document(1)
            st.write(f"Data: {doc2.get('documentdate', 'Desconhecida')}")
            st.write(f"Tipo: {', '.join(doc2.get('type', []))}")
            st.write(f"Páginas: {doc2.get('pages', 'N/A')}")
            img2 = load_tif(doc2['id'])[0]  # Usar a primeira página como referência
            display_tif_with_arrows(doc2['id'])

        # Escala única para comparar os dois documentos
        display_comparison_scale([doc1['id'], doc2['id']], img1, img2)

    elif len(docs) < 2:
        st.warning("Menos de dois documentos encontrados para comparação.")
    else:
        st.warning("Nenhum documento encontrado.")

# Rodapé
st.sidebar.markdown("**Desenvolvido por João Paulo Vieira Costa**\n\nEntre em contato: [jpcosta1990@gmail.com](mailto:jpcosta1990@gmail.com)\n\nEsta aplicação utiliza a Industry Documents Library para facilitar a pesquisa e a comparação de documentos.")
