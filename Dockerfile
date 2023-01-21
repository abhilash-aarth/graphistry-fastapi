# 
FROM python:3.10.9 as requirements-stage

# 
WORKDIR /tmp

# 
RUN pip install poetry

# 
COPY ./pyproject.toml ./poetry.lock* /tmp/

# 
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# 
FROM python:3.10.9

# 
WORKDIR /graphistry-fastapi

# 
COPY --from=requirements-stage /tmp/requirements.txt /graphistry-fastapi/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /graphistry-fastapi/requirements.txt

# 
COPY ./app /graphistry-fastapi/app

# 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
