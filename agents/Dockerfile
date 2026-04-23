# Shared Dockerfile for all agents (ingestor, summarizer, prioritizer, formatter)
# Build args: AGENT_NAME (folder name), PORT (port number)
ARG PYTHON_VERSION=3.11-slim
FROM python:${PYTHON_VERSION}

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared /app/shared

# Copy agent-specific code (injected via ARG at build time)
ARG AGENT_NAME
COPY agents/${AGENT_NAME} /app/agents/${AGENT_NAME}

WORKDIR /app/agents/${AGENT_NAME}

# Expose port (injected via ARG at build time)
ARG PORT
EXPOSE ${PORT}

# Set environment variable for port (can be used in CMD)
ENV AGENT_PORT=${PORT}

# Start agent
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${AGENT_PORT}"]
