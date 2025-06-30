FROM python:3.12.3

WORKDIR /presen-ai

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# streamlitのデフォルトPORT番号
EXPOSE 8080

# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.enableCORS=false", "--server.port=8080"]