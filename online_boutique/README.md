# Online Boutique Multi-Agent System

This is an online boutique application built with a multi-agent architecture using Google ADK agents and MCP (Model Context Protocol).

## Architecture

- **Root Agent**: Online Boutique Coordinator - orchestrates the entire shopping experience
- **Sub-Agents**: Specialized agents for different e-commerce functions via A2A protocol
  - Shipping Service Agent
  - Customer Service Agent  
  - Payment Processor Agent
  - Catalog Service Agent
- **MCP Server**: Provides tools and services for the agents

## Deployment

This application is designed to run on Google Kubernetes Engine (GKE) with each component deployed as separate microservices.
