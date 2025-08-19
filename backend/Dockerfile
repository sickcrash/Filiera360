#FROM python:3.8-slim
#
#WORKDIR /app
#ENV PYTHONUNBUFFERED=1 \
#    FLASK_APP=app.py \
#    FLASK_ENV=development \
#    FLASK_DEBUG=1
#

#COPY app.py requirements.txt ./
#COPY prompts_variables_storage.py ./
#COPY database_mongo/ ./database_mongo/
#
#RUN pip install --upgrade pip && \
#    pip install -r requirements.txt
#
#EXPOSE 5000
#CMD ["flask", "--app", "app.py", "run", "--host=0.0.0.0", "--debug", "--reload"]


FROM python:3.8-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app/__init__.py \
    FLASK_ENV=development \
    FLASK_DEBUG=1 \
    PYTHONPATH=/app

# Copy requirements first for better caching
COPY requirements.txt ./

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the entire application code
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--debug", "--reload"]