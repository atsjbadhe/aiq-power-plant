***Power Plant Visualization***

A full-stack application for visualizing the annual net generation of U.S. power plants based on EPA's eGRID 2023 dataset.

## Table of Contents
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setup and Installation](#setup-and-installation)
  - [Authentication Setup](#authentication-setup)
- [Usage](#usage)
- [Features](#features)
- [Architecture](#architecture)
- [Handling Changing Requirements](#handling-changing-requirements)
- [Monitoring](#monitoring)
- [Technology Choices](#technology-choices)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/atsjbadhe/aiq-power-plant.git
   cd aiq-padministrationower-plant
   ```

2. Build and run the containers:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API swagger: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001 (login with minioadmin/minioadmin)

## Usage
1. **Login**
   - Login (with rightside top option) using your Google credentials.
   - Once succesfull, you will be presented with main screen where you can upload and query data
     
2. **Upload Data**:
   - Download the GEN23 sheet from the [EPA eGRID 2023 dataset](https://www.epa.gov/system/files/documents/2025-01/egrid2023_data_rev1.xlsx)
   - Save as CSV and upload using the application interface or via MinIO console

3. **Visualize Data**:
   - Select a state from the dropdown
   - Specify the number of top plants to view
   - Click "Visualize" to see the chart and data table
   - 
4. **Logout**
   - Logout from righthand top menu
     
## Features

- **Data Ingestion**: Upload CSV files from EPA's eGRID dataset to S3-compatible storage
- **Data Visualization**: Interactive charts showing top power plants by net generation
- **Filtering**: Filter power plants by U.S. state
- **User Interface**: Simple User Interface
- **Authentication**: Secure user authentication via Clerk (social media authentication)
- **Comprehensive Logging**: Application logs, error logs, and audit logs for security and compliance

## Architecture

The solution operates within a typical web application context, leveraging cloud-native principles through containerization. It interfaces with external object storage for data input and provides a web-based interface for user interaction

Refer to  [Software Architecture Document](./wiki/Power-Plan-Visualization-‐-Architecture-Document) for more details.

### Conceptual Architecture

![Conceptual View](./docs/img/aiq-Conceptual.jpg) 

![More Details](./docs/AIQ-Architecture.pdf)

**Data Sources:** The process begins with raw data, exemplified by a "Source file" which is specifically identified as a CSV (Comma Separated Values) file. This indicates that the system primarily ingests structured, delimited data.

**Orchestration:** This central component represents the core data pipeline, handling the transformation and management of data. It consists of three sequential stages:

**Data Ingestion:** This stage is responsible for reading and taking in raw data from the specified data sources (e.g., the CSV file).

**Data Processing:** After ingestion, the raw data undergoes various transformations, cleaning, aggregation, or enrichment processes to make it suitable for analysis and storage.

**Data Storage:** The processed data is then persisted in a storage mechanism, making it available for retrieval and further use.

**Visualisation:** This component is responsible for presenting the processed data in a human-understandable format, likely through charts, graphs, dashboards, or reports, as suggested by the visualization icon. It retrieves data from "Data Storage" to create these visualizations.

**Business User:** The ultimate consumer of the system's output is the "Business User." They interact with the "Visualisation" component by sending "Query" requests to obtain insights from the processed data. The visualization component, in turn, performs "Retrieval" from the "Data Storage" to fulfill these queries.


In essence, the system conceptually takes raw data, processes it through a defined pipeline, stores it, and then allows business users to query and visualize this processed data to gain insights. It highlights the logical separation of concerns within the data flow

Refer to  [Software Architecture Document](./wiki/Power-Plan-Visualization-‐-Architecture-Document) for more details.

### Logical Architecture

![Logical Architecture](./docs/img/aiq-HIghLevelView.jpg)


This diagram provides a high-level architectural overview of a system, organized into several logical layers and domains. It outlines the major functional blocks and their responsibilities.

**Main Application Layers:**

**User Layer:** Represents the end-users interacting with the system.

**User Interface Layer:** Provides the interaction points for users, including File Upload, Query capabilities, and Visualization of data.

**API Management Layer:** Manages and secures API access, featuring an API Gateway, API Security mechanisms, and Traffic Manager for routing and control.

**Business Core/API Layer:** Contains the core business logic and functionalities. This includes File Upload API, Top N Power Plants (suggesting domain-specific logic), Filter API, and data processing steps like Extract, Transform, and Store.

**Persistent Layer:** Represents the data storage mechanism, depicted as a bucket icon (likely object storage or a database).


**Cross-Cutting Concerns and Operational Domains:**

**Control Layer:** Handles overarching management aspects such as AuthN & AuthZ (Authentication and Authorization), Identity Store, Governance, and Administration of the system.

**DevOps:** Encompasses the practices and tools for development and operations, including Container Registry, CI/CD (Continuous Integration/Continuous Deployment), Containers (for deploying components), and Code Repo (source code repository).

**Security:** Focuses on security concerns across different levels: Platform security, Application security, and Data security.

**Ops and Monitoring:** Deals with the operational aspects and system health, including Analytics, Performance monitoring, Audit and Error Handling, and Configuration management.


Logical architecture depicts clear separation of concerns, supporting user interaction, API management, core business logic, and persistent storage, while also highlighting crucial operational, security, and governance aspects.

Refer to  [Software Architecture Document](./wiki/Power-Plan-Visualization-‐-Architecture-Document) for more details.

### Deployment Architecture

![DeploymentView](./docs/img/aiq-DeploymentView.jpg)

Deployment Architecture depicts, Client (browser) accessing a Frontend via HTTPS. User authentication is handled through Google Social Media Authentication using OAuth2, resulting in a token for subsequent API calls. The Frontend communicates with a Backend via request/response. Both Frontend and Backend are deployed as Docker containers within a Container Orchestration environment. The Backend interacts with Minio Object Storage (also containerized) for data persistence. All Docker images (Frontend, Backend, Minio) are managed in a central Container Registry.

Refer to  [Software Architecture Document](./wiki/Power-Plan-Visualization-‐-Architecture-Document) for more details.

### Infrastructure Architecture

![InfraView](./docs/img/aiq-InfraView.jpg)

Application can be hosted on any cloud provider. However, Azure is being used as AIQ uses Azure extensively.

Here's a summary:

**1. External Interactions:**
* **End User:** Accesses the system.
* **DDoS Protection:** Protects the entry point from Distributed Denial of Service attacks.
* **Social Media Authentication (Google):** External service for user authentication.
* **DevOps CI/CD (Github, Terraform):** External tools used for continuous integration, continuous deployment, and infrastructure as code.

**2. Azure Infrastructure (Organized by Subnets):**

* **Gateway Subnet:**
    * **Application Gateway:** Acts as the entry point and reverse proxy for web traffic, distributing requests to the application.
    * **WAF (Web Application Firewall):** Provides security against common web exploits.
* **App Subnet:**
    * **Frontend:** Hosts the user-facing application components.
    * **Backend:** Hosts the core application logic and APIs.
* **Storage Subnet:**
    * **Object Storage:** Provides scalable storage for data (e.g., Minio from previous diagrams, or Azure Blob Storage).
* **Shared Subnet:**
    * **Container Registry:** Stores Docker images for deployment (e.g., Azure Container Registry).
    * **Key Vault:** Securely stores and manages cryptographic keys, secrets, and other sensitive information.
    * **APIM (API Management):** Manages APIs, likely for exposing backend services.
* **Tenant Shared Subnet:** This subnet consolidates various shared Azure services crucial for operations, monitoring, and security across the tenant:
    * **Monitor, App Insights, Security Center, Advisor, Service Health, Network Watcher:** Tools for monitoring application performance, health, security posture, and network diagnostics.
    * **Cost Management & Billing, Log Analytics Workspace:** For cost optimization and centralized log collection/analysis.
    * **Azure DevOps, Policy, Metrics, Defender:** Tools for DevOps practices, enforcing policies, collecting performance metrics, and threat protection.

**Overall Security & Networking:**
* Throughout the diagram, shield icons indicate **network security groups (NSGs)** or other security controls at the subnet level, enforcing network segmentation and access policies.
* The `<->` arrows denote network peering or routing between subnets.
* The cloud icon signifies the overall presence within the Azure cloud.

Refer to  [Software Architecture Document](./wiki/Power-Plan-Visualization-‐-Architecture-Document) for more details.

## Handling Changing Requirements

Refer to  [Software Architecture Document](./wiki/Power-Plan-Visualization-‐-Architecture-Document) for more details.

## Monitoring

Refer to  [Software Architecture Document](./wiki/Power-Plan-Visualization-‐-Architecture-Document) for more details.

## Technology Choices

### Frontend
- **React**: For building interactive user interfaces
- **TypeScript**: For type safety and better developer experience
- **Material UI**: For consistent and responsive design components
- **Recharts**: For data visualization with charts
- **Vite**: For faster development and optimized builds

### Backend
- **FastAPI**: For high-performance, async-capable API development
- **Pandas**: For efficient data processing and analysis
- **Boto3/MinIO**: For S3-compatible object storage interaction
- **Pydantic**: For data validation and settings management

### Infrastructure (local)
- **Docker**: For containerization and consistent environments
- **Docker Compose**: For multi-container application orchestration
- **MinIO**: For S3-compatible object storage
- **Nginx**: For serving static files and API routing

Refer to  [Software Architecture Document](./wiki/Power-Plan-Visualization-‐-Architecture-Document) for more details.

