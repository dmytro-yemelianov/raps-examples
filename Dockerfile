# RAPS Examples - Benchmark Runner
# Multi-stage build for running RAPS benchmarks

# Stage 1: Build RAPS from source (optional - can use pre-built binary)
FROM rust:1.88-slim as raps-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy RAPS source if available
COPY raps/ ./raps/ 2>/dev/null || true

# Build RAPS if source exists
RUN if [ -d "./raps/Cargo.toml" ]; then \
        cd raps && cargo build --release; \
    fi

# Stage 2: Runtime image with all benchmark tools
FROM ubuntu:24.04 as runtime

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    bc \
    time \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    jq \
    binutils \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for Python packages
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages for reporting
RUN pip install --no-cache-dir \
    matplotlib \
    pandas \
    jinja2 \
    markdown

# Install RAPS (try multiple methods)
# Method 1: Copy from builder stage
COPY --from=raps-builder /build/raps/target/release/raps /usr/local/bin/raps 2>/dev/null || true

# Method 2: Download pre-built binary if not built
RUN if [ ! -f /usr/local/bin/raps ]; then \
        ARCH=$(uname -m) && \
        if [ "$ARCH" = "x86_64" ]; then \
            curl -fsSL https://github.com/rapscli/raps/releases/latest/download/raps-linux-amd64 -o /usr/local/bin/raps || true; \
        elif [ "$ARCH" = "aarch64" ]; then \
            curl -fsSL https://github.com/rapscli/raps/releases/latest/download/raps-linux-arm64 -o /usr/local/bin/raps || true; \
        fi && \
        chmod +x /usr/local/bin/raps 2>/dev/null || true; \
    fi

# Set working directory
WORKDIR /workspace

# Copy benchmark files
COPY benchmarks/ ./benchmarks/
COPY scripts/ ./scripts/
COPY data/ ./data/ 2>/dev/null || true

# Create directories
RUN mkdir -p /workspace/reports /workspace/data/generated /workspace/data/samples

# Make all scripts executable
RUN find /workspace/benchmarks -name "*.sh" -exec chmod +x {} \;
RUN find /workspace/scripts -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
RUN find /workspace/scripts -name "*.py" -exec chmod +x {} \; 2>/dev/null || true

# Environment variables
ENV REPORT_DIR=/workspace/reports
ENV DATA_DIR=/workspace/data/generated

# Default command: run all benchmarks
CMD ["bash", "-c", "./scripts/run-all-benchmarks.sh"]
