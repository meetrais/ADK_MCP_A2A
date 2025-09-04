FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install -e .
RUN pip install google-generativeai waitress gunicorn

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

RUN echo '#!/bin/bash\n\
case "$SERVICE_TYPE" in\n\
  "mcp-server")\n\
    gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 "online_boutique_manager.simple_mcp_server.boutique_mcp_server:app"\n\
    ;;\n\
  "shipping-service")\n\
    gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 "online_boutique_manager.sub_agents.shipping_service.agent:app"\n\
    ;;\n\
  "customer-service")\n\
    gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 "online_boutique_manager.sub_agents.customer_service.agent:app"\n\
    ;;\n\
  "payment-processor")\n\
    gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 "online_boutique_manager.sub_agents.payment_processor.agent:app"\n\
    ;;\n\
  "catalog-service")\n\
    gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 "online_boutique_manager.sub_agents.catalog_service.agent:app"\n\
    ;;\n\
  "boutique-coordinator")\n\
    gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 "online_boutique_manager.agent:app"\n\
    ;;\n\
  *)\n\
    echo "Unknown SERVICE_TYPE: $SERVICE_TYPE"\n\
    echo "Available types: mcp-server, shipping-service, customer-service, payment-processor, catalog-service, boutique-coordinator"\n\
    exit 1\n\
    ;;\n\
esac' > /app/start_service.sh && chmod +x /app/start_service.sh

ENV SERVICE_TYPE=mcp-server

CMD ["/app/start_service.sh"]
