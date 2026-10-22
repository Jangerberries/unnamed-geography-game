# Unnamed geography game
# Copyright 2026 Øyvind I. Berntsen
#
# This file is part of unnamed-geography-game.
# 
# unnamed-geography-game is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# unnamed-geography-game is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with unnamed-geography-game. If not, see
# <https://www.gnu.org/licenses/>.


import json

from datetime import datetime
import time
import random

from textual.app import App
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual.validation import Function
from textual.suggester import SuggestFromList
from textual.css.query import NoMatches
from textual_autocomplete import AutoComplete
from textual.widgets import (
    Header,
    Footer,
    Input,
    Label,
    Collapsible,
    TabbedContent,
    Markdown,
    Button
)
from textual.widget import Widget
from textual.containers import (
    Center,
    Middle,
    Vertical,
    Horizontal,
    Grid,
    VerticalScroll,
)
from textual.message import Message
from typing import ClassVar
from importlib.resources import files
from unnamed_geography_game.game import borders_game

from textual.suggester import Suggester

from pathlib import Path
import inspect

from collections import defaultdict

class StatusUpdate(Message):
    def __init__(self, change):
        super().__init__()


def log_from_caller(*items):
    frame = inspect.currentframe()
    try:
        frame = frame.f_back
        instance = frame.f_locals.get("self") if frame else None
        location = f"{Path(frame.f_code.co_filename).name}:{frame.f_lineno}"

        if instance is None:
            label = "?"
        else:
            methods = []
            current = frame

            while current:
                if current.f_locals.get("self") is instance:
                    name = current.f_code.co_name
                    if not name.startswith(("<", "_")):
                        methods.append(name)
                current = current.f_back

            methods.reverse()
            label = " > ".join([type(instance).__name__, *methods])
            instance.log(f"{location}: [{label}]\n\t", *items)

    finally:
        del frame
        

class CountryCard(Vertical):

    BINDINGS = [
        Binding("ctrl+h", "get_hint", "Get a hint", priority = True),
    ]

    def on_status_update(self):
        log_from_caller(f"Updating {self.country['name']}")
        self.country = self.screen.game.countries.vs.find(name=self.country["name"])
        self.guessed_neighbors = self.screen.game.countries.guessed_borders(self.country)
        self.all_neighbors = self.country.neighbors()
        label = self.query_one(Markdown)
        label.update(self.make_title())

    def on_mount(self):
        log_from_caller(f"Mounted {self.country['name']}")

    def on_unmount(self):
        log_from_caller(f"Removing {self.country['name']}")

    def __init__(self, country):
        super().__init__(id = country["alpha3Code"])
        self.country = country

        self.all_neighbors = self.country.neighbors()

    def action_get_hint(self):
        for neighbor in self.all_neighbors:
            border = self.screen.game.countries.es.find(
                self.screen.game.countries.get_eid(
                    self.country["name"], neighbor["name"]
                )
            )
            if border["guessed"]:
                continue
            if border["hints"] >= 3:
                continue
            else:
                border["hints"] += 1
                label = self.query_one(Markdown)
                label.update(self.make_title())
                return
        self.notify("Cannot hint any further!")

    def label_neighbor(self, neighbor):
        """
        Print a neighbor name, either in plain text or obfuscated according to the hint level
        """
        
        border = self.screen.game.countries.es.find(
            self.screen.game.countries.get_eid(
                self.country["name"], neighbor["name"]
            )
        )
        
        if border["guessed"]:
            return f"{neighbor['flag']} {neighbor['name']}"
        elif border["hints"] == 0:
            return f"🇺🇳 ..."
        elif border["hints"] == 1:
            hinted = f"🇺🇳 " + ''.join(' ' if char == ' ' else '-' for char in neighbor["name"])
            return hinted
        elif border["hints"] == 2:

            hinted = f"🇺🇳 " + neighbor["name"][0] + ''.join(' ' if char == ' ' else '-' for char in neighbor["name"][1:])
            return hinted
        elif border["hints"] == 3:
            hinted =  (
                f"🇺🇳 " +
                neighbor["name"][:1] +
                ''.join(' ' if char == ' ' else '-' for char in neighbor["name"][1:-1]) +
                 neighbor["name"][-1:]
            )
            return hinted
        
        
        
    def make_title(self):
        neighbor_labels = " ".join([
            self.label_neighbor(neighbor) for neighbor in self.all_neighbors
        ])
        guessed_text = " ".join(
            [
                f"{country['flag']} {country['name']}"
                for country in self.guessed_neighbors
            ]
        )
        lat = self.country["latlng"][0]
        lng = self.country["latlng"][1]
        return (
            f"# {self.country['flag']} {self.country['name']} "
            f"({len(self.guessed_neighbors)}/{len(self.all_neighbors)}) "
            f"[🌍](https://www.google.com/maps/@{lat},{lng},5z)\n"
            f"{neighbor_labels}"
        )

    def compose(self):
        self.guessed_neighbors = self.screen.game.countries.guessed_borders(self.country)
        self.title = self.make_title()
        yield Markdown(self.title)
        country_input = CountryInput()
        yield country_input
        yield AutoComplete(
            country_input,
            candidates = [
                country["name"] for country in self.screen.game.countries.vs()
            ]
        )

    async def on_input_submitted(self, event: CountryInput.Submitted):
        input = self.query_children(CountryInput).first()

        if input.is_valid:
            log_from_caller(f"Input was {input.value}")
            await self.screen.game.guess_border(self.country["name"], input.value)
            input.clear()

class CompletedCountryTab(Vertical):
    """
    A widget to display completed countries, grouped by region in separate Collapsible widgets.
    """

    def compose(self):
        log_from_caller("I'm composing!")

        regions = {}

        for country in [
            {"country": country, "region": country["region"]} for country in [
                country for country in self.screen.game.countries.vs if all(
                    edge["guessed"] is True for edge in country.incident()
                )]
        ]:
            regions.setdefault(country["region"], []).append(country)

        regions = [
            {"name": region, "countries": countries}
            for region, countries in regions.items()
        ]
        
        texts = [
            ", ".join(
                f"{country['country']['flag']} {country['country']['name']}" for country in region["countries"]
            ) for region in regions
        ]

        for text in texts:
            log_from_caller(text)

        for region in regions:
            log_from_caller(region["name"])

        collapsibles = []
        for region, text in zip(regions, texts):
            collapsibles.append(Collapsible(Markdown(text), title = region["name"]))

        log_from_caller("Generated collapsibles:")
        for collapsible in collapsibles:
            log_from_caller(collapsible)

        yield from collapsibles
    
class CountryInput(Input):

    def __init__(self):
        super().__init__()

    def on_mount(self):
        self.selectable_countries = [
            country["name"] for country in self.screen.game.countries.vs()
        ]

        self.valid_empty = False
        self.validators = [
            Function(
                lambda input: input in self.selectable_countries, "Not a valid country."
            )
        ]
        self.validate_on = ["submitted"]

class UnnamedBordersGame(Screen):

    BINDINGS = [
        Binding("ctrl+e", "quit_game", "Main menu", priority = True),
    ]

    def action_quit_game(self):
        self.app.pop_screen()


    class StatusHeader(Header):

        def __init__(self):
            super().__init__()
        
        def compose(self):
            self.started_at = time.monotonic()
            self.update_sub_title()
            yield from super().compose()

        def on_mount(self) -> None:
            self.set_interval(1, self.update_sub_title)

        def update_sub_title(self) -> None:
            elapsed = int(time.monotonic() - self.started_at)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.app.sub_title  = (
                f"Progress: {self.screen.game.done_countries_num}/{self.screen.game.total_countries_num} "
                f"Guesses: {self.screen.game.num_guesses} "
                f"Mistakes: {self.screen.game.mistakes} "
                f"Hints: {sum(self.screen.game.countries.es['hints'])} "
                f"Elapsed: {minutes:02}:{seconds:02}"
        )

    class GameOver(Message):
        def __init__(self, change):
            super().__init__()
            self.change = change

    class GameOverPopup(ModalScreen):
        def compose(self):
            with Grid():
                yield Label("Game over! Well done.")
                yield Button("Main menu", id = "close")

        def on_button_pressed(self, event: Button.Pressed):
            if event.button.id == "close":
                self.app.pop_screen()
                self.app.pop_screen()
        

    class CountryDone(Message):
        def __init__(self, change):
            super().__init__()
            self.change = change

    class CountryStarted(Message):
        def __init__(self, change):
            super().__init__()
            self.change = change

    def __init__(self):
        super().__init__()

        json_resource = files("unnamed_geography_game").joinpath("countries.json")
        with json_resource.open("r") as file:
            data = json.load(file)

        included_names = {"Uzbekistan", "Hong Kong", "Macao"}
        excluded_names = {
            "United Kingdom of Great Britain and Northern Ireland",
            "Ireland",
            "Haiti",
            "Dominican Republic",
            "Sri Lanka"
        }

        # Misc. data fixes
        czech_republic = next(item for item in data if item["name"] == "Czech Republic")
        czech_republic["borders"] = ["DEU", "POL", "AUT", "SVK"]

        singapore = next(item  for item in data if item["name"] == "Singapore")
        singapore["borders"] = ["MYS"]

        revised_data = [
            {**country, "include_in_game": True}
            for country in data
            if country["name"] not in excluded_names
            and "borders" in country
            and (country["name"] in included_names or country["independent"] is True)
        ]
        
        self.game = borders_game(revised_data)
        self.game.subscribe(self.on_game_changed)
        log_from_caller("Seed is:", self.game.countries.vs().find(seed = True)["name"])

    def on_game_changed(self, change):
        log_from_caller(f"Got a {change['kind']}")
        if change["kind"] == "game-over":
            self.post_message(self.GameOver(change))
            return
        if change["kind"] == "new-done":
            self.post_message(self.CountryDone(change))
            completed_tab = self.screen.query_one(CompletedCountryTab)
            log_from_caller(completed_tab)
            completed_tab.refresh(recompose = True)

        if change["kind"] == "new-partial":
            self.post_message(self.CountryStarted(change))

        if change["kind"] == "success":
            guess = change["guess"]
            for card in self.screen.query(CountryCard):
                if card.country in guess["countries"]:
                    card.post_message(StatusUpdate(change))

        if change["kind"] == "failure":
            self.post_message(StatusUpdate(change))            

    async def on_unnamed_borders_game_game_over(self, message):
        self.app.push_screen(self.GameOverPopup())

    async def on_unnamed_borders_game_country_started(self, message):
        new_country_card = CountryCard(message.change["vertex"])
        grid = self.screen.query_one("#in-progress", Grid)
        await grid.mount(new_country_card)

    async def on_unnamed_borders_game_country_done(self, message):
        try:
            done_country_card = self.screen.query_one(f"#{message.change['vertex']['alpha3Code']}", CountryCard)
        except NoMatches:
            log_from_caller("Didn't find a CountryCard, skipping.")
            return

        change_focus = done_country_card.query_one(CountryInput).has_focus

        await done_country_card.remove()
        first_card = self.query_one(CountryCard)

        if change_focus:
            log_from_caller(f"Removed card was focused prior to removal; changing focus")
            first_card.query_one(Input).focus()
            self.screen.query_one("#in-progress-scroll", VerticalScroll).focus()
            self.screen.query_one("#in-progress-scroll", VerticalScroll).scroll_home()

    def make_subtitle(self):
        return (
            f"Progress: {self.game.done_countries_num}/{self.game.total_countries_num} "
            f"Guesses: {self.game.num_guesses} "
            f"Mistakes: {self.game.mistakes} "
            f"Hints: {sum(self.game.countries.es['hints'])}"
        )


    def compose(self):
        yield self.StatusHeader()
        with Middle(), Center(), Vertical():
            with TabbedContent("In progress", "Completed"):
                with VerticalScroll(can_focus = False, id = "in-progress-scroll"), Grid(classes="countrygrid", id="in-progress"):
                    yield CountryCard(
                        self.game.countries.vs().find(seed = True)
                    )
                yield CompletedCountryTab()
                
        yield Footer()

class MainMenu(App):
    CSS_PATH = "app.tcss"
    
    def __init__(self):
        super().__init__()
            
    def compose(self):
        yield Button("Unnamed Borders Game", id = "unnamed-borders-game")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "unnamed-borders-game":
            unnamed_borders_screen = UnnamedBordersGame()
            self.app.push_screen(unnamed_borders_screen)

    def on_mount(self) -> None:
        self.title = "Unnamed geography game"
        self.theme = "solarized-dark"
        
def main():
    app = MainMenu()
    app.run()

if __name__ == "__main__":
    main()
