FROM python:3.10-slim

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ARG PIP_DEFAULT_TIMEOUT=300
ARG PIP_RETRIES=10

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
	PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip && \
	python -m pip install \
	--no-cache-dir \
	--index-url ${PIP_INDEX_URL} \
	--trusted-host ${PIP_TRUSTED_HOST} \
	--timeout ${PIP_DEFAULT_TIMEOUT} \
	--retries ${PIP_RETRIES} \
	-r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
