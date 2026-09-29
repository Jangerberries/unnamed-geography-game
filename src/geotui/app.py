import json

from textual.app import App
from textual.screen import Screen
from textual.validation import Function
from textual.suggester import SuggestFromList
from textual.widgets import Header, Footer, Input, Label, Collapsible
from textual.containers import (
    Center,
    Middle,
    Vertical,
    Horizontal,
    Grid,
    VerticalScroll,
)
from typing import ClassVar

from importlib.resources import files

from geotui.game import borders_game


class CountryCard(Collapsible):
    def __init__(self, country):
        self.country = country
        self.done_borders = [
            border
            for border, completed in country["borders"].items()
            if completed is True
        ]
        self.missing_borders = [
            "..."
            for border, completed in country["borders"].items()
            if completed is not True
        ]
        labels = [Label(f"✅ {border}") for border in self.done_borders]
        super().__init__(*labels, collapsed=True, title=self.make_title())

    def make_title(self):
        return f"{self.country['flag']} {self.country['name']} ({len(self.done_borders)}/{len(self.country['borders'])})"


class CountryGrid(Grid):
    def __init__(self):
        super().__init__()

    def compose(self):
        self.countries = [
            CountryCard(country) for country in self.app.game.status()["in_progress"]
        ]
        yield from self.countries


class CountryInput(Input):
    def __init__(self):
        selectable_countries = [country["name"] for country in self.app.game.countries]
        super().__init__()
        self.valid_empty = False
        self.suggester = SuggestFromList(selectable_countries, case_sensitive=False)
        self.validators = [
            Function(
                lambda input: input in selectable_countries, "Not a valid country."
            )
        ]
        self.validate_on = ["submitted"]


class MainScreen(Screen):
    def __init__(self):
        super().__init__()

    def on_mount(self):
        self.sub_title = self.make_status()

    def compose(self):
        yield Header()
        with Middle(), Center(), Vertical():
            with VerticalScroll():
                yield CountryGrid()
            yield Horizontal(CountryInput(), CountryInput())
        yield Footer()

    def make_status(self):
        status = self.app.game.status()
        return f"""{status["done_number"]}/{status["total_number"]} done, {status["guesses"]} guesses, {status["mistakes"]} mistakes"""

    def on_input_submitted(self, event: CountryInput.Submitted) -> None:
        inputs = self.query(CountryInput)
        first = inputs.first()
        second = inputs.last()

        if first.is_valid and second.is_valid:
            self.app.game.guess_border(first.value, second.value)
            self.sub_title = self.make_status()
            self.query_one(CountryGrid).refresh(recompose=True)

        return


class geotui(App):
    CSS_PATH = "app.tcss"
    SCREENS: ClassVar = {"main-menu": MainScreen}

    def __init__(self):
        super().__init__()

        json_resource = files("geotui").joinpath("countries.json")
        with json_resource.open("r") as file:
            data = json.load(file)
        self.game = borders_game(data)

    def on_mount(self) -> None:
        self.title = "Unnamed geography game"
        self.theme = "atom-one-dark"
        self.push_screen("main-menu")


def main():
    app = geotui()
    app.run()


if __name__ == "__main__":
    main()
