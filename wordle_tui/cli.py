"""Command line interface for Wordle TUI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import NoReturn

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from wordle_tui import __version__
from wordle_tui.dictionary import WordleDictionary
from wordle_tui.stats import WordleStats


def output_waybar() -> None:
    """Output single-line JSON for Waybar custom module."""
    stats = WordleStats()
    tot = stats.total_played
    won = stats.total_won
    pct = stats.win_percentage
    streak = stats.current_streak
    last = stats.stats.get("last_played")

    if tot == 0:
        payload = {
            "text": "󰬡 Wordle IT",
            "tooltip": "Wordle TUI - Italiano\nNessuna partita giocata ancora.\nAvvia con 'wordle-tui'",
            "class": "idle",
        }
    else:
        last_info = ""
        if last:
            st = "Vinta" if last.get("won") else "Persa"
            last_info = f"\nUltima: {last.get('length')}L ({st} in {last.get('attempts')} tentativi)"

        css_class = "won" if (last and last.get("won")) else "played"
        payload = {
            "text": f"󰬡 {pct}% 🔥{streak}",
            "tooltip": (
                f"Wordle TUI - Italiano\n"
                f"Partite giocate: {tot}\n"
                f"Vittorie: {won} ({pct}%)\n"
                f"Serie attuale: 🔥 {streak} (Max: {stats.max_streak})"
                f"{last_info}"
            ),
            "class": css_class,
        }

    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def print_stats_cli() -> None:
    """Print game stats to stdout with Rich formatting."""
    console = Console()
    stats = WordleStats()

    if stats.total_played == 0:
        console.print("[yellow]Nessuna statistica disponibile. Gioca la tua prima partita con 'wordle-tui'![/]")
        return

    table = Table(title="📊 Statistiche Wordle Italiano", style="bold #bd93f9")
    table.add_column("Parametro", style="#8be9fd")
    table.add_column("Valore", style="#50fa7b")

    table.add_row("Partite Totali", str(stats.total_played))
    table.add_row("Partite Vinte", f"{stats.total_won} ({stats.win_percentage}%)")
    table.add_row("Serie Attuale", f"🔥 {stats.current_streak}")
    table.add_row("Serie Massima", f"🏆 {stats.max_streak}")

    console.print(table)

    # Per-length breakdown
    by_len = stats.stats.get("by_length", {})
    if by_len:
        len_table = Table(title="📏 Dettaglio per Lunghezza Parola", style="bold #6272a4")
        len_table.add_column("Lunghezza", style="#ff79c6")
        len_table.add_column("Giocate", style="#f8f8f2")
        len_table.add_column("Vinte", style="#50fa7b")
        len_table.add_column("Win %", style="#8be9fd")
        len_table.add_column("Serie", style="#ffb86c")

        for l_key in sorted(by_len.keys(), key=lambda x: int(x)):
            data = by_len[l_key]
            p = data.get("played", 0)
            w = data.get("won", 0)
            pct = int(round((w / p * 100))) if p > 0 else 0
            len_table.add_row(f"{l_key} Lettere", str(p), str(w), f"{pct}%", f"🔥 {data.get('current_streak', 0)}")

        console.print(len_table)


def run_update_dict() -> None:
    """Download and rebuild dictionary from upstream."""
    console = Console()
    console.print("[bold #8be9fd]Aggiornamento del vocabolario italiano in corso...[/]")

    def progress(msg: str) -> None:
        console.print(f" • [dim #6272a4]{msg}[/]")

    try:
        targets, guesses = WordleDictionary.update_from_upstream(callback=progress)
        console.print(
            f"[bold #50fa7b]Vocabolario aggiornato con successo![/] "
            f"Totale: [cyan]{targets:,}[/] soluzioni e [cyan]{guesses:,}[/] parole ammesse."
        )
    except Exception as exc:
        console.print(f"[bold #ff5555]Errore durante l'aggiornamento:[/] {exc}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="wordle-tui",
        description="Dracula-themed Wordle Italiano TUI con lunghezza parole personalizzabile.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-l", "--length",
        type=int,
        default=5,
        help="Lunghezza iniziale della parola (default: 5, supporto 4..8)",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Comandi disponibili")

    # Subcomando: waybar
    subparsers.add_parser("waybar", help="Output JSON a riga singola per modulo Waybar")

    # Subcomando: stats
    subparsers.add_parser("stats", help="Visualizza statistiche di gioco da riga di comando")

    # Subcomando: update-dict
    subparsers.add_parser("update-dict", help="Scarica e aggiorna il vocabolario italiano completo")

    args = parser.parse_args()

    if args.subcommand == "waybar":
        output_waybar()
        return

    if args.subcommand == "stats":
        print_stats_cli()
        return

    if args.subcommand == "update-dict":
        run_update_dict()
        return

    # Start TUI App
    from wordle_tui.tui import WordleApp

    # Validate length
    dict_manager = WordleDictionary.get_instance()
    avail = dict_manager.get_available_lengths()
    chosen_len = args.length if args.length in avail else 5

    app = WordleApp(initial_length=chosen_len)
    app.run()


if __name__ == "__main__":
    main()
