# SML para realizar pruebas de software

## Descripción
Sistema para generar pruebas unitarias automáticamente para código Python usando modelos locales, análisis estático, RAG y ejecución con pytest.

## Objetivo
Automatizar la generación, ejecución y evaluación de pruebas unitarias para apoyar el proceso de testing de software.

## Tecnologías
- Python
- FastAPI
- React + Vite
- Pytest
- Pytest-cov
- Ollama
- Docker

## Arquitectura
Frontend React → Backend FastAPI → Generador de pruebas → Ejecutor pytest → Métricas/resultados

## Cómo ejecutar con Docker
docker compose up --build

## Cómo ejecutar backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

## Cómo ejecutar frontend
cd frontend
npm install
npm run dev

## Funcionalidades
- Generación de pruebas unitarias
- Generación en streaming
- Evaluación de cobertura
- Detección de posibles bugs
- Registro de resultados
- Uso de RAG
- Evaluación de oráculo

## Ejemplo de uso
Subir código Python → generar tests → ejecutar pruebas → revisar métricas