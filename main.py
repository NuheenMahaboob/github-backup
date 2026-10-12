from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from backup import backup_repository

console = Console()


def main():
    console.print(
        Panel.fit(
            "[bold cyan]GitHub Backup Tool[/bold cyan]",
            border_style="green",
        )
    )

    while True:

        url = Prompt.ask(
            "\n[cyan]Paste GitHub Repository URL[/cyan]"
        ).strip()

        if url == "":
            continue

        try:
            backup_repository(url)

        except Exception as e:
            console.print(f"\n[red]{e}[/red]")

        again = Prompt.ask(
            "\nBackup another repository? (y/n)",
            default="n"
        )

        if again.lower() != "y":
            break


if __name__ == "__main__":
    main()
