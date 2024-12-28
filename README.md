# Proyecto: Integración de FastAPI con Elasticsearch e IA

Este proyecto consta de los siguientes componentes:

1. **Elasticsearch**: Un motor de búsqueda que almacena documentos indexados y permite realizar consultas rápidas.
2. **FastAPI (Elastic Service)**: Una API para indexar y buscar documentos en Elasticsearch.
3. **FastAPI (AI Service)**: Una API que utiliza un modelo GPT-2 para generar respuestas basadas en el contexto de los datos almacenados en Elasticsearch.
4. **Script de Indexación**: Un script para generar y cargar datos aleatorios en Elasticsearch.

---

## **Requisitos Previos**

### **1. Instalación de Dependencias**

- **Docker**: Para ejecutar Elasticsearch.
- **Python 3.8+**: Para ejecutar FastAPI y los scripts asociados.

Instala las siguientes bibliotecas en tu entorno Python:

```bash
pip install fastapi uvicorn requests elasticsearch transformers torch
```

### **2. Configuración de Elasticsearch con Docker**

Crea un archivo `docker-compose.yml` con el siguiente contenido:

```yaml
version: '3.8'  # Asegúrate de usar la versión de Docker Compose adecuada

services:
  es01:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.2  # Última versión de Elasticsearch
    container_name: es01
    environment:
      - node.name=es01
      - cluster.name=es-docker-cluster
      - cluster.initial_master_nodes=es01
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false  # Desactivar seguridad para pruebas
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - data01:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"  # Exponer el puerto 9200
    networks:
      - elastic

volumes:
  data01:
    driver: local

networks:
  elastic:
    driver: bridge
```

Ejecuta el contenedor con:
```bash
docker-compose up -d
```

Verifica que Elasticsearch esté corriendo accediendo a `http://localhost:9200`.

---

## **Servicios FastAPI**

### **1. Elastic Service**

Este servicio permite indexar y buscar documentos en Elasticsearch.

#### **Código**: `elastic_service.py`

```python
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
```

Ejecuta el servicio con:
```bash
uvicorn elastic_service:app --reload --port 8000
```

Accede a Swagger en `http://127.0.0.1:8000/docs`.

---

### **2. AI Service**

Este servicio se conecta al Elastic Service para buscar documentos y utiliza un modelo GPT-2 para generar respuestas basadas en el contexto.

#### **Código**: `fastapi_service.py`

```python
from fastapi import FastAPI, HTTPException
from transformers import AutoTokenizer, AutoModelForCausalLM
from pydantic import BaseModel
import requests
from fastapi.middleware.cors import CORSMiddleware

model_name = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype="auto")

# Aplicación FastAPI
app = FastAPI(title="Servicio FastAPI con Elasticsearch e IA", description="API para indexar, buscar y generar respuestas con IA", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar a dominios específicos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para la consulta
class Consulta(BaseModel):
    prompt: str

# Ruta para procesar la consulta con Elasticsearch y GPT-2
@app.post("/consulta/")
async def procesar_consulta(consulta: Consulta):
    # Realizar búsqueda en Elasticsearch
    elastic_url = "http://localhost:8000/buscar/"
    response = requests.get(elastic_url, params={"query": consulta.prompt})
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error al conectar con Elasticsearch")
    
    resultados = response.json().get("resultados", [])
    if not resultados:
        return {"respuesta": "No se encontraron resultados en Elasticsearch."}

    # Concatenar resultados para el contexto
    contexto = " ".join([res["contenido"] for res in resultados])

    # Generar respuesta con GPT-2
    input_text = f"Contexto: {contexto}\nPregunta: {consulta.prompt}\nRespuesta:"
    inputs = tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True)
    outputs = model.generate(inputs["input_ids"], max_length=512, num_return_sequences=1)
    respuesta = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return {"respuesta": respuesta}
```

Ejecuta el servicio con:
```bash
uvicorn fastapi_service:app --reload --port 8001
```

Accede a Swagger en `http://127.0.0.1:8001/docs`.

---

## **Script para Indexar Datos Aleatorios**

Este script genera datos aleatorios y los envía al Elastic Service para indexarlos.

#### **Código**: `indexar_datos.py`

```python
import requests
import random

# URL del servicio para indexar documentos
url = "http://localhost:8000/indexar/"

# Generar datos aleatorios
def generar_datos():
    titulos = [
        "Cómo usar Python",
        "Introducción a Elasticsearch",
        "Tutorial de FastAPI",
        "Guía de DevOps",
        "Inteligencia Artificial y Machine Learning",
    ]
    contenidos = [
        "Python es un lenguaje versátil para desarrollo de software.",
        "Elasticsearch es un motor de búsqueda basado en Lucene.",
        "FastAPI es un framework moderno para construir APIs en Python.",
        "DevOps incluye herramientas como Docker, Kubernetes y Terraform.",
        "La IA y el ML están transformando industrias globalmente.",
    ]

    datos = []
    for i in range(10):  # Generar 10 documentos aleatorios
        datos.append({
            "id": i,
            "titulo": random.choice(titulos),
            "contenido": random.choice(contenidos),
        })
    return datos

# Enviar datos a Elasticsearch
def enviar_datos(datos):
    for doc in datos:
        response = requests.post(url, json=doc)
        if response.status_code == 200:
            print(f"Documento {doc['id']} indexado correctamente.")
        else:
            print(f"Error al indexar documento {doc['id']}: {response.text}")

# Ejecutar el script
if __name__ == "__main__":
    datos = generar_datos()
    enviar_datos(datos)
```

Ejecuta el script con:
```bash
python indexar_datos.py
```

---

## **Pruebas de la API**

### **Indexar un Documento**
```bash
curl -X POST "http://localhost:8000/indexar/" -H "Content-Type: application/json" -d '{"id": 1, "titulo": "Python", "contenido": "Python es un lenguaje versátil"}'
```

### **Buscar Documentos**
```bash
curl -X GET "http://localhost:8000/buscar/?query=Python"
```

### **Generar Respuesta con IA**
```bash
curl -X POST "http://localhost:8001/consulta/" -H "Content-Type: application/json" -d '{"prompt": "¿Qué es Python?"}'
```

---

## **Conclusión**
Con este proyecto, has integrado Elasticsearch, FastAPI y un modelo GPT-2 para crear un sistema que combina búsqueda de datos y generación de respuestas inteligentes. Puedes personalizarlo según tus necesidades y ampliar sus funcionalidades.

Si tienes preguntas o necesitas soporte, ¡no dudes en pedir ayuda!

