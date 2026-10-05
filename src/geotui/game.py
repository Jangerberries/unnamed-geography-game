import random
import igraph


class CountryGraph(igraph.Graph):
    def __init__(self, data):
        super().__init__(directed=False)
        self.add_vertices(len(data))
        for vertex, country in zip(self.vs, data):
            for key, value in country.items():
                vertex[key] = value

        edges = []

        for country in [item for item in data if "borders" in item]:
            country_vertex = self.vs.find(name=country["name"])

            for bordering_country in country["borders"]:
                matches = self.vs.select(alpha3Code=bordering_country)

                if not matches:
                    continue

                bordering_vertex = matches[0]
                
                edges.append({country_vertex.index, bordering_vertex.index})

        edges = {tuple(sorted(edge)) for edge in edges}

        self.add_edges(list(edges))

        for edge in self.es:
            edge["guessed"] = False
            edge["hints"] = 0

        for vertex in self.vs:
            vertex["seed"] = False

        self.seed_country = self.vs[random.randrange(self.vcount())]
        self.seed_country["seed"] = True
            
        self.guesses = 0

    @property
    def partially_guessed_countries(self):
        def matches(v):
            guessed = [
                self.es[eid]["guessed"]
                for eid in self.incident(v.index, mode="ALL")
            ]

            some_guessed = any(guessed)
            all_guessed = all(guessed)
            
            return not all_guessed and (some_guessed or v["seed"])

        return self.vs.select(matches)

    @property
    def completely_guessed_countries(self):
        return self.vs.select(
            lambda v: all(
                self.es[eid]["guessed"] == True
                for eid in self.incident(v.index, mode="ALL")
            )
        )

    def guess_border(self, country_a, country_b):
        self.guesses += 1
        vertex_a = self.vs.select(name=country_a)
        vertex_b = self.vs.select(name=country_b)

        if len(vertex_a) == 1 and len(vertex_b) == 1:
            are_neighbors = self.are_adjacent(vertex_a[0], vertex_b[0])            

            if are_neighbors:
                edge = self.es[self.get_eid(vertex_a[0].index, vertex_b[0].index)]
                edge["guessed"] = True
                edge["order_guessed"] = self.guesses
                return True

            else:
                return False

    def guessed_borders(self, country):
        edges = self.es.select(_incident=[country.index], guessed=True)

        edges = sorted(
            edges,
            key=lambda edge: edge["order_guessed"]
        )

        neighbors = self.vs[
            [
                edge.target if edge.source == country.index else edge.source
                for edge in edges
            ]
        ]

        return neighbors


class borders_game:
    def __init__(self, data):
        self.countries = CountryGraph(data)
        self.countries.delete_vertices(
            [v.index for v in self.countries.vs(_degree_eq=0)]
        )
        self.mistakes = 0

        self._listeners = []

    @property
    def guesses(self):
        return self.countries.guesses

    @property
    def total_countries_num(self):
        return len(self.countries.vs.select(independent=True, _degree_gt=0))

    @property
    def done_countries_num(self):
        return len(self.countries.completely_guessed_countries)

    def subscribe(self, listener: Callable):
        self._listeners.append(listener)

    async def _notify(self, change):
        for listener in self._listeners:
            listener(change)

    async def guess_border(self, a, b):
        done_before = self.countries.completely_guessed_countries.indices
        partial_before = self.countries.partially_guessed_countries.indices

        result = self.countries.guess_border(a, b)

        if result is True:
            done_after = self.countries.completely_guessed_countries.indices
            partial_after = self.countries.partially_guessed_countries.indices
            new_done = self.countries.vs(
                set(done_after) - set(done_before)
            )

            if len(new_done) == 1:
                await self._notify({"kind": "new-done", "vertex": new_done[0]})

            if len(new_done) == 2:
                await self._notify({"kind": "new-done", "vertex": new_done[0]})
                await self._notify({"kind": "new-done", "vertex": new_done[1]})
                
            new_partial = self.countries.vs(
                set(partial_after) - set(partial_before)
            )

            if len(new_partial) == 1:
                await self._notify({"kind": "new-partial", "vertex": new_partial[0]})

            if len(new_partial) == 2:
                await self._notify({"kind": "new-partial", "vertex": new_partial[0]})
                await self._notify({"kind": "new-partial", "vertex": new_partial[1]})

            await self._notify({"kind": "success"})

        elif result is False:
            self.mistakes += 1
            await self._notify({"kind": "failure"})

        return result
