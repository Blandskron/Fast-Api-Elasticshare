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

# Ruta para procesar la consulta con Elasticsearch y Llama
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

    # Generar respuesta con Llama
    input_text = f"Contexto: {contexto}\nPregunta: {consulta.prompt}\nRespuesta:"
    inputs = tokenizer(input_text, return_tensors="pt", max_length=1024, truncation=True)
    outputs = model.generate(inputs["input_ids"], max_length=512, num_return_sequences=1)
    respuesta = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return {"respuesta": respuesta}
