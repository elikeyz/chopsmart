# ChopSmart

ChopSmart is an AI-powered recipe generator that turns your available ingredients into personalized, nutritionally-aware recipes. Enter what you have on hand, set your dietary preferences, and a multi-agent pipeline powered by Anthropic Claude on AWS Bedrock generates a tailored recipe — complete with step-by-step instructions and a built-in assistant for cooking questions.

## How It Works

1. **Enter ingredients** — List what you have available at home.
2. **Set preferences** — Specify dietary restrictions, allergies, cuisine style, meal type, and calorie target.
3. **Generate** — A three-agent pipeline (Planner → Evaluator → Optimizer) drafts, validates, and refines a recipe against your constraints.
4. **Cook** — Follow step-by-step instructions enriched with nutritional data from the OpenNutrition MCP server.
5. **Ask questions** — Use the built-in assistant chat for real-time cooking tips, substitutions, and clarifications.

## Technologies

| Layer | Stack |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 — hosted on **Vercel** |
| Backend | Python 3.12, FastAPI — containerized via **Amazon ECR**, deployed on **AWS App Runner** |
| Agent framework | OpenAI Agents SDK + LiteLLM (AWS Bedrock adapter) |
| AI model | Anthropic Claude via **AWS Bedrock** |
| MCP server | OpenNutrition (Node.js + SQLite) — nutrition data via Model Context Protocol |
| Infrastructure | Terraform (ECR, App Runner, IAM, OIDC federation) |
| Package managers | `uv` (Python), `npm` (Node.js / frontend) |

## Architecture

The frontend is hosted on Vercel and communicates with the FastAPI backend over HTTPS. The backend runs as a containerized service on AWS App Runner, invokes Claude through AWS Bedrock, and queries the OpenNutrition MCP server — co-located in the same container — for nutritional data.

```txt
                        +------------------+
                        |     Browser      |
                        +------------------+
                                 |
                              HTTPS
                                 |
                                 v
                        +------------------+
                        |     Vercel       |
                        |   (Frontend)     |
                        | Next.js / React  |
                        |   Tailwind CSS   |
                        +------------------+
                                 |
                           REST API calls
                                 |
                                 v
+----------------+      +--------------------+
|  Amazon ECR    | pull |   AWS App Runner   |
| (Docker image) | ---> |     (Backend)      |
+----------------+      | FastAPI / Python   |
                        +--------------------+
                               |      |
               Bedrock API     |      | MCP Protocol
                               |      |
                   +-----------+      +-----------+
                   |                              |
                   v                              v
          +------------------+        +------------------+
          |   AWS Bedrock    |        |   MCP Server     |
          | (Anthropic Claude|        | OpenNutrition    |
          |  Sonnet 4.6)     |        | (SQLite, in-proc)|
          +------------------+        +------------------+
```

## Project Structure

```txt
chopsmart/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline (GitHub Actions)
├── backend/
│   ├── main.py                 # FastAPI entry point and route definitions
│   ├── planner.py              # Planner agent — drafts the initial recipe
│   ├── evaluator.py            # Evaluator agent — validates against constraints
│   ├── optimizer.py            # Optimizer agent — refines based on feedback
│   ├── assistant.py            # Assistant agent — answers user questions
│   ├── context.py              # System prompts for each agent
│   ├── output_types.py         # Pydantic models (Recipe, Ingredient, etc.)
│   ├── mcp_servers.py          # MCP server initialization (Node.js subprocess)
│   ├── deploy.py               # AWS ECR + App Runner deployment script
│   └── pyproject.toml          # Python dependencies (uv)
├── frontend/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Home page
│   ├── components/
│   │   ├── RecipeForm.tsx      # Ingredient input and preferences form
│   │   ├── RecipeDisplay.tsx   # Recipe output renderer
│   │   ├── RecipeChat.tsx      # Assistant chat with markdown support
│   │   ├── TagInput.tsx        # Tag-based input for allergies and dislikes
│   │   └── ...                 # Header, loading skeletons, empty states
│   ├── next.config.ts          # Next.js config (standalone output for Docker)
│   └── package.json
├── mcp-opennutrition/
│   ├── src/
│   │   ├── index.ts            # MCP server entry point
│   │   └── SQLiteDBAdapter.ts  # SQLite adapter for the nutrition dataset
│   ├── data/                   # OpenNutrition dataset (downloaded at build time)
│   └── scripts/                # Dataset pipeline scripts (TSV → SQLite)
├── terraform/
│   └── backend/
│       ├── main.tf             # ECR repository, App Runner service, IAM roles
│       ├── github-oidc.tf      # GitHub Actions OIDC trust relationship
│       ├── variables.tf
│       └── outputs.tf
└── Dockerfile                  # Multi-stage build: MCP server + FastAPI backend
```

## Design Decisions and Trade-offs

### Multi-Agent Pipeline (Planner → Evaluator → Optimizer)

Recipe generation is handled by three specialized agents rather than a single prompt. The **Planner** drafts a recipe using nutritional data from the MCP server. The **Evaluator** checks it strictly against user constraints (allergies, calorie budget, dislikes). The **Optimizer** rewrites any failing sections based on the evaluator's feedback.

- **Why:** Combining generation and validation in a single prompt produces recipes that subtly violate constraints. Separate agents make each role auditable and independently improvable.
- **Trade-off:** Sequential execution increases latency and Bedrock token cost compared to a one-shot approach.

### OpenAI Agents SDK + LiteLLM as a Bedrock Adapter

The agent orchestration layer uses the OpenAI Agents SDK. LiteLLM acts as a thin adapter, routing calls to Claude on AWS Bedrock using the OpenAI-compatible interface.

- **Why:** The Agents SDK provides structured tool use, trace spans, and a clean handoff model between agents. LiteLLM enables Bedrock integration without rewriting orchestration logic.
- **Trade-off:** An extra abstraction layer adds a dependency and a potential failure point. LiteLLM's Bedrock support may lag behind new Bedrock features.

### MCP Server as an In-Container Subprocess

The OpenNutrition MCP server runs as a Node.js subprocess inside the same container as the FastAPI backend. It provides the Planner agent with per-ingredient nutritional data (calories, macros) via the Model Context Protocol, backed by a local SQLite database built at image build time.

- **Why:** Local nutrition lookups are fast (no external API), and co-location in one image simplifies deployment to a single App Runner service.
- **Trade-off:** Both processes share the container lifecycle. A crash in the MCP subprocess requires a full container restart. A sidecar container pattern would be more resilient but significantly increases operational complexity on App Runner.

### AWS App Runner for the Backend

The FastAPI backend is packaged as a Docker image, stored in Amazon ECR, and deployed as an App Runner service.

- **Why:** App Runner manages load balancing, auto-scaling, and TLS termination with near-zero configuration. ECR keeps the image registry in the same AWS region as the compute.
- **Trade-off:** App Runner offers less control than ECS or EKS — no native sidecar containers, limited VPC configuration options, and visible cold starts for low-traffic services.

### Frontend on Vercel

The Next.js frontend deploys to Vercel via Git integration, with no additional configuration file required.

- **Why:** Zero-config deployments, automatic preview environments per pull request, and global CDN caching out of the box.
- **Trade-off:** The frontend and backend run in separate clouds. CORS must be explicitly managed on the FastAPI side.

### Terraform for Infrastructure

All AWS resources — ECR, App Runner, IAM roles, and the GitHub Actions OIDC trust — are defined in Terraform under `terraform/backend/`.

- **Why:** Infrastructure changes are reproducible, reviewable in pull requests, and recoverable from state.
- **Trade-off:** Terraform state is local by default. The S3 remote backend configured in `deploy.py` requires manual bootstrapping for new environments.

## Observability

### Current Instrumentation

| Signal | Details |
| --- | --- |
| Health check | `GET /health` — used by App Runner for readiness probes |
| Structured errors | FastAPI exception handlers return consistent JSON for all 4xx/5xx responses |
| Agent traces | OpenAI Agents SDK emits spans per agent step (tool calls, LLM I/O); visible in the OpenAI dashboard when `OPENAI_API_KEY` is set |
| Application logs | INFO-level Python logs forwarded to CloudWatch Logs via App Runner's built-in log stream |

### Gaps and Recommendations

| Concern | Recommendation |
| --- | --- |
| Per-agent latency | Wrap each agent call with timing logs; emit as structured JSON for CloudWatch Insights |
| Bedrock token cost | Log the `usage` object from each Bedrock response to track tokens and cost per request |
| Frontend errors | Add a React error boundary and integrate an error reporting service (e.g. Sentry) |
| Alerting | Create CloudWatch alarms on App Runner 5xx error rate and p99 response latency |
| End-to-end tracing | Instrument with AWS X-Ray or OpenTelemetry to correlate frontend → backend → Bedrock spans |

## CI/CD

Backend deployments are fully automated via **GitHub Actions**. The frontend deploys independently via **Vercel Git integration**.

### Backend Pipeline: `.github/workflows/deploy.yml`

**Trigger:** Push to `main`, or manual dispatch via `workflow_dispatch`.

```txt
Push to main
     |
     v
GitHub Actions Runner
     |
     +-- Authenticate to AWS via OIDC (no long-lived credentials)
     |
     +-- Set up Python 3.12 + uv
     |
     +-- Install locked dependencies  (uv sync --frozen)
     |
     +-- Run backend/deploy.py
           |
           +-- Build multi-stage Docker image (MCP server + FastAPI)
           |
           +-- Push image to Amazon ECR
           |
           +-- Trigger AWS App Runner redeployment
```

**AWS authentication** uses OpenID Connect federation — no IAM access keys are stored in GitHub Secrets. The `github-oidc.tf` Terraform module provisions the trust policy. The runner assumes the `github_actions` IAM role, which has least-privilege permissions scoped to ECR image push and App Runner service updates.

### Frontend Pipeline (Vercel)

Every push to `main` triggers a production deployment on Vercel. Every pull request gets its own preview deployment URL automatically.

### Environment Variables

| Variable | Where configured | Used by |
| --- | --- | --- |
| `DEFAULT_AWS_REGION` | GitHub Actions secret | Deploy script, App Runner |
| `BEDROCK_MODEL_ID` | `terraform/backend/terraform.tfvars` | App Runner runtime |
| `BEDROCK_REGION` | `terraform/backend/terraform.tfvars` | App Runner runtime |
| `OPENAI_API_KEY` | GitHub Actions secret | Agent trace reporting |
| `NEXT_PUBLIC_API_URL` | Vercel environment settings | Frontend API base URL |

## Setup

### Prerequisites

- Node.js 20+
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker
- AWS CLI configured with credentials that have ECR and App Runner permissions (for deployment)
- Terraform 1.5+ (for infrastructure provisioning)

### Frontend

```bash
cd frontend
npm install
npm run dev
# Available at http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`.

### Backend

Build and run the Docker image (includes the MCP server):

```bash
docker build -t chopsmart-backend .
docker run -p 8000:8000 \
  -e BEDROCK_MODEL_ID=<model-id> \
  -e BEDROCK_REGION=<region> \
  -e DEFAULT_AWS_REGION=<region> \
  chopsmart-backend
# Available at http://localhost:8000
```

For local development without Docker:

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000
```

> The MCP server subprocess requires the `mcp-opennutrition` package to be built first (`npm run build` inside `mcp-opennutrition/`). The Docker build handles this automatically.

### Infrastructure (Terraform)

```bash
cd terraform/backend
terraform init
terraform apply
```

Configure `terraform.tfvars` with your `aws_region`, `bedrock_model_id`, `bedrock_region`, and `openai_api_key` before applying.
