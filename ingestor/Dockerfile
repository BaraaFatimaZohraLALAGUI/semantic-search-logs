# ingestor/Dockerfile
FROM python:3.14.8
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir sentence-transformers elasticsearch==9.5.1
# bake the model into the image so startup doesn't download it
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
WORKDIR /app
COPY . .
CMD ["python", "-u", "receiver.py"]