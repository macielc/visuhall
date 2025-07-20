# 1. Usar uma imagem base oficial do Python
FROM python:3.11-slim

# 2. Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# 3. Copiar o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# 4. Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar os arquivos da aplicação e o frontend
COPY *.py /app/
COPY frontend/ /app/frontend/

# 6. Expor a porta que o Flask usará
EXPOSE 8000

# 7. Definir o comando para rodar a aplicação
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8000", "app:app"] 