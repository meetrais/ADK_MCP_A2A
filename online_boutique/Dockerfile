FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install -e .
RUN pip install google-generativeai waitress

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

RUN echo '#!/bin/bash\n\
case "$SERVICE_TYPE" in\n\
  "mcp-server")\n\
    python -c "from online_boutique_manager.simple_mcp_server.boutique_mcp_server import run_server; run_server()"\n\
    ;;\n\
  "shipping-service")\n\
    python -m online_boutique_manager.sub_agents.shipping_service.agent\n\
    ;;\n\
  "customer-service")\n\
    python -m online_boutique_manager.sub_agents.customer_service.agent\n\
    ;;\n\
  "payment-processor")\n\
    python -m online_boutique_manager.sub_agents.payment_processor.agent\n\
    ;;\n\
  "catalog-service")\n\
    python -m online_boutique_manager.sub_agents.catalog_service.agent\n\
    ;;\n\
  "boutique-coordinator")\n\
    python -m online_boutique_manager.agent\n\
    ;;\n\
  *)\n\
    echo "Unknown SERVICE_TYPE: $SERVICE_TYPE"\n\
    echo "Available types: mcp-server, shipping-service, customer-service, payment-processor, catalog-service, boutique-coordinator"\n\
    exit 1\n\
    ;;\n\
esac' > /app/start_service.sh && chmod +x /app/start_service.sh

ENV SERVICE_TYPE=mcp-server

CMD ["/app/start_service.sh"]
