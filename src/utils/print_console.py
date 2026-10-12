from rich.console import Console
from rich.panel import Panel

console = Console()


def print_step(number, message):
    console.rule(f"[bold cyan]{number} - {message}[/bold cyan]")


def print_success(message):
    console.print(f"[bold green]✓[/bold green] {message}")


def print_info(message):
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message):
    console.print(f"[bold yellow]⚠ {message}[/bold yellow]")


def print_error(message):
    console.print(f"[bold red]✗ {message}")


def print_header(message):  # to complete
    console.print(f"[bold green]✓[/bold green] {message}")
