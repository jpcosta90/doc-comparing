import requests
from PIL import Image
import io
from industry_docs.industry_docs import get_tif_url

def load_tif(doc_id):
    """
    Carrega um documento TIF inteiro como uma lista de frames.
    """
    tif_url = get_tif_url(doc_id)
    response = requests.get(tif_url, stream=True)
    if response.status_code == 200:
        img = Image.open(io.BytesIO(response.content))
        frames = []
        for i in range(getattr(img, "n_frames", 1)):
            img.seek(i)
            frame = img.copy()
            frames.append(frame)
        return frames
    else:
        return None

def get_first_page(doc_id):
    """
    Retorna a primeira página de um documento TIF.
    """
    frames = load_tif(doc_id)
    return frames[0] if frames else None


