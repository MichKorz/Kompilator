# Używamy wersji 3.11 lub 3.12 (najnowsze stabilne)
FROM mcr.microsoft.com/devcontainers/python:3.11

# Unikamy generowania plików .pyc w kontenerze (śmieci)
ENV PYTHONDONTWRITEBYTECODE=1
# Buforowanie wyjścia (żeby print() pojawiał się od razu w konsoli)
ENV PYTHONUNBUFFERED=1

# Aktualizacja listy pakietów i instalacja narzędzi do maszyny wirtualnej
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    flex \
    bison \
    libcln-dev \
    && rm -rf /var/lib/apt/lists/*

# Ustawiamy katalog roboczy
WORKDIR /workspace