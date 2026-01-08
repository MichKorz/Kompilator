# Używamy wersji 3.11 lub 3.12 (najnowsze stabilne)
FROM mcr.microsoft.com/devcontainers/python:3.11

# Unikamy generowania plików .pyc w kontenerze (śmieci)
ENV PYTHONDONTWRITEBYTECODE=1
# Buforowanie wyjścia (żeby print() pojawiał się od razu w konsoli)
ENV PYTHONUNBUFFERED=1

# Opcjonalnie: Instalacja dodatkowych narzędzi systemowych
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     vim \
#     && rm -rf /var/lib/apt/lists/*

# Ustawiamy katalog roboczy
WORKDIR /workspace