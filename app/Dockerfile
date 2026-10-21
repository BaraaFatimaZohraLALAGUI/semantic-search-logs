# app/Dockerfile
FROM python:3.14.8
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir sentence-transformers streamlit elasticsearch==9.5.1
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
WORKDIR /app
COPY ui.py .
EXPOSE 8501
CMD ["streamlit", "run", "ui.py", "--server.address", "0.0.0.0", "--server.headless", "true"]
