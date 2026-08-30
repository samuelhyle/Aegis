"""CLI commands for database backup and restore."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import click


@click.group()
def db():
    """Database management commands."""
    pass


@db.command()
@click.option("--output", "-o", help="Output file path", default=None)
@click.option("--database-url", help="Database URL", default=None)
def backup(output: str | None, database_url: str | None):
    """Backup the database to a JSON file."""
    from .db import DatabaseManager

    manager = DatabaseManager(database_url)
    manager.create_tables()

    # Generate default filename if not provided
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"aegis_backup_{timestamp}.json"

    output_path = Path(output)

    click.echo(f"Backing up database to {output_path}...")

    try:
        data = manager.export_investigations(format="json", include_deleted=True)

        with open(output_path, "w") as f:
            f.write(data)

        # Get backup stats
        records = manager.get_all_investigations(include_deleted=True)
        click.echo(f"✓ Backup complete: {len(records)} records exported")
        click.echo(f"✓ File size: {output_path.stat().st_size:,} bytes")

    except Exception as e:
        click.echo(f"✗ Backup failed: {e}", err=True)
        sys.exit(1)


@db.command()
@click.argument("input_file")
@click.option("--database-url", help="Database URL", default=None)
@click.option("--clear/--no-clear", help="Clear existing data before restore", default=False)
def restore(input_file: str, database_url: str | None, clear: bool):
    """Restore the database from a JSON backup file."""
    from .db import DatabaseManager
    from .models import AgentResult, InvestigationReport, ReviewDecision

    manager = DatabaseManager(database_url)
    manager.create_tables()

    input_path = Path(input_file)
    if not input_path.exists():
        click.echo(f"✗ File not found: {input_path}", err=True)
        sys.exit(1)

    click.echo(f"Restoring database from {input_path}...")

    try:
        with open(input_path) as f:
            records = json.load(f)

        if not isinstance(records, list):
            click.echo("✗ Invalid backup format: expected a list of records", err=True)
            sys.exit(1)

        # Clear existing data if requested
        if clear:
            click.echo("Clearing existing data...")
            session = manager.get_session()
            try:
                from .db import InvestigationRecord
                session.query(InvestigationRecord).delete()
                session.commit()
            finally:
                session.close()

        # Restore records
        restored = 0
        skipped = 0

        for record_data in records:
            try:
                # Convert back to InvestigationReport
                agent_results = [
                    AgentResult(**ar) for ar in record_data.get("agent_results", [])
                ]

                review_decision = None
                if record_data.get("review_decision"):
                    review_decision = ReviewDecision(record_data["review_decision"])

                report = InvestigationReport(
                    patient_id=record_data["patient_id"],
                    question=record_data["question"],
                    conclusion=record_data["conclusion"],
                    evidence=record_data.get("evidence", []),
                    confidence=record_data["confidence"],
                    review_required=record_data.get("review_required", True),
                    trace_id=record_data["trace_id"],
                    generated_at=datetime.fromisoformat(record_data["generated_at"]) if record_data.get("generated_at") else datetime.utcnow(),
                    agent_results=agent_results,
                    reviewed=record_data.get("reviewed", False),
                    review_decision=review_decision,
                    reviewer_id=record_data.get("reviewer_id"),
                    review_notes=record_data.get("review_notes"),
                    reviewed_at=datetime.fromisoformat(record_data["reviewed_at"]) if record_data.get("reviewed_at") else None,
                )

                manager.save_investigation(report)
                restored += 1

            except Exception as e:
                click.echo(f"  Warning: Skipped record {record_data.get('trace_id', 'unknown')}: {e}")
                skipped += 1

        click.echo(f"✓ Restore complete: {restored} records restored, {skipped} skipped")

    except json.JSONDecodeError as e:
        click.echo(f"✗ Invalid JSON file: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Restore failed: {e}", err=True)
        sys.exit(1)


@db.command()
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv"]), default="json", help="Export format")
@click.option("--output", "-o", help="Output file path", default=None)
@click.option("--include-deleted/--no-deleted", help="Include soft-deleted records", default=False)
@click.option("--database-url", help="Database URL", default=None)
def export(fmt: str, output: str | None, include_deleted: bool, database_url: str | None):
    """Export investigations to JSON or CSV."""
    from .db import DatabaseManager

    manager = DatabaseManager(database_url)
    manager.create_tables()

    # Generate default filename if not provided
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"aegis_export_{timestamp}.{fmt}"

    output_path = Path(output)

    click.echo(f"Exporting investigations to {output_path}...")

    try:
        data = manager.export_investigations(format=fmt, include_deleted=include_deleted)

        with open(output_path, "w") as f:
            f.write(data)

        # Get export stats
        records = manager.get_all_investigations(include_deleted=include_deleted)
        click.echo(f"✓ Export complete: {len(records)} records exported")
        click.echo(f"✓ File size: {output_path.stat().st_size:,} bytes")

    except Exception as e:
        click.echo(f"✗ Export failed: {e}", err=True)
        sys.exit(1)


@db.command()
@click.argument("trace_id")
@click.option("--database-url", help="Database URL", default=None)
def soft_delete(trace_id: str, database_url: str | None):
    """Soft delete an investigation record."""
    from .db import DatabaseManager

    manager = DatabaseManager(database_url)
    manager.create_tables()

    click.echo(f"Soft deleting investigation {trace_id}...")

    if manager.soft_delete(trace_id):
        click.echo(f"✓ Investigation {trace_id} soft deleted")
    else:
        click.echo(f"✗ Investigation {trace_id} not found", err=True)
        sys.exit(1)


@db.command()
@click.argument("trace_id")
@click.option("--database-url", help="Database URL", default=None)
def restore_record(trace_id: str, database_url: str | None):
    """Restore a soft-deleted investigation record."""
    from .db import DatabaseManager

    manager = DatabaseManager(database_url)
    manager.create_tables()

    click.echo(f"Restoring investigation {trace_id}...")

    if manager.restore(trace_id):
        click.echo(f"✓ Investigation {trace_id} restored")
    else:
        click.echo(f"✗ Investigation {trace_id} not found or not deleted", err=True)
        sys.exit(1)


@db.command()
@click.option("--database-url", help="Database URL", default=None)
@click.option("--include-deleted/--no-deleted", help="Include soft-deleted records", default=False)
def stats(database_url: str | None, include_deleted: bool):
    """Show database statistics."""
    from .db import DatabaseManager

    manager = DatabaseManager(database_url)
    manager.create_tables()

    total = manager.count_investigations(include_deleted=True)
    active = manager.count_investigations(include_deleted=False)
    deleted = total - active

    click.echo("Database Statistics:")
    click.echo(f"  Total records: {total}")
    click.echo(f"  Active records: {active}")
    click.echo(f"  Soft-deleted: {deleted}")

    if include_deleted:
        records = manager.get_all_investigations(include_deleted=True)
        if records:
            reviewed = sum(1 for r in records if r.reviewed)
            click.echo(f"  Reviewed: {reviewed}")
            click.echo(f"  Pending review: {active - reviewed}")


if __name__ == "__main__":
    db()
