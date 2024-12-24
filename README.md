# Busca de Candidatas com Modelos de Comparação

Esta aplicação foi desenvolvida para buscar e comparar documentos de um repositório online usando diferentes modelos de comparação. A aplicação é construída com [Streamlit](https://streamlit.io/) e permite a busca, análise e comparação de documentos com base em filtros personalizados.

## Funcionalidades

### 1. **Busca de Documentos**
- Permite buscar documentos com base nos seguintes filtros:
  - **Coleção**: Escolha uma coleção específica ou todas as coleções disponíveis.
  - **Tipo de Documento**: Filtra os documentos com base no tipo (dependente da coleção selecionada).
  - **Número Máximo de Páginas**: Limita os documentos a um número máximo de páginas.
  - **Resultados por Página**: Define o número de resultados retornados por página.

### 2. **Contagem de Documentos**
- Permite contar o número de documentos disponíveis com base nos filtros aplicados, fornecendo uma visão geral do tamanho do conjunto de dados.

### 3. **Busca Sequencial**
- Realiza a busca de documentos sequencialmente e permite a comparação de pares de documentos usando um modelo selecionado.
- As comparações realizadas e salvas são atualizadas dinamicamente.

### 4. **Busca por Grupamento**
- Permite buscar documentos e realizar comparações agrupando por combinação de coleção e tipo de documento.
- A aplicação verifica a quantidade de documentos antes de iniciar as comparações dentro de cada grupo.

### 5. **Modelos de Comparação**
- Integra diferentes modelos para comparar documentos baseados em similaridade de imagem, incluindo:
  - **Skimage Similarity** (default).
  - Outros modelos customizáveis que podem ser configurados no código.

### 6. **Banco de Dados**
- Armazena os resultados das comparações relevantes no banco de dados SQLite.
- Cada comparação salva contém:
  - ID dos documentos comparados.
  - Similaridade calculada.
  - Modelo usado na comparação.

## Pré-requisitos

Certifique-se de ter os seguintes itens instalados:

- Python 3.8 ou superior
- Streamlit
- SQLite
- Bibliotecas adicionais listadas no arquivo `requirements.txt`.

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/jpcosta90/doc-comparing.git
   cd seu-repositorio
