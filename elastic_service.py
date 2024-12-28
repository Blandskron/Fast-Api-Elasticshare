from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from pydantic import BaseModel

# Conexión a Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Definir la aplicación FastAPI
app = FastAPI()

# Agregar el middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar a dominios específicos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para los datos
class Documento(BaseModel):
    id: int
    titulo: str
    contenido: str

# Ruta para indexar documentos
@app.post("/indexar/")
async def indexar_documento(doc: Documento):
    res = es.index(index="documentos", id=doc.id, body=doc.dict())
    return {"mensaje": "Documento indexado", "resultado": res}

# Ruta para buscar documentos
@app.get("/buscar/")
async def buscar_documento(query: str):
    query_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["titulo", "contenido"]
            }
        }
    }
    res = es.search(index="documentos", body=query_body)
    return {"resultados": [hit["_source"] for hit in res["hits"]["hits"]]}
