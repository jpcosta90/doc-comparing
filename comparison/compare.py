from skimage.metrics import structural_similarity as ssim
import numpy as np
import streamlit as st


# Função para seleção do modelo de comparação
def select_comparison_model():
    models = {
        "Skimage Similarity": compare_pil_images,
        "Modelo 1": compare_pil_images_model1,
        "Modelo 2": compare_pil_images_model2
    }
    selected_model_name = st.selectbox("Escolha o modelo para calcular a similaridade:", list(models.keys()))
    return models[selected_model_name]


def compare_pil_images(img1, img2, threshold=0.9):
    """
    Compara duas imagens em formato PIL e retorna 4 para semelhantes e 0 para diferentes.

    Args:
        img1 (PIL.Image): Primeira imagem a ser comparada.
        img2 (PIL.Image): Segunda imagem a ser comparada.
        threshold (float): Limiar de similaridade SSIM para considerar imagens semelhantes.

    Returns:
        int: 4 para imagens semelhantes, 0 para imagens diferentes.
    """
    # Converter imagens para escala de cinza e arrays NumPy
    img1_gray = np.array(img1.convert("L"))
    img2_gray = np.array(img2.convert("L"))

    # Redimensionar imagens para tamanhos iguais, se necessário
    if img1_gray.shape != img2_gray.shape:
        img2_gray = np.array(img2.resize(img1.size).convert("L"))

    # Calcular o índice de similaridade estrutural (SSIM)
    similarity_index, _ = ssim(img1_gray, img2_gray, full=True)

    # Retornar 4 para semelhantes e 0 para diferentes
    return {"output": 4 if similarity_index >= threshold else 0, "score": similarity_index}

def compare_pil_images_model1(img1, img2, threshold=0.5):
    """
    Teste
    """
    return {"output": 0, "score": 0.0}

def compare_pil_images_model2(img1, img2, threshold=0.5):
    """
    Teste
    """
    return {"output": 4, "score": 1.0}

