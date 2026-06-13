ARG REGISTRY=registry.access.redhat.com
ARG IMAGE=ubi9/ubi-minimal
ARG TAG=latest
FROM ${REGISTRY}/${IMAGE}:${TAG}

WORKDIR /app

RUN microdnf install -y ca-certificates tar gzip shadow-utils && \
    microdnf clean all

RUN curl -LsSf https://astral.sh/uv/install.sh \
    | env UV_INSTALL_DIR=/usr/local/bin sh
RUN uv python install 3.14

# Create non-root user
RUN useradd -m -u 1001 appuser && \
    chown -R 1001:0 /app && \
    chmod -R g=u /app
USER 1001

# Copy dependency files first for better Docker layer caching
COPY --chown=1001:0 models ./models
COPY --chown=1001:0 sales_inventory_manager/pyproject.toml sales_inventory_manager/uv.lock* ./sales_inventory_manager/
WORKDIR /app/sales_inventory_manager
RUN uv sync --frozen

# Copy shared models and pricing analyzer source files
COPY --chown=1001:0 sales_inventory_manager ./sales_inventory_manager

ENV LOG_LEVEL=info

EXPOSE 8000

ENTRYPOINT ["uv", "run", "uvicorn", "inventory_manager_api:app"]
CMD ["--host", "0.0.0.0", "--port", "8000"]