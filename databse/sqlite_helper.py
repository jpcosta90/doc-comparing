import sqlite3
from typing import List, Optional, Tuple
import os

# Caminho do banco de dados
DB_PATH = os.path.join("databse", "document_comparisons.db")

def initialize_database():
    """
    Inicializa o banco de dados e cria a tabela Comparacoes, se não existir.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Criação da tabela
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Comparacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc1_id TEXT NOT NULL,
        doc2_id TEXT NOT NULL,
        similarity_score FLOAT NOT NULL,
        comparison_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_feedback INTEGER NULL,
        comments TEXT NULL
    )
    """)
    conn.commit()
    conn.close()


def save_comparison(doc1_id: str, doc2_id: str, 
                    user_feedback: Optional[int] = None, comments: Optional[str] = None):
    """
    Insere um registro de comparação no banco de dados.
    Atualiza o registro se ele já existir.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Tenta inserir um novo registro
        cursor.execute("""
        INSERT INTO Comparacoes (doc1_id, doc2_id, user_feedback, comments)
        VALUES (?, ?, ?, ?)
        """, (doc1_id, doc2_id, user_feedback, comments))
    except sqlite3.IntegrityError:
        # Atualiza o registro existente se a combinação doc1_id e doc2_id já existir
        update_comparison(doc1_id, doc2_id, user_feedback, comments, conn)

    conn.commit()
    conn.close()

def update_comparison(doc1_id: str, doc2_id: str, 
                      user_feedback: Optional[int] = None, comments: Optional[str] = None,
                      connection=None):
    """
    Atualiza um registro existente no banco de dados com base em doc1_id e doc2_id.
    """
    close_connection = False
    if connection is None:
        connection = sqlite3.connect(DB_PATH)
        close_connection = True

    cursor = connection.cursor()

    # Atualiza os campos user_feedback e comments
    cursor.execute("""
    UPDATE Comparacoes
    SET user_feedback = ?, comments = ?, comparison_date = CURRENT_TIMESTAMP
    WHERE doc1_id = ? AND doc2_id = ?
    """, (user_feedback, comments, doc1_id, doc2_id))

    if close_connection:
        connection.commit()
        connection.close()

def fetch_comparisons() -> List[Tuple]:
    """
    Retorna todos os registros da tabela Comparacoes.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Comparacoes")
    results = cursor.fetchall()

    conn.close()
    return results

def fetch_table_structure(table_name: str) -> List[Tuple]:
    """
    Retorna a estrutura da tabela especificada.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name});")
    structure = cursor.fetchall()

    conn.close()
    return structure

def fetch_tables() -> List[str]:
    """
    Retorna uma lista de todas as tabelas no banco de dados.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]

    conn.close()
    return tables

def comparison_exists(doc1_id, doc2_id, connection=None):
    """
    Verifica se a comparação entre dois documentos já existe no banco de dados.
    """
    close_connection = False
    if connection is None:
        connection = sqlite3.connect(DB_PATH)
        close_connection = True

    cursor = connection.cursor()
    cursor.execute("""
    SELECT 1 FROM Comparacoes WHERE doc1_id = ? AND doc2_id = ?
    """, (doc1_id, doc2_id))
    exists = cursor.fetchone()

    if close_connection:
        connection.close()

    return exists is not None


def get_new_comparison(documents, connection=None):
    """
    Retorna dois documentos que ainda não foram comparados.
    """
    close_connection = False
    if connection is None:
        connection = sqlite3.connect(DB_PATH)
        close_connection = True

    cursor = connection.cursor()
    for i in range(len(documents) - 1):
        doc1_id = documents[i]['id']
        doc2_id = documents[i + 1]['id']
        if not comparison_exists(doc1_id, doc2_id, connection):
            if close_connection:
                connection.close()
            return [documents[i], documents[i + 1]]

    if close_connection:
        connection.close()

    return None

def save_or_update_comparison(doc1_id, doc2_id, user_feedback, comments, connection=None):
    """
    Salva ou atualiza uma comparação no banco de dados.
    """
    if comparison_exists(doc1_id, doc2_id, connection):
        update_comparison(doc1_id, doc2_id, user_feedback, comments, connection)
    else:
        save_comparison(doc1_id, doc2_id, user_feedback, comments)

# Inicializa a tabela Candidatas
def initialize_candidates_table():
    """
    Cria a tabela Candidatas no banco de dados, se não existir.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Candidatas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc1_id TEXT NOT NULL,
        doc2_id TEXT NOT NULL,
        similarity_score FLOAT NOT NULL,
        modelo TEXT NOT NULL,
        comparison_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(doc1_id, doc2_id, modelo)
    )
    """)
    conn.commit()
    conn.close()

# Salva uma comparação candidata
def save_candidate(doc1_id, doc2_id, similarity_score, modelo):
    """
    Insere uma comparação candidata na tabela Candidatas.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO Candidatas (doc1_id, doc2_id, similarity_score, modelo)
        VALUES (?, ?, ?, ?)
        """, (doc1_id, doc2_id, similarity_score, modelo))
    except sqlite3.IntegrityError:
        pass  # Evita duplicatas

    conn.commit()
    conn.close()

# Conta os registros na tabela Candidatas
def count_candidates():
    """
    Retorna o número de registros na tabela Candidatas.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Candidatas")
    count = cursor.fetchone()[0]

    conn.close()
    return count

# Busca candidatos na tabela
def fetch_candidates(limit=100):
    """
    Retorna os registros da tabela Candidatas, limitados ao valor especificado.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Candidatas LIMIT ?", (limit,))
    candidates = cursor.fetchall()

    conn.close()
    return candidates
