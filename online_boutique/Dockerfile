# Use a slim, recent version of Python as the base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies. 'curl' is necessary for the HEALTHCHECK.
# 'build-essential' is good practice if any Python packages need to compile C extensions.
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code into the container
COPY . .

# Install Python dependencies defined in pyproject.toml
RUN pip install -e .

# Install any additional dependencies not managed by pyproject.toml
RUN pip install google-generativeai waitress

# Expose the port that the application server will run on
EXPOSE 8080

# Define a health check to let Kubernetes know if the application is responsive.
# This will hit the /health endpoint that was added to the Python code.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Create a startup script that can run different services based on an environment variable.
# Note: This assumes your directory 'simple-mcp-server' is renamed to 'simple_mcp_server'
# to be a valid Python package.
RUN echo '#!/bin/bash\n\
case "$SERVICE_TYPE" in\n\
  "mcp-server")\n\
    python -c "from online_boutique_manager.simple_mcp_server.boutique_mcp_server import run_server; run_server()"\n\
    ;;\n\
  "product-manager")\n\
    python -c "from online_boutique_manager.sub_agents.product_manager.agent import run_server; run_server()"\n\
    ;;\n\
  "shipping-service")\n\
    python -c "from online_boutique_manager.sub_agents.shipping_service.agent import run_server; run_server()"\n\
    ;;\n\
  "customer-service")\n\
    python -c "from online_boutique_manager.sub_agents.customer_service.agent import run_server; run_server()"\n\
    ;;\n\
  "payment-processor")\n\
    python -c "from online_boutique_manager.sub_agents.payment_processor.agent import run_server; run_server()"\n\
    ;;\n\
  "catalog-service")\n\
    python -c "from online_boutique_manager.sub_agents.catalog_service.agent import run_server; run_server()"\n\
    ;;\n\
  "boutique-coordinator")\n\
    python -c "from online_boutique_manager.agent import run_server; run_server()"\n\
    ;;\n\
  *)\n\
    echo "Unknown SERVICE_TYPE: $SERVICE_TYPE"\n\
    echo "Available types: mcp-server, product-manager, shipping-service, customer-service, payment-processor, catalog-service, boutique-coordinator"\n\
    exit 1\n\
    ;;\n\
esac' > /app/start_service.sh && chmod +x /app/start_service.sh

# Set a default service to run if SERVICE_TYPE is not specified.
ENV SERVICE_TYPE=mcp-server

# The default command to run when the container starts.
CMD ["/app/start_service.sh"]
