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
COPY --chown=1001:0 supply_gap_analyzer/pyproject.toml supply_gap_analyzer/uv.lock* ./supply_gap_analyzer/
WORKDIR /app/supply_gap_analyzer
RUN uv sync --frozen

# Copy shared models and pricing analyzer source files
COPY --chown=1001:0 supply_gap_analyzer ./supply_gap_analyzer

ENV LOG_LEVEL=info

ENTRYPOINT ["uv", "run", "python", "supply_change_listener.py"]
CMD []