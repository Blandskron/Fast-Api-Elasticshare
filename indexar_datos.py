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
