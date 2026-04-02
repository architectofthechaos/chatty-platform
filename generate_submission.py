"""
Generate the submission PDF for the Chatty Platform Engineering Homework.
Run: python generate_submission.py
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)


def build_pdf(output_path="submission.pdf", screenshots=None):
    """Build the submission PDF."""

    if screenshots is None:
        screenshots = {}

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name="MainTitle",
        parent=styles["Title"],
        fontSize=24,
        spaceAfter=6,
        textColor=HexColor("#1a1a1a"),
    ))
    styles.add(ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=24,
    ))
    styles.add(ParagraphStyle(
        name="SectionHead",
        parent=styles["Heading1"],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=HexColor("#2c3e50"),
    ))
    styles.add(ParagraphStyle(
        name="SubHead",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
        textColor=HexColor("#34495e"),
    ))
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="Caption",
        parent=styles["Normal"],
        fontSize=9,
        textColor=HexColor("#888888"),
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=16,
    ))
    styles.add(ParagraphStyle(
        name="BulletItem",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceAfter=4,
    ))

    story = []

    # ── Title Page ──
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Chatty Platform Engineering", styles["MainTitle"]))
    story.append(Paragraph("Submission Document", styles["Subtitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="60%", thickness=1, color=HexColor("#cccccc")))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Vishnu G", styles["Body"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "GitHub: <link href=\"https://github.com/YOUR_REPO_HERE\">"
        "https://github.com/YOUR_REPO_HERE</link>",
        styles["Body"],
    ))
    story.append(PageBreak())

    # ── Overview ──
    story.append(Paragraph("Overview", styles["SectionHead"]))
    story.append(Paragraph(
        "Starting from a working Chat API application, I operationalized it into a "
        "platform-ready service with foundational DevOps, infrastructure, and SDLC best practices. "
        "The focus was on quality and clarity over scope.",
        styles["Body"],
    ))
    story.append(Spacer(1, 0.1 * inch))

    # Summary table
    summary_data = [
        ["Category", "Status"],
        ["Dockerize (Dockerfile + docker-compose + Postgres)", "Implemented"],
        ["GitHub Actions CI (lint, test, build, OpenAPI)", "Implemented"],
        ["OpenAPI spec generation", "Implemented"],
        ["CORS approach (env-driven)", "Implemented"],
        ["Config / env var management", "Implemented"],
        ["DB migration instrumentation (Alembic)", "Implemented"],
        ["Infra as code (Terraform + EKS)", "Described in RATIONALE.md"],
        ["CI/CD full pipeline (blue/green, ArgoCD)", "Described in RATIONALE.md"],
        ["Auth/AuthZ (Keycloak, RBAC)", "Described in RATIONALE.md"],
        ["Exposing service to front-end", "Described in RATIONALE.md"],
        ["Auto scaling + load testing (HPA, k6)", "Described in RATIONALE.md"],
        ["Cloud spend management", "Described in RATIONALE.md"],
        ["General SDLC", "Described in RATIONALE.md"],
    ]

    col_widths = [4.2 * inch, 2.5 * inch]
    t = Table(summary_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8f9fa")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ── What Was Implemented ──
    story.append(Paragraph("What Was Implemented", styles["SectionHead"]))

    # Docker
    story.append(Paragraph("Dockerization", styles["SubHead"]))
    story.append(Paragraph(
        "The application runs with a single command: <b>docker compose up --build</b>. "
        "The setup includes a Postgres 16 database with health checks, an entrypoint script "
        "that runs Alembic migrations automatically before starting the server, and environment "
        "variable configuration via .env.example.",
        styles["Body"],
    ))

    if screenshots.get("docker_compose"):
        img = Image(screenshots["docker_compose"], width=6.5 * inch, height=3.5 * inch)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Paragraph("docker compose up: Postgres starts, migrations run, app ready on port 8000", styles["Caption"]))

    # Swagger
    story.append(Paragraph("API Documentation (Swagger UI)", styles["SubHead"]))
    story.append(Paragraph(
        "FastAPI auto-generates interactive API documentation at /docs. "
        "All endpoints for users, chatrooms, messages, and chatroom participants "
        "are visible with request/response schemas.",
        styles["Body"],
    ))

    if screenshots.get("swagger"):
        img = Image(screenshots["swagger"], width=6.5 * inch, height=3.5 * inch)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Paragraph("Swagger UI at localhost:8000/docs", styles["Caption"]))

    # CI
    story.append(Paragraph("GitHub Actions CI Pipeline", styles["SubHead"]))
    story.append(Paragraph(
        "The CI pipeline runs on every push with four jobs: lint (ruff check + format), "
        "unit tests (pytest with JUnit artifacts), Docker image build, and OpenAPI spec generation. "
        "Lint and tests run in parallel. Build and OpenAPI are gated on both passing.",
        styles["Body"],
    ))

    if screenshots.get("ci_pipeline"):
        img = Image(screenshots["ci_pipeline"], width=6.5 * inch, height=3 * inch)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Paragraph("GitHub Actions: all 4 jobs passing", styles["Caption"]))

    if screenshots.get("ci_artifact"):
        img = Image(screenshots["ci_artifact"], width=6.5 * inch, height=2 * inch)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Paragraph("OpenAPI spec uploaded as CI build artifact", styles["Caption"]))

    # Alembic
    story.append(Paragraph("Database Migrations (Alembic)", styles["SubHead"]))
    story.append(Paragraph(
        "Replaced the original drop-all-tables-on-startup behavior with Alembic migrations. "
        "The initial migration is auto-generated from existing SQLAlchemy models. "
        "Migrations run automatically on container startup via the entrypoint script. "
        "Developers create new migrations with: <b>poetry run alembic revision --autogenerate</b>",
        styles["Body"],
    ))

    story.append(PageBreak())

    # ── What Was Described ──
    story.append(Paragraph("What Was Described in RATIONALE.md", styles["SectionHead"]))
    story.append(Paragraph(
        "The following topics are documented with architecture diagrams, Kubernetes manifests, "
        "and practical approaches in RATIONALE.md:",
        styles["Body"],
    ))

    described_items = [
        ("<b>Infra as Code</b>: Terraform module structure for EKS, RDS, ALB, ECR. "
         "GitOps deployment workflow, remote state management, CI for Terraform. "
         "Detailed in terraform/README.md."),
        ("<b>CI/CD Full Pipeline</b>: Complete flow from developer machine to production "
         "with pre-commit hooks, security scans (SAST, Trivy), integration tests, "
         "ECR push, ArgoCD sync to staging, manual approval gate, blue/green production deploys."),
        ("<b>Auth/AuthZ</b>: Keycloak as IdP with JWT validation in FastAPI. "
         "Socket.IO auth via handshake token. RBAC built on the existing "
         "chatroom_participant table with owner/member/read-only roles."),
        ("<b>Exposing to Front-End</b>: Full request path from client through "
         "Route 53, API Gateway (rate limiting, WAF), ALB (TLS, sticky sessions), "
         "to EKS pods with Redis adapter for cross-pod Socket.IO coordination."),
        ("<b>Auto Scaling</b>: Kubernetes HPA, pod resource requests/limits, "
         "LimitRange, ResourceQuota with actual YAML manifests for Chatty. "
         "Database connection pooling via RDS Proxy/PgBouncer."),
        ("<b>Cloud Spend</b>: Right-sizing by environment, non-production auto-shutdown, "
         "AWS Budgets with alerts, Savings Plans for baseline compute, resource tagging."),
        ("<b>General SDLC</b>: Trunk-based development, feature flags via env vars, "
         "environment parity across dev/staging/production."),
    ]

    for item in described_items:
        story.append(Paragraph(f"\u2022  {item}", styles["BulletItem"]))

    story.append(Spacer(1, 0.2 * inch))

    # Additional considerations
    story.append(Paragraph("Additional Considerations", styles["SubHead"]))
    story.append(Paragraph(
        "Beyond the original TODO list, the RATIONALE.md also covers:",
        styles["Body"],
    ))
    story.append(Paragraph(
        "\u2022  <b>Observability</b>: Production stack with Loki (logs), Prometheus (metrics), "
        "Tempo (traces), and Grafana dashboards for API health, Socket.IO connections, "
        "database performance, and infrastructure utilization.",
        styles["BulletItem"],
    ))
    story.append(Paragraph(
        "\u2022  <b>SLIs and SLOs</b>: Defined for Chatty with specific targets "
        "(p99 latency < 300ms, error rate < 0.1%, 99.9% uptime, Socket.IO delivery < 500ms). "
        "Burn-rate alerting via Alertmanager to PagerDuty.",
        styles["BulletItem"],
    ))

    story.append(PageBreak())

    # ── Key Insight ──
    story.append(Paragraph("Key Insight", styles["SectionHead"]))
    story.append(Paragraph(
        "The biggest gap in the original codebase was not a missing feature. It was a single "
        "block of code in main.py that dropped and recreated all database tables on every startup. "
        "In development, this is invisible. In production, it would silently wipe all user data "
        "on every deploy.",
        styles["Body"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "This is the kind of issue that platform engineering exists to catch. The first thing I did "
        "was replace it with Alembic migrations that run automatically on container startup. "
        "Schema changes are now versioned, reviewable, and reversible. No data loss, no surprises.",
        styles["Body"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "It reinforced for me that operationalizing an app is not about adding new capabilities. "
        "It is about identifying the assumptions that work in development but break in production, "
        "and replacing them with practices that scale.",
        styles["Body"],
    ))

    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc")))
    story.append(Spacer(1, 0.2 * inch))

    # Repo link
    story.append(Paragraph("Repository", styles["SubHead"]))
    story.append(Paragraph(
        "<link href=\"https://github.com/YOUR_REPO_HERE\">"
        "https://github.com/YOUR_REPO_HERE</link>",
        styles["Body"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Key files:", styles["Body"]))
    files = [
        "README.md - bootstrapping, project structure, operational status",
        "RATIONALE.md - decisions, architecture, AI usage",
        "CONTRIBUTING.md - how to extend the app",
        "terraform/README.md - IaC module structure and operational practices",
        "docker-compose.yml - one-command local setup",
        ".github/workflows/ci.yml - CI pipeline",
    ]
    for f in files:
        story.append(Paragraph(f"\u2022  {f}", styles["BulletItem"]))

    # Build
    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    # Check for screenshots in the current directory
    screenshot_map = {
        "docker_compose": "screenshot_docker.png",
        "swagger": "screenshot_swagger.png",
        "ci_pipeline": "screenshot_ci.png",
        "ci_artifact": "screenshot_artifact.png",
    }

    found = {}
    for key, filename in screenshot_map.items():
        if os.path.exists(filename):
            found[key] = filename
            print(f"Found screenshot: {filename}")
        else:
            print(f"Missing screenshot: {filename} (will be skipped)")

    build_pdf(output_path="submission.pdf", screenshots=found)
