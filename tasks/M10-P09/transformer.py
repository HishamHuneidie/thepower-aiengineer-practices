"""Methods and classes to transform from text to embedding"""

from typing import Any
from sentence_transformers import SentenceTransformer

transformer = None

model: dict[str, Any] = {
    'name': 'paraphrase-multilingual-MiniLM-L12-v2',
    'dimensions': 384,
    'transformer': None,
}

def transform(text: str|list[str]) -> Any:
    """Convert text to embedding"""
    
    global model
    
    if model['transformer'] is None:
        model['transformer'] = SentenceTransformer(model['name'])
    
    return model['transformer'].encode(text, normalize_embeddings=True)