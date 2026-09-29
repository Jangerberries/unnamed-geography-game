class borders_game:
    def __init__(self, data):
        self.countries = [
            country
            for country in data
            if country["independent"] and "borders" in country
        ]

        self.countries = [
            {
                key: country[key]
                for key in ["name", "flag", "alpha3Code", "borders"]
                if key in country
            }
            for country in self.countries
        ]

        for i, country in enumerate(self.countries):
            borders = self.countries[i]["borders"]
            # translate alpha3 to name
            names = [
                country["name"]
                for border in borders
                for country in self.countries
                if country["alpha3Code"] == border
            ]
            country["borders"] = {name: False for name in names}

        for country in self.countries:
            country["done"] = False
            country["mentioned"] = False

        self.guesses = 0
        self.mistakes = 0
        self.countries_total = len(self.countries)

    def status(self):
        done_countries = [country for country in self.countries if country["done"]]

        in_progress_countries = [
            country
            for country in self.countries
            if not country["done"] and any(country["borders"].values())
        ]

        mentioned_countries = [
            country
            for country in self.countries
            if country["mentioned"] is True and not any(country["borders"].values())
        ]

        return {
            "done": done_countries,
            "done_number": len(done_countries),
            "total_number": len(self.countries),
            "in_progress": in_progress_countries,
            "mentioned": mentioned_countries,
            "guesses": self.guesses,
            "mistakes": self.mistakes,
            "progress": f"{len(done_countries)}/{self.countries_total}",
        }

    def guess_single_country(self, guess):
        country = next(
            (country for country in self.countries if country["name"] == guess), None
        )
        if country is not None:
            if country["done"]:
                return {"country": country}
            if not country["borders"]:
                country["done"] = True
                self.guesses = self.guesses + 1
                return {"country": country}
            else:
                self.guesses = self.guesses + 1
                country["mentioned"] = True
                return {"country": country}
        else:
            self.guesses = self.guesses + 1
            self.mistakes = self.mistakes + 1
            return {"country": country}

    def guess_border(self, a, b):
        country_a = next(
            (country for country in self.countries if country["name"] == a), None
        )
        country_b = next(
            (country for country in self.countries if country["name"] == b), None
        )
        if country_a is None and country_b is None:
            self.guesses += 1
            self.mistakes += 1
            return {"status": self.status(), "last_result": None, "last_guess": [a, b]}
        elif country_a is None:
            self.guesses += 1
            self.mistakes += 1
            if country_b["mentioned"] is not True:
                country_b["mentioned"] = True
                return {
                    "status": self.status(),
                    "last_result": country_b,
                    "last_guess": [a, b],
                }
            else:
                return {
                    "status": self.status(),
                    "last_result": None,
                    "last_guess": [a, b],
                }
        elif country_b is None:
            self.guesses += 1
            self.mistakes += 1
            if country_a["mentioned"] is not True:
                country_a["mentioned"] = True
                return {
                    "status": self.status(),
                    "last_result": country_a,
                    "last_guess": [a, b],
                }
            else:
                return {
                    "status": self.status(),
                    "last_result": None,
                    "last_guess": [a, b],
                }
        else:
            if country_a["mentioned"] is not True:
                country_a["mentioned"] = True
            if country_b["mentioned"] is not True:
                country_b["mentioned"] = True
            # don't add a guess if the border has already been guessed
            if a in [
                border
                for border, completed in country_b["borders"].items()
                if completed is True
            ]:
                return {
                    "status": self.status(),
                    "last_result": [country_a, country_b],
                    "last_guess": [a, b],
                }
            # if the guess is currently unmentioned, add a guess and mark the border as completed
            elif a in [
                border
                for border, completed in country_b["borders"].items()
                if completed is not True
            ]:
                self.guesses += 1
                country_a["borders"][b] = True
                country_b["borders"][a] = True
                if all(country_a["borders"].values()):
                    country_a["done"] = True
                if all(country_b["borders"].values()):
                    country_b["done"] = True
                return {
                    "status": self.status(),
                    "last_result": [country_a, country_b],
                    "last_guess": [a, b],
                }
            else:
                self.guesses += 1
                self.mistakes += 1
                return {
                    "status": self.status(),
                    "last_result": None,
                    "last_guess": [a, b],
                }
