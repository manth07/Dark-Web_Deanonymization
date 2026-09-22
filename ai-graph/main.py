"""Command Line Interface for Dark Web Threat Actor Deanonymization Engine."""
import json
import os
import shutil
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from core.logger import get_logger
from export.reporter import IntelligenceReporter
from graph.schema import init_schema
from pipeline import StylometryPipeline
from schemas.raw_post import RawForumPost

app = typer.Typer(
    help="Autonomous NLP Stylometry & Neo4j Threat Intelligence CLI",
    add_completion=False,
)
console = Console()
logger = get_logger("cli.main")


@app.command("init-db")
def cmd_init_db(
    clear: bool = typer.Option(
        False, "--clear", "-c", help="Clear all existing nodes and edges before applying constraints"
    ),
) -> None:
    """Run Neo4j database schema migrations and enforce unique/node-key constraints."""
    console.print("[bold blue]Starting Neo4j Schema Initialization & Migrations...[/bold blue]")
    try:
        pipeline = StylometryPipeline()
        if clear:
            console.print("[yellow]Clearing existing database contents...[/yellow]")
            pipeline.repository.clear()

        applied_statements = init_schema(driver=pipeline.repository.driver)
        console.print(
            f"[bold green]Successfully executed {len(applied_statements)} schema constraints and indexes![/bold green]"
        )
    except Exception as exc:
        console.print(f"[bold red]Schema migration error: {exc}[/bold red]")
        raise typer.Exit(code=1)


@app.command("ingest-fixtures")
def cmd_ingest_fixtures(
    fixtures_path: str = typer.Option(
        "fixtures/sample_posts.json",
        "--fixtures",
        "-f",
        help="Path to synthetic dark web forum post JSON corpus",
    ),
    init_schema_first: bool = typer.Option(
        True, "--init-schema/--no-init-schema", help="Initialize schema constraints before ingestion"
    ),
) -> None:
    """Load dark web forum post fixtures and run full stylometric deanonymization pipeline."""
    console.print(f"[bold blue]Loading synthetic dark web corpus from '{fixtures_path}'...[/bold blue]")
    p = Path(fixtures_path)
    if not p.exists():
        console.print(f"[bold red]Fixtures file '{fixtures_path}' not found.[/bold red]")
        raise typer.Exit(code=1)

    try:
        with open(p, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        posts = [RawForumPost.model_validate(item) for item in raw_data]
        console.print(f"[cyan]Loaded {len(posts)} posts for processing.[/cyan]")

        pipeline = StylometryPipeline()
        if init_schema_first:
            init_schema(driver=pipeline.repository.driver)

        processed = pipeline.process_batch(posts)
        console.print(f"[bold green]Successfully ingested {len(processed)} posts end-to-end![/bold green]")

        # Display unique personas and linkages
        candidate_profiles = pipeline.repository.get_candidate_profiles()
        unique_handles = {p.handle for p in candidate_profiles}
        clusters = {p.attribution_id for p in candidate_profiles if p.attribution_id}

        console.print("\n[bold]Ingestion Summary:[/bold]")
        console.print(f"  • Total Posts Ingested: {len(processed)}")
        console.print(f"  • Distinct Personas: {len(unique_handles)} ({', '.join(sorted(unique_handles))})")
        console.print(f"  • Resolved Threat Actor Clusters: {len(clusters)}")

    except Exception as exc:
        console.print(f"[bold red]Pipeline ingestion failed: {exc}[/bold red]")
        raise typer.Exit(code=1)


@app.command("export-actor")
def cmd_export_actor(
    actor_id: str = typer.Option(..., "--actor-id", "-a", help="Threat Actor Cluster ID to export"),
    format_type: str = typer.Option(
        "json", "--format", "-f", help="Export format: 'json', 'csv', or 'both'"
    ),
    output_dir: str = typer.Option(
        "exports", "--output-dir", "-o", help="Target output directory for intelligence artifacts"
    ),
) -> None:
    """Export threat intelligence reports and analyst deliverables for a resolved ThreatActor."""
    console.print(f"[bold blue]Querying Threat Intelligence for Actor ID: '{actor_id}'...[/bold blue]")
    try:
        reporter = IntelligenceReporter()
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        if format_type.lower() in ("json", "both"):
            json_file = out_path / f"{actor_id}.json"
            reporter.export_json(actor_id, str(json_file))
            console.print(f"[green]• Exported NTRO JSON Deliverable to: {json_file}[/green]")

        if format_type.lower() in ("csv", "both"):
            csv_file = out_path / f"{actor_id}.csv"
            reporter.export_csv(actor_id, str(csv_file))
            console.print(f"[green]• Exported Analyst CSV Spreadsheet to: {csv_file}[/green]")

        # Print Textual Summary Briefing
        summary = reporter.generate_summary_report(actor_id)
        console.print("\n[bold yellow]Threat Actor Briefing Summary:[/bold yellow]")
        console.print(summary, markup=False)

    except Exception as exc:
        console.print(f"[bold red]Export failed: {exc}[/bold red]")
        raise typer.Exit(code=1)


@app.command("run-worker")
def cmd_run_worker(
    input_dir: str = typer.Option(
        "data/incoming", "--input-dir", "-i", help="Directory to monitor for incoming JSON post batches"
    ),
    processed_dir: str = typer.Option(
        "data/processed", "--processed-dir", "-p", help="Directory to move processed JSON post batches"
    ),
    poll_interval: int = typer.Option(
        5, "--interval", help="Polling interval in seconds between directory scans"
    ),
    run_once: bool = typer.Option(
        False, "--once", help="Run a single directory scan pass and exit"
    ),
) -> None:
    """Continuously poll or watch an incoming directory for new dark web post files."""
    in_dir = Path(input_dir)
    proc_dir = Path(processed_dir)
    in_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    pipeline = StylometryPipeline()
    console.print(f"[bold blue]Worker started. Monitoring '{in_dir}' for incoming posts...[/bold blue]")

    while True:
        try:
            json_files = list(in_dir.glob("*.json"))
            if json_files:
                console.print(f"[cyan]Found {len(json_files)} file(s) for ingestion.[/cyan]")
                for file_path in json_files:
                    console.print(f"Processing: {file_path.name}")
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if isinstance(data, dict):
                        data = [data]

                    posts = [RawForumPost.model_validate(p) for p in data]
                    pipeline.process_batch(posts)

                    # Move to processed
                    dest = proc_dir / file_path.name
                    shutil.move(str(file_path), str(dest))
                    console.print(f"[green]Archived '{file_path.name}' to '{dest}'[/green]")

            if run_once:
                break

            time.sleep(poll_interval)
        except KeyboardInterrupt:
            console.print("[yellow]Worker stopping gracefully on user interrupt.[/yellow]")
            break
        except Exception as exc:
            logger.error(f"Worker iteration error: {exc}", exc_info=True)
            if run_once:
                raise typer.Exit(code=1)
            time.sleep(poll_interval)


if __name__ == "__main__":
    app()
