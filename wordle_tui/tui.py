"""Textual TUI implementation for Dracula Italian Wordle."""

from __future__ import annotations

import subprocess
from typing import Dict, List, Optional

from rich.text import Text
from textual import events, on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, ProgressBar, Static

from wordle_tui.dictionary import WordleDictionary
from wordle_tui.game import GameStatus, LetterState, WordleGame
from wordle_tui.stats import WordleStats


# Dracula Palette constants
BG_SCREEN = "#1e1f29"
BG_CARD = "#282a36"
BG_SELECT = "#44475a"
BORDER_PRIMARY = "#bd93f9"
BORDER_SECONDARY = "#6272a4"
ACCENT_PINK = "#ff79c6"
ACCENT_GREEN = "#50fa7b"
ACCENT_CYAN = "#8be9fd"
ACCENT_YELLOW = "#f1fa8c"
ACCENT_ORANGE = "#ffb86c"
ALERT_RED = "#ff5555"
FG_MAIN = "#f8f8f2"
FG_MUTED = "#6272a4"


TCSS = f"""
Screen {{
    background: {BG_SCREEN};
    color: {FG_MAIN};
    padding: 0 1;
    overflow: hidden;
}}

#top-bar {{
    height: 1;
    width: 100%;
    margin-top: 0;
    layout: horizontal;
    background: {BG_SCREEN};
}}

#top-title {{
    width: auto;
    color: {ACCENT_PINK};
    text-style: bold;
    margin-right: 2;
}}

#top-pills {{
    width: auto;
    color: {FG_MUTED};
    margin-right: 2;
}}

#top-stats {{
    width: 1fr;
    text-align: right;
    color: {ACCENT_CYAN};
}}

#hero-card {{
    height: 7;
    width: 100%;
    background: {BG_CARD};
    border: round {BORDER_PRIMARY};
    padding: 0 1;
    layout: horizontal;
    margin-bottom: 1;
}}

#hero-logo {{
    width: 32;
    height: 5;
    color: {ACCENT_PURPLE if 'ACCENT_PURPLE' in globals() else BORDER_PRIMARY};
    content-align: left middle;
}}

#hero-meta {{
    width: 1fr;
    height: 5;
    layout: vertical;
    content-align: left middle;
    padding-left: 1;
}}

.hero-line {{
    height: 1;
}}

#workspace {{
    height: 1fr;
    width: 100%;
    layout: vertical;
    overflow-y: auto;
    scrollbar-gutter: stable;
}}

#board-container {{
    width: 100%;
    height: auto;
    align: center top;
    margin-bottom: 1;
}}

.wordle-row {{
    height: 3;
    width: 100%;
    layout: horizontal;
    align: center middle;
    margin-bottom: 0;
}}

.tile {{
    width: 5;
    height: 3;
    content-align: center middle;
    text-style: bold;
    margin: 0 1;
    border: round {BORDER_SECONDARY};
    background: {BG_CARD};
    color: {FG_MUTED};
}}

.tile-typing {{
    border: round {ACCENT_PINK};
    color: {FG_MAIN};
    background: {BG_CARD};
}}

.tile-correct {{
    background: {ACCENT_GREEN};
    border: round {ACCENT_GREEN};
    color: #1e1f29;
}}

.tile-present {{
    background: {ACCENT_YELLOW};
    border: round {ACCENT_YELLOW};
    color: #1e1f29;
}}

.tile-absent {{
    background: {BG_SELECT};
    border: round {BG_SELECT};
    color: {FG_MUTED};
}}

#keyboard-container {{
    width: 100%;
    height: auto;
    layout: vertical;
    align: center top;
    margin-top: 1;
    margin-bottom: 0;
}}

#kb-header {{
    width: 100%;
    text-align: center;
    color: {FG_MUTED};
    text-style: dim;
    margin-bottom: 0;
}}

.kb-row {{
    height: 1;
    width: 100%;
    layout: horizontal;
    align: center middle;
    margin-bottom: 0;
}}

.kb-key {{
    width: 3;
    height: 1;
    content-align: center middle;
    text-style: bold;
    margin: 0 1;
    background: transparent;
    border: none;
    color: {ACCENT_CYAN};
}}

.kb-correct {{
    background: {ACCENT_GREEN};
    border: none;
    color: #1e1f29;
}}

.kb-present {{
    background: {ACCENT_YELLOW};
    border: none;
    color: #1e1f29;
}}

.kb-absent {{
    background: transparent;
    border: none;
    color: {BG_SELECT};
    text-style: strike;
}}

#footer-bar {{
    height: 1;
    width: 100%;
    layout: horizontal;
    background: {BG_SCREEN};
}}

#footer-hints {{
    width: 1fr;
    color: {FG_MUTED};
}}

#footer-status {{
    width: auto;
    color: {ACCENT_PINK};
    text-style: bold;
}}

/* Modals */
ModalScreen {{
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}}

.modal-dialog {{
    width: 60;
    height: auto;
    max-height: 85%;
    background: {BG_CARD};
    border: round {BORDER_PRIMARY};
    padding: 1 2;
    overflow-y: auto;
}}

.modal-title {{
    color: {ACCENT_PINK};
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}}

.modal-subtitle {{
    color: {ACCENT_CYAN};
    text-align: center;
    margin-bottom: 1;
}}

.modal-text {{
    color: {FG_MAIN};
    margin-bottom: 1;
}}

.modal-buttons {{
    layout: horizontal;
    align: center middle;
    height: 3;
    margin-top: 1;
}}

.dialog-btn {{
    margin: 0 1;
    background: {BG_SELECT};
    color: {FG_MAIN};
    border: round {BORDER_PRIMARY};
}}

.dialog-btn:hover {{
    background: {ACCENT_PINK};
    color: #1e1f29;
}}

.stat-row {{
    layout: horizontal;
    height: 1;
    margin: 0 0;
}}

.stat-label {{
    width: 15;
    color: {FG_MUTED};
}}

.stat-val {{
    width: 1fr;
    color: {ACCENT_GREEN};
    text-style: bold;
}}

.len-pill {{
    padding: 0 1;
    color: {FG_MUTED};
    background: {BG_CARD};
}}

.len-pill:hover {{
    color: {FG_MAIN};
    background: {BG_SELECT};
}}

.len-pill-active {{
    color: {ACCENT_PINK};
    background: {BG_SELECT};
    text-style: bold;
}}

.pause-grid {{
    layout: grid;
    grid-size: 2;
    grid-gutter: 1;
    width: 100%;
    height: auto;
    margin: 1 0;
}}

.pause-grid Button {{
    width: 100%;
    height: 3;
}}

.len-grid {{
    layout: grid;
    grid-size: 3;
    grid-gutter: 1;
    width: 100%;
    height: auto;
    margin: 1 0;
}}

.len-grid Button {{
    width: 100%;
    height: 3;
}}
"""


class LengthPillWidget(Static):
    """Clickable word length pill in top bar."""
    def __init__(self, length: int) -> None:
        super().__init__(f"[{length}L]", id=f"pill-{length}", classes="len-pill")
        self.length = length

    def on_click(self) -> None:
        self.app.run_worker(self.app.change_word_length(self.length))


class TileWidget(Static):
    """Single Wordle letter tile."""
    pass


class KeyWidget(Static):
    """Clickable alphabet letter tracker."""
    def __init__(self, key_id: str) -> None:
        super().__init__(key_id, id=f"kb-{key_id}", classes="kb-key")
        self.key_id = key_id

    def on_click(self) -> None:
        self.app.on_virtual_key(self.key_id)


class GameOverModal(ModalScreen[None]):
    """Modal displayed when game is won or lost."""

    def __init__(self, game: WordleGame, stats: WordleStats) -> None:
        super().__init__()
        self.game = game
        self.stats = stats

    def compose(self) -> ComposeResult:
        won = self.game.status == GameStatus.WON
        title = "🎉 VITTORIA ECCELLENTE!" if won else "💀 PARTITA TERMINATA"
        title_color = ACCENT_GREEN if won else ALERT_RED

        yield Vertical(
            Label(title, classes="modal-title", id="go-title"),
            Label(
                f"La parola segreta era: [bold {ACCENT_YELLOW}]{self.game.target}[/]",
                classes="modal-subtitle",
            ),
            Label(
                f"Tentativi utilizzati: [bold]{self.game.attempt_count} / {self.game.max_attempts}[/]  •  "
                f"Serie attuale: [bold {ACCENT_ORANGE}]🔥 {self.stats.current_streak}[/]",
                classes="modal-text",
            ),
            Static(self._build_emoji_box(), id="emoji-box"),
            Horizontal(
                Button("📋 Copia Griglia Emoji", id="btn-copy", classes="dialog-btn"),
                Button("🔄 Nuova Partita [Enter]", id="btn-new", classes="dialog-btn", variant="primary"),
                Button("Chiudi [Esc]", id="btn-close", classes="dialog-btn"),
                classes="modal-buttons",
            ),
            classes="modal-dialog",
        )

    def _build_emoji_box(self) -> str:
        lines = [f"[bold {ACCENT_CYAN}]{self.game.get_share_grid()}[/]"]
        return "\n".join(lines)

    @on(Button.Pressed, "#btn-copy")
    def action_copy(self) -> None:
        grid_text = self.game.get_share_grid()
        copied = False
        try:
            p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p.communicate(input=grid_text.encode("utf-8"), timeout=2)
            if p.returncode == 0:
                copied = True
        except Exception:
            pass

        if copied:
            self.app.flash_status("Griglia copiata negli appunti (Wayland)!")
        else:
            self.app.flash_status("Griglia visibile nel dialog!")

    @on(Button.Pressed, "#btn-new")
    def action_new_game(self) -> None:
        self.dismiss()
        self.app.start_new_game()

    @on(Button.Pressed, "#btn-close")
    def action_close(self) -> None:
        self.dismiss()

    def on_key(self, event: events.Key) -> None:
        if event.key in ("enter", "n"):
            self.dismiss()
            self.app.start_new_game()
        elif event.key in ("escape", "q"):
            self.dismiss()


class LengthModal(ModalScreen[int]):
    """Modal dialog to select word length."""

    def __init__(self, current_length: int, available_lengths: List[int]) -> None:
        super().__init__()
        self.current_length = current_length
        self.available_lengths = available_lengths

    def compose(self) -> ComposeResult:
        buttons = []
        for l in self.available_lengths:
            prefix = "★ " if l == self.current_length else ""
            btn = Button(f"{prefix}{l} Lettere", id=f"len-{l}", classes="dialog-btn")
            if l == self.current_length:
                btn.variant = "primary"
            buttons.append(btn)

        yield Vertical(
            Label("📏 SCEGLI LA LUNGHEZZA DELLA PAROLA", classes="modal-title"),
            Label("Seleziona il numero di lettere per le prossime partite:", classes="modal-subtitle"),
            Grid(*buttons, classes="len-grid"),
            Horizontal(
                Button("Annulla [Esc]", id="btn-cancel", classes="dialog-btn"),
                classes="modal-buttons",
            ),
            classes="modal-dialog",
        )

    @on(Button.Pressed)
    def on_button(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("len-"):
            val = int(event.button.id.split("-")[1])
            self.dismiss(val)
        elif event.button.id == "btn-cancel":
            self.dismiss(None)

    def on_key(self, event: events.Key) -> None:
        if event.key in ("escape", "q"):
            self.dismiss(None)
        elif event.key.isdigit():
            val = int(event.key)
            if val in self.available_lengths:
                self.dismiss(val)


class StatsModal(ModalScreen[None]):
    """Modal displaying gameplay stats and guess distribution."""

    def __init__(self, stats: WordleStats, current_length: int) -> None:
        super().__init__()
        self.stats = stats
        self.current_length = current_length

    def compose(self) -> ComposeResult:
        total = self.stats.total_played
        won = self.stats.total_won
        pct = self.stats.win_percentage
        streak = self.stats.current_streak
        max_s = self.stats.max_streak

        l_stats = self.stats.get_length_stats(self.current_length)
        l_played = l_stats.get("played", 0)
        l_won = l_stats.get("won", 0)
        l_pct = int(round((l_won / l_played * 100))) if l_played > 0 else 0

        # Distribution bars
        dist = self.stats.guess_distribution
        max_dist = max(dist.values()) if any(dist.values()) else 1

        dist_lines = []
        for att in range(1, 7):
            count = dist.get(str(att), 0)
            bar_len = int((count / max_dist) * 25) if max_dist > 0 else 0
            bar = "█" * bar_len
            dist_lines.append(
                f"[bold {FG_MAIN}]{att}[/] | [bold {ACCENT_GREEN}]{bar:<25}[/] [bold {FG_MAIN}]{count}[/]"
            )

        dist_text = "\n".join(dist_lines)

        yield Vertical(
            Label("📊 STATISTICHE WORDLE ITALIANO", classes="modal-title"),
            Label(
                f"[bold {ACCENT_CYAN}]Totali:[/] Giocate: [bold]{total}[/] • Vinte: [bold {ACCENT_GREEN}]{won}[/] ({pct}%) • "
                f"Serie: [bold {ACCENT_ORANGE}]🔥 {streak}[/] (Max: {max_s})",
                classes="modal-text",
            ),
            Label(
                f"[bold {BORDER_PRIMARY}]Lunghezza {self.current_length}L:[/] Giocate: [bold]{l_played}[/] • "
                f"Vinte: [bold {ACCENT_GREEN}]{l_won}[/] ({l_pct}%) • Serie: [bold {ACCENT_ORANGE}]🔥 {l_stats.get('current_streak', 0)}[/]",
                classes="modal-text",
            ),
            Label("DISTRIBUZIONE TENTATIVI:", classes="modal-subtitle"),
            Static(dist_text, classes="modal-text"),
            Horizontal(
                Button("Chiudi [Esc]", id="btn-close", classes="dialog-btn"),
                classes="modal-buttons",
            ),
            classes="modal-dialog",
        )

    @on(Button.Pressed, "#btn-close")
    def on_close(self) -> None:
        self.dismiss()

    def on_key(self, event: events.Key) -> None:
        if event.key in ("escape", "enter", "q", "s"):
            self.dismiss()


class HelpModal(ModalScreen[None]):
    """Modal displaying rules and keybindings."""

    def compose(self) -> ComposeResult:
        rules = (
            f"[bold {ACCENT_PINK}]COME SI GIOCA A WORDLE ITALIANO:[/]\n"
            f"1. Indovina la parola segreta in 6 tentativi.\n"
            f"2. Ogni tentativo deve essere una parola italiana valida.\n"
            f"3. Dopo ogni invio, i colori delle caselle cambieranno:\n\n"
            f"  [bold {ACCENT_GREEN}]🟩 VERDE[/]    : La lettera è presente nella parola ed è nella posizione corretta.\n"
            f"  [bold {ACCENT_YELLOW}]🟨 GIALLO[/]   : La lettera è presente nella parola ma in una posizione diversa.\n"
            f"  [bold {FG_MUTED}]⬛ GRIGIO[/]   : La lettera non è presente nella parola.\n\n"
            f"[bold {ACCENT_CYAN}]COMANDI DA TASTIERA:[/]\n"
            f"• [bold {FG_MAIN}]A-Z[/]         : Digita le lettere della parola\n"
            f"• [bold {FG_MAIN}]Enter[/]       : Conferma e invia la parola\n"
            f"• [bold {FG_MAIN}]Backspace[/]   : Cancella l'ultima lettera digitata\n"
            f"• [bold {FG_MAIN}]Esc[/]         : Apri menu pausa (per nuova partita, statistiche, esci)\n"
            f"• [bold {FG_MAIN}]4, 5, 6, 7, 8[/] : Cambia lunghezza parola (o clicca in alto)\n"
            f"• [bold {FG_MAIN}]Ctrl+N[/]      : Nuova partita rapida\n"
            f"• [bold {FG_MAIN}]Ctrl+S[/]      : Mostra statistiche\n"
            f"• [bold {FG_MAIN}]Ctrl+L[/]      : Menu scelta lunghezza\n"
            f"• [bold {FG_MAIN}]? / F1[/]      : Questa guida\n"
            f"• [bold {FG_MAIN}]Ctrl+Q[/]      : Esci dal gioco"
        )

        yield Vertical(
            Label("📖 GUIDA & REGOLE", classes="modal-title"),
            Static(rules, classes="modal-text"),
            Horizontal(
                Button("Ho capito [Esc]", id="btn-close", classes="dialog-btn"),
                classes="modal-buttons",
            ),
            classes="modal-dialog",
        )

    @on(Button.Pressed, "#btn-close")
    def on_close(self) -> None:
        self.dismiss()

    def on_key(self, event: events.Key) -> None:
        if event.key in ("escape", "enter", "q", "h", "question_mark"):
            self.dismiss()


class PauseModal(ModalScreen[Optional[str]]):
    """Pause & options menu shown when Esc is pressed during game."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("⏸️ PARTITA IN PAUSA", classes="modal-title"),
            Label("Seleziona un'azione [Enter/Esc per riprendere]:", classes="modal-subtitle"),
            Grid(
                Button("▶️ Riprendi [Esc]", id="btn-resume", classes="dialog-btn", variant="primary"),
                Button("🔄 Nuova Partita [N]", id="btn-new", classes="dialog-btn"),
                Button("📏 Lunghezza [L]", id="btn-len", classes="dialog-btn"),
                Button("📊 Statistiche [S]", id="btn-stats", classes="dialog-btn"),
                Button("📖 Regole [H]", id="btn-help", classes="dialog-btn"),
                Button("🚪 Esci [Q]", id="btn-quit", classes="dialog-btn"),
                classes="pause-grid",
            ),
            classes="modal-dialog",
        )

    @on(Button.Pressed)
    def on_btn(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-resume":
            self.dismiss("resume")
        elif bid == "btn-new":
            self.dismiss("new")
        elif bid == "btn-len":
            self.dismiss("len")
        elif bid == "btn-stats":
            self.dismiss("stats")
        elif bid == "btn-help":
            self.dismiss("help")
        elif bid == "btn-quit":
            self.dismiss("quit")

    def on_key(self, event: events.Key) -> None:
        key = event.key.lower()
        if key in ("escape", "enter"):
            self.dismiss("resume")
        elif key == "n":
            self.dismiss("new")
        elif key == "l":
            self.dismiss("len")
        elif key == "s":
            self.dismiss("stats")
        elif key in ("h", "question_mark"):
            self.dismiss("help")
        elif key == "q":
            self.dismiss("quit")
        elif key.isdigit() and int(key) in (4, 5, 6, 7, 8):
            self.dismiss(f"len-{key}")


class WordleApp(App[None]):
    """Dracula Italian Wordle TUI Application."""

    CSS = TCSS
    TITLE = "Wordle TUI - Dracula Edition"

    def __init__(self, initial_length: int = 5) -> None:
        super().__init__()
        self.dict_manager = WordleDictionary.get_instance()
        self.stats_manager = WordleStats()
        self.word_length = initial_length
        self.game: WordleGame = self._create_game(self.word_length)
        self.status_clear_timer = None

    def _create_game(self, length: int) -> WordleGame:
        target = self.dict_manager.get_random_target(length)
        return WordleGame(target)

    def compose(self) -> ComposeResult:
        # Top Bar with interactive length indicators
        yield Horizontal(
            Static("󰬡 WORDLE ITALIANO", id="top-title"),
            Static("", id="top-pills"),
            Static("", id="top-stats"),
            id="top-bar",
        )

        # Hero Card
        logo_art = (
            "╦ ╦╔═╗╦═╗╔╦╗╦  ╔═╗\n"
            "║║║║ ║╠╦╝ ║║║  ║╣ \n"
            "╚╩╝╚═╝╩╚══╩╝╩═╝╚═╝"
        )
        yield Horizontal(
            Static(logo_art, id="hero-logo"),
            Vertical(
                Static("", id="hero-meta-len", classes="hero-line"),
                Static("", id="hero-meta-dict", classes="hero-line"),
                Static("", id="hero-meta-streak", classes="hero-line"),
                id="hero-meta",
            ),
            id="hero-card",
        )

        # Build initial board tiles
        board_rows = []
        for r in range(self.game.max_attempts):
            tiles = [TileWidget("", id=f"tile-{r}-{c}", classes="tile") for c in range(self.word_length)]
            board_rows.append(Horizontal(*tiles, classes="wordle-row", id=f"row-{r}"))
        board = Container(*board_rows, id="board-container")

        # Build clean alphabet letter tracker (QWERTY layout)
        r1 = ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"]
        r2 = ["A", "S", "D", "F", "G", "H", "J", "K", "L"]
        r3 = ["Z", "X", "C", "V", "B", "N", "M"]

        row1_keys = [KeyWidget(k) for k in r1]
        row2_keys = [KeyWidget(k) for k in r2]
        row3_keys = [KeyWidget(k) for k in r3]
        keyboard = Container(
            Static("── LETTERE DELL'ALFABETO (Stato) ──", id="kb-header"),
            Horizontal(*row1_keys, classes="kb-row"),
            Horizontal(*row2_keys, classes="kb-row"),
            Horizontal(*row3_keys, classes="kb-row"),
            id="keyboard-container",
        )

        # Workspace with grid and virtual keyboard
        yield ScrollableContainer(
            board,
            keyboard,
            id="workspace",
        )

        # Footer Bar
        yield Horizontal(
            Static(
                "[Enter] Invia  [⌫] Cancella  [4-8] Lunghezza  [Esc] Menu / Pausa  [?] Aiuto",
                id="footer-hints",
            ),
            Static("", id="footer-status"),
            id="footer-bar",
        )

    def on_mount(self) -> None:
        self._refresh_board_tiles()
        self._refresh_keyboard_colors()
        self._update_headers()

    def _update_headers(self) -> None:
        # Update pills with clear number keys [4] 4L  [5] 5L  [6] 6L  [7] 7L  [8] 8L
        pills = []
        for l in (4, 5, 6, 7, 8):
            if l == self.word_length:
                pills.append(f"[bold #1e1f29 on #ff79c6] [{l}] {l}L [/]")
            else:
                pills.append(f"[bold #6272a4] [{l}] {l}L [/]")
        self.query_one("#top-pills", Static).update(" ".join(pills))

        # Update stats top
        tot = self.stats_manager.total_played
        won = self.stats_manager.total_won
        pct = self.stats_manager.win_percentage
        streak = self.stats_manager.current_streak
        top_text = f"Vinte: [bold {ACCENT_GREEN}]{won}/{tot}[/] ({pct}%) • [bold {ACCENT_ORANGE}]🔥 {streak}[/]"
        self.query_one("#top-stats", Static).update(top_text)

        # Hero Meta
        t_cnt, g_cnt = self.dict_manager.get_counts(self.word_length)
        self.query_one("#hero-meta-len", Static).update(
            f"Modalità: [bold {ACCENT_CYAN}]{self.word_length} Lettere[/]  •  Tentativo: [bold {ACCENT_YELLOW}]{self.game.attempt_count + 1} / {self.game.max_attempts}[/]"
        )
        self.query_one("#hero-meta-dict", Static).update(
            f"Dizionario Italiano: [bold {FG_MAIN}]{t_cnt:,}[/] segrete • [bold {FG_MAIN}]{g_cnt:,}[/] ammesse"
        )
        self.query_one("#hero-meta-streak", Static).update(
            f"Record Serie: [bold {ACCENT_ORANGE}]{self.stats_manager.max_streak}[/]  •  Premi [bold {FG_MAIN}]4, 5, 6, 7, 8[/] per cambiare lunghezza"
        )

    def _refresh_board_tiles(self) -> None:
        # Existing submitted guesses
        for row_idx, (guess, evals) in enumerate(zip(self.game.guesses, self.game.evaluations)):
            for col_idx, (letter, state) in enumerate(zip(guess, evals)):
                tile = self.query_one(f"#tile-{row_idx}-{col_idx}", TileWidget)
                tile.update(letter)
                tile.remove_class("tile-typing", "tile-correct", "tile-present", "tile-absent")
                if state == LetterState.CORRECT:
                    tile.add_class("tile-correct")
                elif state == LetterState.PRESENT:
                    tile.add_class("tile-present")
                elif state == LetterState.ABSENT:
                    tile.add_class("tile-absent")

        # Current active typing row
        curr_row = self.game.attempt_count
        if curr_row < self.game.max_attempts:
            typed = self.game.current_input
            for col_idx in range(self.word_length):
                tile = self.query_one(f"#tile-{curr_row}-{col_idx}", TileWidget)
                tile.remove_class("tile-typing", "tile-correct", "tile-present", "tile-absent")
                if col_idx < len(typed):
                    tile.update(typed[col_idx])
                    tile.add_class("tile-typing")
                else:
                    tile.update("")

        # Remaining empty rows
        for r in range(curr_row + 1, self.game.max_attempts):
            for c in range(self.word_length):
                tile = self.query_one(f"#tile-{r}-{c}", TileWidget)
                tile.update("")
                tile.remove_class("tile-typing", "tile-correct", "tile-present", "tile-absent")

    def _refresh_keyboard_colors(self) -> None:
        for char, state in self.game.keyboard_states.items():
            key_widget = self.query_one(f"#kb-{char}", KeyWidget)
            key_widget.remove_class("kb-correct", "kb-present", "kb-absent")
            if state == LetterState.CORRECT:
                key_widget.add_class("kb-correct")
            elif state == LetterState.PRESENT:
                key_widget.add_class("kb-present")
            elif state == LetterState.ABSENT:
                key_widget.add_class("kb-absent")

    def flash_status(self, message: str, duration: float = 3.0) -> None:
        """Display status message in footer and clear after duration."""
        status = self.query_one("#footer-status", Static)
        status.update(message)

        if self.status_clear_timer:
            self.status_clear_timer.stop()

        self.status_clear_timer = self.set_timer(duration, lambda: status.update(""))

    def on_virtual_key(self, key_id: str) -> None:
        """Handle mouse click on on-screen keyboard."""
        if key_id == "ENTER":
            self._handle_enter()
        elif key_id == "BACKSPACE":
            self._handle_backspace()
        else:
            self._handle_letter(key_id)

    @on(events.Click, "#top-pills")
    def on_top_pills_click(self) -> None:
        self.action_choose_length()

    def action_pause_menu(self) -> None:
        """Open pause menu when Esc is pressed during active game."""
        def _on_pause_result(action: Optional[str]) -> None:
            if not action or action == "resume":
                return
            if action == "new":
                self.start_new_game()
            elif action == "len":
                self.action_choose_length()
            elif action.startswith("len-"):
                l = int(action.split("-")[1])
                self.run_worker(self.change_word_length(l))
            elif action == "stats":
                self.push_screen(StatsModal(self.stats_manager, self.word_length))
            elif action == "help":
                self.push_screen(HelpModal())
            elif action == "quit":
                self.exit()

        self.push_screen(PauseModal(), _on_pause_result)

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        key = event.key

        # Standard Ctrl / Function shortcuts always available
        if key in ("ctrl+c", "ctrl+q"):
            self.exit()
            return
        if key == "ctrl+n":
            self.start_new_game()
            return
        if key == "ctrl+s":
            self.push_screen(StatsModal(self.stats_manager, self.word_length))
            return
        if key == "ctrl+l":
            self.action_choose_length()
            return
        if key in ("ctrl+h", "f1", "question_mark"):
            self.push_screen(HelpModal())
            return

        # Direct number keys 4..8 to change length
        if key.isdigit():
            val = int(key)
            if val in self.dict_manager.get_available_lengths():
                self.run_worker(self.change_word_length(val))
                return

        # Escape key: opens Pause Menu when playing, or exits if game is over
        if key == "escape":
            if self.game.status == GameStatus.PLAYING:
                self.action_pause_menu()
            else:
                self.exit()
            return

        # If game is finished, letters act as convenient shortcuts
        if self.game.status != GameStatus.PLAYING:
            if key in ("enter", "space", "n", "N"):
                self.start_new_game()
            elif key in ("s", "S"):
                self.push_screen(StatsModal(self.stats_manager, self.word_length))
            elif key in ("l", "L"):
                self.action_choose_length()
            elif key in ("q", "Q"):
                self.exit()
            elif key in ("h", "H"):
                self.push_screen(HelpModal())
            return

        # Playing state: ONLY Wordle inputs! Every single letter A-Z goes to the word!
        if key == "enter":
            self._handle_enter()
        elif key in ("backspace", "delete"):
            self._handle_backspace()
        elif len(key) == 1 and key.isalpha() and key.isascii():
            self._handle_letter(key)

    def _handle_letter(self, char: str) -> None:
        if self.game.add_letter(char):
            self._refresh_board_tiles()

    def _handle_backspace(self) -> None:
        if self.game.remove_letter():
            self._refresh_board_tiles()

    def _handle_enter(self) -> None:
        current_input = self.game.current_input
        if len(current_input) < self.word_length:
            self.flash_status(f"Inserisci {self.word_length} lettere!")
            return

        if not self.dict_manager.is_valid_guess(current_input, self.word_length):
            self.flash_status("Parola non presente nel vocabolario italiano!")
            return

        success, msg = self.game.submit_guess()
        self._refresh_board_tiles()
        self._refresh_keyboard_colors()
        self._update_headers()

        if self.game.status != GameStatus.PLAYING:
            won = self.game.status == GameStatus.WON
            self.stats_manager.record_game(
                self.word_length,
                won,
                self.game.attempt_count,
                self.game.target,
            )
            self._update_headers()
            self.push_screen(GameOverModal(self.game, self.stats_manager))
        else:
            self.flash_status(msg)

    def start_new_game(self) -> None:
        """Start a new game session with current length."""
        self.game = self._create_game(self.word_length)
        self._refresh_board_tiles()
        self._refresh_keyboard_colors()
        self._update_headers()
        self.flash_status("Nuova partita avviata!")

    async def change_word_length(self, length: int) -> None:
        """Change word length and rebuild board."""
        if length == self.word_length and self.game.status == GameStatus.PLAYING:
            return
        self.word_length = length
        self.game = self._create_game(self.word_length)

        board = self.query_one("#board-container", Container)
        await board.remove_children()

        board_rows = []
        for r in range(self.game.max_attempts):
            tiles = [TileWidget("", id=f"tile-{r}-{c}", classes="tile") for c in range(self.word_length)]
            board_rows.append(Horizontal(*tiles, classes="wordle-row", id=f"row-{r}"))
        await board.mount(*board_rows)

        self._refresh_board_tiles()
        self._refresh_keyboard_colors()
        self._update_headers()
        self.flash_status(f"Lunghezza impostata a {length} lettere!")

    def action_choose_length(self) -> None:
        """Open length selection modal."""
        def _on_select(length: Optional[int]) -> None:
            if length and length != self.word_length:
                self.run_worker(self.change_word_length(length))

        avail = [l for l in self.dict_manager.get_available_lengths() if l <= 8]
        self.push_screen(LengthModal(self.word_length, avail), _on_select)
