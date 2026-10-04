import json

from datetime import datetime
import time        

from textual.app import App
from textual.screen import Screen
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
)
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
from geotui.game import borders_game

from textual.suggester import Suggester

class StatusUpdate(Message):
    def __init__(self, change):
        super().__init__()


class CountryCard(Vertical):

    BINDINGS = [
        Binding("ctrl+h", "get_hint", "Get a hint", priority = True)
    ]
    
    def on_status_update(self):
        self.log("CountryCard: on_status_update is updating the title")
        self.country = self.app.game.countries.vs.find(name=self.country["name"])
        self.guessed_neighbors = self.app.game.countries.guessed_borders(self.country)
        self.all_neighbors = self.country.neighbors()
        label = self.query_one(Markdown)
        label.update(self.make_title())

    def __init__(self, country):
        super().__init__(id = country["alpha3Code"])
        self.country = country
        self.guessed_neighbors = self.app.game.countries.guessed_borders(self.country)
        self.all_neighbors = self.country.neighbors()
        self.title = self.make_title()

    def action_get_hint(self):
        for neighbor in self.all_neighbors:
            border = self.app.game.countries.es.find(
                self.app.game.countries.get_eid(
                    self.country["name"], neighbor["name"]
                )
            )
            if border["guessed"]:
                continue
            self.app.log(f"action_get_hint: checking {neighbor['name']}:")
            self.app.log(f"action_get_hint: hints: {border['hints']}")
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
        
        border = self.app.game.countries.es.find(
            self.app.game.countries.get_eid(
                self.country["name"], neighbor["name"]
            )
        )
        self.app.log(f"label_neighbor: making label for {neighbor['name']}")
        self.app.log(f"label_neighbor: guessed is {border['guessed']}")
        self.app.log(f"label_neighbor: hints is {border['hints']}")
        
        if border["guessed"]:
            return f"{neighbor['flag']} {neighbor['name']}"
        elif border["hints"] == 0:
            return f"🇺🇳 ..."
        elif border["hints"] == 1:
            hinted = f"🇺🇳 " + ''.join(' ' if char == ' ' else '-' for char in neighbor["name"])
            self.app.log(f"Hinted is {hinted}")
            return hinted
        elif border["hints"] == 2:

            hinted = f"🇺🇳 " + neighbor["name"][0] + ''.join(' ' if char == ' ' else '-' for char in neighbor["name"][1:])
            self.app.log(f"Hinted is {hinted}")            
            return hinted
        elif border["hints"] == 3:
            hinted =  (
                f"🇺🇳 " +
                neighbor["name"][:1] +
                ''.join(' ' if char == ' ' else '-' for char in neighbor["name"][1:-1]) +
                 neighbor["name"][-1:]
            )
            self.app.log(f"Hinted is {hinted}")
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
        yield Markdown(self.title)
        country_input = CountryInput()
        yield country_input
        yield AutoComplete(
            country_input,
            candidates = country_input.selectable_countries
        )

    async def on_input_submitted(self, event: CountryInput.Submitted):
        input = self.query_children(CountryInput).first()

        if input.is_valid:
            self.app.log(f"CountryCard: on_input_submitted: Input was {input.value}")
            await self.app.game.guess_border(self.country["name"], input.value)
            self.app.log(f"CountryCard: in_input_submitted: Clearing the input.")
            input.clear()


class CountryInput(Input):
    def __init__(self):
        self.selectable_countries = [
            country["name"] for country in self.app.game.countries.vs()
        ]

        super().__init__()
        self.valid_empty = False
        self.validators = [
            Function(
                lambda input: input in self.selectable_countries, "Not a valid country."
            )
        ]
        self.validate_on = ["submitted"]


        

class UnnamedGame(App):
    CSS_PATH = "app.tcss"

    class StatusHeader(Header):

        def __init__(self):
            super().__init__()
            self.started_at = time.monotonic()            
            self.update_sub_title()
        
        def compose(self):
            self.started_at = time.monotonic()
            yield from super().compose()

        def on_mount(self) -> None:
            self.set_interval(1, self.update_sub_title)

        def update_sub_title(self) -> None:
            elapsed = int(time.monotonic() - self.started_at)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.app.sub_title  = (
                f"Progress: {self.app.game.done_countries_num}/{self.app.game.total_countries_num} "
                f"Guesses: {self.app.game.guesses} "
                f"Mistakes: {self.app.game.mistakes} "
                f"Hints: {sum(self.app.game.countries.es['hints'])} "
                f"Elapsed: {minutes:02}:{seconds:02}"
        )

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

        json_resource = files("geotui").joinpath("countries.json")
        with json_resource.open("r") as file:
            data = json.load(file)

        data = [item for item in data if item["independent"] is True]
        self.game = borders_game(data)
        self.game.subscribe(self._on_game_changed)

    def _on_game_changed(self, change):
        self.app.log(f"UnnamedGame: _on_game_changed: got a {change['kind']}")
        if change["kind"] == "new-done":
            self.app.log("UnnamedGame: _on_game_changed: dispatching to self.CountryDone")
            self.post_message(self.CountryDone(change))
        if change["kind"] == "new-partial":
            self.app.log("UnnamedGame: _on_game_changed: dispatching to self.CountryStarted")
            self.post_message(self.CountryStarted(change))

        if change["kind"] in ["success", "failure"]:
            for card in self.app.query(CountryCard):
                self.app.log("UnnamedGame: _on_game_changed: dispatching to StatusUpdate")
                card.post_message(StatusUpdate(change))
            self.post_message(StatusUpdate(change))
            
    async def on_unnamed_game_country_started(self, message):
        new_country_card = CountryCard(message.change["vertex"])
        grid = self.app.query_one("#in_progress", Grid)
        self.app.log("UnnamedGame: on_unnamed_game_country-started: mounting a new CountryCard")
        await grid.mount(new_country_card)
        self.app.log("UnnamedGame: on_unnamed_game_country-started: CountryCard finished mounting")

    async def on_unnamed_game_country_done(self, message):
        try:
            done_country_card = self.app.query_one(f"#{message.change['vertex']['alpha3Code']}", CountryCard)
        except NoMatches:
            self.app.log("UnnamedGame: on_unnamed_country_done: didn't find a CountryCard, skipping")
            return

        change_focus = done_country_card.query_one(CountryInput).has_focus
        self.app.log(f"UnnamedGame: on_unnamed_game_country_done: change_focus is {change_focus}")
        self.app.log("UnnamedGame: on_unnamed_game_country_done: removing a CountryCard")
        await done_country_card.remove()
        self.app.log("UnnamedGame: on_unnamed_game_country_done: removed CountryCard")
        first_card = self.query_one(CountryCard)

        if change_focus:
            self.app.log("UnnamedGame: on_unnamed_game_country_done: removed widget was focused")
            self.app.log("UnnamedGame: on_unnamed_game_country_done: focusing a new input")
            first_card.query_one(Input).focus()
        else:

            self.app.log("UnnamedGame: on_unnamed_game_country_done: not changing focus")

    def make_subtitle(self):
        return (
            f"Progress: {self.app.game.done_countries_num}/{self.app.game.total_countries_num} "
            f"Guesses: {self.app.game.guesses} "
            f"Mistakes: {self.app.game.mistakes} "
            f"Hints: {sum(self.app.game.countries.es['hints'])}"
        )

    def on_mount(self) -> None:
        self.title = "Unnamed geography game"
        self.theme = "solarized-dark"

    def compose(self):
        yield self.StatusHeader()
        with Middle(), Center(), Vertical():
            with TabbedContent("In progress", "Completed"):
                with VerticalScroll(can_focus = False), Grid(classes="countrygrid", id="in_progress"):
                    country_cards = [
                        CountryCard(country)
                        for country in self.app.game.countries.partially_guessed_countries
                    ]
                    yield from country_cards
                with VerticalScroll():
                    yield Grid(classes="countrygrid", id="completed")

        yield Footer()

def main():
    app = UnnamedGame()
    app.run()

if __name__ == "__main__":
    main()
