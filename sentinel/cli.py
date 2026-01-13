"""Sentinel CLI interface."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from sentinel.scanner import VulnerabilityScanner
from sentinel.parsers import ParserFactory
from sentinel.sbom import SBOMGenerator
from sentinel.talon_client import TalonClient
from sentinel.config import config

console = Console()


@click.group()
@click.version_option(version="1.0.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Sentinel - Dependency Vulnerability Scanner"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if verbose:
        config.log_level = "DEBUG"


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--package-manager", "-p", type=click.Choice(["npm", "pip", "composer", "auto"]),
              default="auto", help="Package manager to scan")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", "output_format", type=click.Choice(["json", "table", "cyclonedx", "spdx"]),
              default="table", help="Output format")
@click.option("--severity", "-s", type=click.Choice(["low", "medium", "high", "critical"]),
              default="low", help="Minimum severity to report")
@click.option("--include-dev", is_flag=True, help="Include dev dependencies")
@click.option("--post-to-talon", is_flag=True, help="Post results to Talon API")
@click.pass_context
def scan(
    ctx: click.Context,
    path: str,
    package_manager: str,
    output: Optional[str],
    output_format: str,
    severity: str,
    include_dev: bool,
    post_to_talon: bool,
) -> None:
    """Scan a project for dependency vulnerabilities."""
    project_path = Path(path).resolve()
    
    console.print(f"\n[bold blue]🔍 Scanning project:[/] {project_path}\n")
    
    try:
        # Run the async scan
        result = asyncio.run(_run_scan(
            project_path=project_path,
            package_manager=package_manager,
            severity=severity,
            include_dev=include_dev,
            post_to_talon=post_to_talon,
        ))
        
        # Output results
        if output_format == "table":
            _display_table(result)
        elif output_format == "json":
            output_data = json.dumps(result, indent=2, default=str)
            if output:
                Path(output).write_text(output_data)
                console.print(f"[green]Results written to {output}[/]")
            else:
                console.print(output_data)
        elif output_format in ("cyclonedx", "spdx"):
            sbom_generator = SBOMGenerator()
            sbom_data = sbom_generator.generate(result, format=output_format)
            if output:
                Path(output).write_text(sbom_data)
                console.print(f"[green]SBOM written to {output}[/]")
            else:
                console.print(sbom_data)
        
        # Exit with error code if vulnerabilities found
        if result.get("vulnerable_count", 0) > 0:
            critical_high = result.get("critical_count", 0) + result.get("high_count", 0)
            if critical_high > 0:
                sys.exit(1)
                
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(2)


async def _run_scan(
    project_path: Path,
    package_manager: str,
    severity: str,
    include_dev: bool,
    post_to_talon: bool,
) -> dict:
    """Run the vulnerability scan asynchronously."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Parse dependencies
        task = progress.add_task("Parsing dependencies...", total=None)
        parser = ParserFactory.create(package_manager, project_path)
        dependencies = await parser.parse(include_dev=include_dev)
        progress.update(task, description=f"Found {len(dependencies)} dependencies")
        
        # Scan for vulnerabilities
        progress.update(task, description="Scanning for vulnerabilities...")
        scanner = VulnerabilityScanner()
        result = await scanner.scan(
            project_name=project_path.name,
            dependencies=dependencies,
            severity_threshold=severity,
        )
        progress.update(task, description="Scan complete!")
        
        # Post to Talon if requested
        if post_to_talon:
            progress.update(task, description="Posting results to Talon...")
            talon_client = TalonClient()
            await talon_client.post_scan_result(result)
            progress.update(task, description="Results posted to Talon!")
    
    return result


def _display_table(result: dict) -> None:
    """Display scan results as a formatted table."""
    # Summary
    console.print("\n[bold]📊 Scan Summary[/]")
    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")
    
    summary_table.add_row("Project", result.get("project_name", "Unknown"))
    summary_table.add_row("Package Manager", result.get("package_manager", "Unknown"))
    summary_table.add_row("Total Dependencies", str(result.get("total_dependencies", 0)))
    summary_table.add_row("Vulnerable Packages", str(result.get("vulnerable_count", 0)))
    
    console.print(summary_table)
    
    # Severity breakdown
    console.print("\n[bold]⚠️  Severity Breakdown[/]")
    severity_table = Table(show_header=True)
    severity_table.add_column("Severity", style="bold")
    severity_table.add_column("Count", justify="right")
    
    severities = [
        ("Critical", result.get("critical_count", 0), "red"),
        ("High", result.get("high_count", 0), "orange1"),
        ("Medium", result.get("medium_count", 0), "yellow"),
        ("Low", result.get("low_count", 0), "blue"),
    ]
    
    for sev_name, count, color in severities:
        severity_table.add_row(f"[{color}]{sev_name}[/]", str(count))
    
    console.print(severity_table)
    
    # Vulnerabilities list
    vulnerabilities = result.get("vulnerabilities", [])
    if vulnerabilities:
        console.print("\n[bold]🔒 Vulnerabilities Found[/]")
        vuln_table = Table(show_header=True)
        vuln_table.add_column("CVE ID", style="cyan")
        vuln_table.add_column("Package")
        vuln_table.add_column("Version")
        vuln_table.add_column("Severity")
        vuln_table.add_column("CVSS")
        vuln_table.add_column("Fixed In")
        
        severity_colors = {
            "CRITICAL": "red",
            "HIGH": "orange1",
            "MEDIUM": "yellow",
            "LOW": "blue",
        }
        
        for vuln in vulnerabilities[:20]:  # Limit display
            severity = vuln.get("severity", "UNKNOWN")
            color = severity_colors.get(severity, "white")
            vuln_table.add_row(
                vuln.get("cve_id", "N/A"),
                vuln.get("package_name", "N/A"),
                vuln.get("installed_version", "N/A"),
                f"[{color}]{severity}[/]",
                str(vuln.get("cvss_score", "N/A")),
                vuln.get("fixed_version", "N/A"),
            )
        
        console.print(vuln_table)
        
        if len(vulnerabilities) > 20:
            console.print(f"\n[dim]... and {len(vulnerabilities) - 20} more vulnerabilities[/]")
    else:
        console.print("\n[bold green]✅ No vulnerabilities found![/]")


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--format", "-f", "output_format", type=click.Choice(["cyclonedx", "spdx"]),
              default="cyclonedx", help="SBOM format")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file path")
@click.pass_context
def sbom(ctx: click.Context, path: str, output_format: str, output: str) -> None:
    """Generate a Software Bill of Materials (SBOM)."""
    project_path = Path(path).resolve()
    
    console.print(f"\n[bold blue]📦 Generating SBOM for:[/] {project_path}\n")
    
    try:
        result = asyncio.run(_generate_sbom(project_path, output_format))
        Path(output).write_text(result)
        console.print(f"[bold green]✅ SBOM generated:[/] {output}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(2)


async def _generate_sbom(project_path: Path, output_format: str) -> str:
    """Generate SBOM asynchronously."""
    parser = ParserFactory.create("auto", project_path)
    dependencies = await parser.parse(include_dev=True)
    
    sbom_generator = SBOMGenerator()
    return sbom_generator.generate(
        {
            "project_name": project_path.name,
            "dependencies": [dep.to_dict() for dep in dependencies],
        },
        format=output_format,
    )


@cli.command()
@click.option("--cve", "-c", required=True, help="CVE ID to lookup")
@click.pass_context
def lookup(ctx: click.Context, cve: str) -> None:
    """Lookup details for a specific CVE."""
    from sentinel.nvd_client import NVDClient
    
    console.print(f"\n[bold blue]🔍 Looking up:[/] {cve}\n")
    
    try:
        result = asyncio.run(_lookup_cve(cve))
        if result:
            console.print(json.dumps(result, indent=2, default=str))
        else:
            console.print(f"[yellow]CVE {cve} not found[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(2)


async def _lookup_cve(cve_id: str) -> Optional[dict]:
    """Lookup a CVE from NVD."""
    from sentinel.nvd_client import NVDClient
    
    async with NVDClient() as client:
        return await client.get_cve(cve_id)


def main() -> None:
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
