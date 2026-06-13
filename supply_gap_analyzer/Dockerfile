ARG REGISTRY=registry.access.redhat.com
ARG IMAGE=ubi9/ubi-minimal
ARG TAG=latest
FROM ${REGISTRY}/${IMAGE}:${TAG}

WORKDIR /app

RUN microdnf update && \
    microdnf -y upgrade && \
    microdnf install -y curl ca-certificates tar gzip shadow-utils && \
    microdnf clean all

# Create non-root user
RUN useradd -r -u 1001 appuser

USER 1001

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN uv python install 3.14

# Copy dependency files first for better Docker layer caching
COPY --chown=1001:0 supply_gap_analyzer/pyproject.toml supply_gap_analyzer/uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy shared models and pricing analyzer source files
COPY --chown=1001:0 models ./models
COPY --chown=1001:0 pricing_analyzer ./pricing_analyzer

# Set working directory to pricing_analyzer so the listener can be run directly
WORKDIR /app/pricing_analyzer
ENV LOG_LEVEL=info

ENTRYPOINT ["uv", "run", "python", "supply_change_listener.py"]
CMD []