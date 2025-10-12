# SHACL-BI: Business Intelligence for Semantic Data Quality

A unified platform for semantic data quality management through AI-enhanced SHACL validation and interactive analytics. SHACL-BI integrates the PHOENIX project with SHACL-BI to provide a comprehensive solution for understanding, analyzing, and remediating SHACL constraint violations.

![SHACL-BI Architecture](docs/images/architecture-diagram.png)

## 🌟 Overview

SHACL-BI combines the analytical power of data visualization with the AI-powered explanation and remediation capabilities of PHOENIX. It offers an interactive web interface for exploring SHACL validation results, generating human-readable explanations for violations, and receiving AI-powered suggestions for repairs.

## 🎯 Key Features

### 📊 Interactive Dashboards
- **Real-time Analytics**: Visualize validation metrics with interactive charts and tables
- **Multi-dimensional Views**: Explore violations by shapes, constraints, properties, and focus nodes
- **Data Export**: Download validation statistics and reports in CSV format
- **Responsive Design**: Optimized for desktop and mobile devices

### 🤖 AI-Powered Explanations
- **Natural Language Explanations**: Generate human-readable explanations for SHACL violations using state-of-the-art LLMs
- **Multi-Provider Support**: OpenAI GPT-4, Anthropic Claude, and Google Gemini integration
- **Intelligent Caching**: Violation Knowledge Graph learns from user interactions to improve future explanations
- **Contextual Understanding**: Analyzes violation patterns and data relationships for comprehensive explanations

### 🔧 Interactive Remediation
- **One-Click Repairs**: Apply AI-generated SPARQL repair queries with a single click
- **Validation Feedback**: Real-time validation of repair suggestions before application
- **Repair History**: Track applied repairs and their effectiveness
- **Rollback Capability**: Safely undo applied repairs if needed

### 🔄 Dual-Mode Operation
- **Analytics Mode**: Upload SHACL validation reports for in-depth analysis and visualization
- **Remediation Mode**: Upload data and SHACL shapes for validation with AI-powered explanations and repairs
- **Seamless Switching**: Toggle between modes without losing context

### 🔒 Enterprise Security
- **Tenant Isolation**: Complete data separation between users using session-specific graphs
- **Shared Knowledge**: Violation Knowledge Graph shared across users for community learning
- **Secure Authentication**: Role-based access control and API key management
- **Data Privacy**: No data leakage between tenant sessions

### 🏗️ RESTful API
- **Comprehensive Endpoints**: Full CRUD operations for violations, explanations, and repairs
- **Session Management**: Secure session handling for multi-tenant environments
- **Batch Operations**: Process multiple violations simultaneously
- **Webhook Support**: Real-time notifications for validation events

## 🏛️ Architecture Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Vue.js 3 SPA]
        COMP[Components]
        ROUTER[Vue Router]
        CHART[Chart.js]
    end

    subgraph "Backend Layer"
        API[Flask REST API]
        AUTH[Authentication]
        VAL[Validation Engine]
        PHX[PHOENIX AI]
    end

    subgraph "Data Layer"
        VIRT[Virtuoso RDF Store]
        VKG[Violation Knowledge Graph]
        SESSION[Session Graphs]
        LLM[LLM Providers]
    end

    subgraph "External Services"
        OPENAI[OpenAI API]
        ANTH[Anthropic API]
        GEM[Google Gemini API]
    end

    UI --> API
    COMP --> ROUTER
    ROUTER --> API

    API --> AUTH
    API --> VAL
    API --> PHX

    VAL --> VIRT
    PHX --> VKG
    PHX --> SESSION

    VIRT --> SESSION
    VKG --> VIRT

    PHX --> LLM
    LLM --> OPENAI
    LLM --> ANTH
    LLM --> GEM
```

### Component Architecture

```mermaid
graph LR
    subgraph "Frontend Components"
        LP[LandingPage]
        ML[MainLayout]
        SB[SideBar]
        MC[MainContent]
        VT[ViolationTable]
        VTR[ViolationTableRow]
    end

    subgraph "Backend Services"
        UB[Upload Routes]
        SR[Simple Routes]
        DR[Dashboard Routes]
        PS[Phoenix Service]
        VS[Virtuoso Service]
    end

    subgraph "Data Models"
        VIO[Violations]
        EXP[Explanations]
        REP[Repairs]
        SES[Sessions]
    end

    LP --> ML
    ML --> SB
    ML --> MC
    MC --> VT
    VT --> VTR

    VTR --> UB
    UB --> SR
    SR --> DR
    DR --> PS
    PS --> VS

    VS --> VIO
    PS --> EXP
    PS --> REP
    VS --> SES
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- API key for at least one LLM provider (OpenAI, Anthropic, or Google Gemini)

### Using Docker (Recommended)

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/shacl-bi.git
    cd shacl-bi
    ```

2. **Configure environment**:
    ```bash
    # Copy the example environment file
    cp backend/.env.example .env
    # Edit with your API keys
    nano .env
    ```

    Example `.env` file:
    ```bash
    # LLM Provider Keys (at least one required)
    OPENAI_API_KEY=your_openai_key_here
    ANTHROPIC_API_KEY=your_anthropic_key_here
    GEMINI_API_KEY=your_gemini_key_here

    # Database Configuration
    VIRTUOSO_ENDPOINT=http://localhost:8890/sparql-auth
    VIRTUOSO_USER=dba
    VIRTUOSO_PASSWORD=dba

    # Graph URIs
    SHAPES_GRAPH=http://ex.org/ShapesGraph
    VALIDATION_GRAPH=http://ex.org/ValidationReport
    VIOLATION_KG_GRAPH=http://ex.org/ViolationKnowledgeGraph

    # Feature Flags
    ENABLE_XPSHACL_FEATURES=true
    ENABLE_DASHBOARD_FEATURES=true
    DEFAULT_AI_MODEL=openai/gpt-4
    ```

3. **Start the application**:
    ```bash
    docker-compose up -d
    ```

### Ultra-Fast Builds with Docker Bake

For maximum build performance:
```bash
# Use Bake for maximum performance
COMPOSE_BAKE=true docker-compose up --build

# Or use dedicated bake scripts
./scripts/bake-build.sh          # Unix/Linux/MacOS
./scripts/bake-build.bat         # Windows
```

### Access Points

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:80
- **Virtuoso SPARQL Endpoint**: http://localhost:8890/sparql

## 📖 Usage Guide

### Analytics Mode
1. Navigate to the landing page and select "Analytics Mode"
2. Enter your Virtuoso configuration:
   - Directory path to your Virtuoso installation
   - SHACL shapes graph name
   - Validation report graph name
3. Click "ENTER ANALYTICS MODE" to load the dashboard
4. Explore violations through interactive charts and detailed tables
5. Export data and insights as needed

### Remediation Mode (PHOENIX)
1. Select "Upload Mode" on the landing page
2. Upload your RDF data file (.ttl, .rdf, .n3, .nt)
3. Upload your SHACL shapes graph file
4. Review validation results with AI-generated explanations
5. Apply intelligent repair suggestions with one click
6. Track repair history and effectiveness

### Key Interactive Features

#### 📋 Validation Results Table
- **Expandable Rows**: Click any violation to see detailed information
- **Smart Explanations**: AI-generated explanations for each violation
- **Repair Suggestions**: Context-aware repair recommendations
- **Accept/Reject**: Choose which repairs to apply
- **SPARQL Preview**: View and understand repair queries before application

#### 📈 Interactive Charts
- **Violation Distribution**: Visualize violations by shape and constraint type
- **Severity Analysis**: Understand impact and priority of violations
- **Trend Tracking**: Monitor violation patterns over time
- **Filter Controls**: Focus on specific data subsets

#### 🔍 Advanced Filtering
- **Multi-dimensional Filters**: Filter by shape, constraint, property, severity
- **Search Functionality**: Find specific violations quickly
- **Saved Filters**: Reuse common filter configurations
- **Real-time Updates**: See results instantly as you filter

## 🛡️ Security Architecture

### Multi-Tenant Data Isolation

SHACL-BI implements robust tenant isolation to ensure data privacy and security:

```mermaid
graph TB
    subgraph "User Sessions"
        USER1[User 1 Session]
        USER2[User 2 Session]
        USER3[User 3 Session]
    end

    subgraph "Private Data Graphs"
        PRIV1[ValidationReport/Session_1]
        PRIV2[ValidationReport/Session_2]
        PRIV3[ValidationReport/Session_3]
    end

    subgraph "Shared Resources"
        VKG[ViolationKnowledgeGraph]
        SHAPES[ShapesGraph]
    end

    USER1 --> PRIV1
    USER2 --> PRIV2
    USER3 --> PRIV3

    PRIV1 -.-> VKG
    PRIV2 -.-> VKG
    PRIV3 -.-> VKG

    USER1 -.-> SHAPES
    USER2 -.-> SHAPES
    USER3 -.-> SHAPES
```

### Security Features

#### 🔐 Session-Based Isolation
- **Unique Session IDs**: Each upload generates a cryptographically secure session identifier
- **Named Graph Separation**: Data stored in session-specific named graphs
- **Access Control**: Users can only access their own session data
- **Automatic Cleanup**: Session data cleaned up after configurable time periods

#### 🛡️ Authentication & Authorization
- **API Key Management**: Secure storage and rotation of LLM provider API keys
- **Role-Based Access**: Different permission levels for different user types
- **Request Validation**: Comprehensive input validation and sanitization
- **Rate Limiting**: Protection against API abuse and DoS attacks

#### 🔒 Data Protection
- **Encryption in Transit**: All API communications use HTTPS/TLS
- **Secure Storage**: Sensitive configuration encrypted at rest
- **Audit Logging**: Complete audit trail of all data access and modifications
- **Backup & Recovery**: Automated backup procedures for critical data

#### 🚨 Privacy Controls
- **Data Minimization**: Only collect and store necessary data
- **User Consent**: Clear consent mechanisms for data processing
- **Data Retention**: Configurable data retention policies
- **Right to Delete**: Complete data deletion upon user request

## 📊 Supported Formats & Constraints

### Input Formats
- **RDF Data**: Turtle (.ttl), RDF/XML (.rdf), N-Triples (.nt), JSON-LD (.jsonld)
- **SHACL Shapes**: Turtle format preferred, all RDF formats supported
- **Validation Reports**: Standard SHACL validation reports in RDF format

### Supported SHACL Constraints
- **Property Constraints**: minCount, maxCount, datatype, pattern, minInclusive, maxInclusive
- **Node Constraints**: class, target declarations, nodeKind
- **Complex Constraints**: sh:and, sh:or, sh:xone, sh:not
- **Custom Constraints**: SPARQL-based constraint validation
- **Advanced Features**: Property paths, constraint components, validation reports

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
VIRTUOSO_ENDPOINT=http://localhost:8890/sparql-auth
VIRTUOSO_USER=dba
VIRTUOSO_PASSWORD=dba

# Graph Configuration
SHAPES_GRAPH=http://ex.org/ShapesGraph
VALIDATION_GRAPH=http://ex.org/ValidationReport
VIOLATION_KG_GRAPH=http://ex.org/ViolationKnowledgeGraph

# AI Configuration
SRG_MODEL=openai/gpt-5-nano-2025-08-07
GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
```

### LLM Provider Configuration

#### OpenAI
```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
```

#### Anthropic Claude
```bash
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-sonnet
ANTHROPIC_MAX_TOKENS=2000
ANTHROPIC_TEMPERATURE=0.7
```

#### Google Gemini
```bash
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-pro
GEMINI_MAX_TOKENS=2000
GEMINI_TEMPERATURE=0.7
```

## 🔄 Recently Implemented Features

### ✅ AI-Powered Violation Explanations (Latest)
- **Natural Language Processing**: Advanced LLM integration for human-readable explanations
- **Context-Aware Analysis**: Understanding of violation context and data relationships
- **Multi-Provider Support**: Seamless switching between OpenAI, Anthropic, and Google models
- **Real-time Generation**: On-demand explanation generation with caching optimization

### ✅ Interactive Repair Suggestions
- **One-Click Repairs**: Apply AI-generated SPARQL queries directly from the UI
- **Repair Validation**: Preview and validate repair queries before application
- **Success Feedback**: Real-time confirmation of successful repairs
- **Error Handling**: Comprehensive error reporting and rollback capabilities

### ✅ Enhanced Security Architecture
- **Tenant Isolation**: Complete data separation between users
- **Session Management**: Secure session handling with automatic cleanup
- **Access Control**: Role-based permissions and API key management
- **Audit Trail**: Complete logging of all system activities

### ✅ Advanced UI/UX Improvements
- **Responsive Design**: Optimized for all device sizes
- **Interactive Charts**: Real-time data visualization with Chart.js
- **Advanced Filtering**: Multi-dimensional filtering with saved configurations
- **Export Capabilities**: CSV export for all data tables and charts

### ✅ Performance Optimizations
- **Background Processing**: Async LLM calls for better responsiveness
- **Intelligent Caching**: Violation Knowledge Graph for improved performance
- **Database Optimization**: Optimized SPARQL queries and indexing
- **Docker Bake**: Ultra-fast build times with parallel processing

## 🧪 Testing & Quality Assurance

### Backend Testing
```bash
cd backend
python -m pytest tests/ -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_validation.py -v
```

### Frontend Testing
```bash
cd frontend
npm run test
npm run test:e2e
npm run lint
npm run build
```

### Integration Testing
```bash
# Run full integration test suite
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🔧 API Reference

### Core Endpoints

#### Validation
- `POST /api/upload/files` - Upload data and shapes for validation
- `GET /api/violations?session_id={id}` - Get violations for a session
- `GET /api/statistics?session_id={id}` - Get validation statistics

#### Explanations & Repairs
- `POST /api/explanation` - Generate explanation for a violation
- `GET /api/explanations/{session_id}` - Get cached explanations
- `POST /api/repair` - Apply a repair suggestion

#### Analytics
- `GET /api/dashboard/home?session_id={id}` - Dashboard overview
- `GET /api/shapes/overview?session_id={id}` - Shapes analysis
- `GET /api/constraints/overview?session_id={id}` - Constraints analysis

### Response Format
```json
{
  "success": true,
  "data": {
    "violations": [...],
    "statistics": {...},
    "explanations": [...]
  },
  "session_id": "abc123",
  "message": "Operation completed successfully"
}
```

## 🚀 Performance Metrics

### Build Performance
- **Standard Docker Build**: ~70s first build, ~20-30s cached builds
- **Docker Bake Build**: ~50s first build, ~15-20s cached builds
- **Frontend Build**: ~30s production build, ~10s development build

### Runtime Performance
- **Validation Processing**: <5s for typical datasets (<10k triples)
- **Explanation Generation**: <10s for individual violations
- **Dashboard Loading**: <2s for charts and statistics
- **API Response Time**: <500ms average, <2s 95th percentile

### Scalability
- **Concurrent Users**: 100+ simultaneous users
- **Data Volume**: Supports datasets up to 100k triples per session
- **Storage**: Efficient graph storage with automatic cleanup
- **Memory Usage**: <2GB typical, <4GB peak load

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with comprehensive tests
4. **Ensure code quality**: `npm run lint` and `python -m pytest`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Submit a pull request** with detailed description

### Development Guidelines
- Follow existing code patterns and conventions
- Write comprehensive tests for new features
- Update documentation for API changes
- Ensure backward compatibility where possible
- Use semantic versioning for releases

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[SHACL](https://www.w3.org/TR/shacl/)** - Shapes Constraint Language specification
- **[Virtuoso](https://virtuoso.openlinksw.com/)** - High-performance RDF triple store
- **[Vue.js](https://vuejs.org/)** - Progressive JavaScript framework
- **[Flask](https://flask.palletsprojects.com/)** - Python web framework
- **[Chart.js](https://www.chartjs.org/)** - Flexible charting library
- **[Vuetify](https://vuetifyjs.com/)** - Material Design component framework
- **[OpenAI](https://openai.com/)** - GPT language models
- **[Anthropic](https://anthropic.com/)** - Claude language models
- **[Google](https://ai.google.dev/)** - Gemini language models

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/gcpdev/shacl-bi/wiki)
- **Issues**: [GitHub Issues](https://github.com/gcpdev/shacl-bi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/gcpdev/shacl-bi/discussions)
---

**SHACL-BI** - Empowering semantic data quality with AI-driven insights and automated remediation. 🚀