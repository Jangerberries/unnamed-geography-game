# Unnamed geography game

## What is this?

A simple terminal game about listing every land border you can think
of.

## How do I install it?

```console
uv tool install https://github.com/Jangerberries/unnamed-geography-game.git
```

To install from a specific branch, i.e. `dev`:

```console
uv tool install https://github.com/Jangerberries/unnamed-geography-game@dev
```
## How do I use it?

After installation:

```console
unnamed-geography-game
```

Some shortcuts (may or may not work on your system):

- <kbd>Ctrl</kbd>+<kbd>p</kbd> to bring up the command palette.
- <kbd>Ctrl</kbd>+<kbd>h</kbd> to get a hint about a current country
- <kbd>Ctrl</kbd>+<kbd>q</kbd> quit the game

## What counts as a border?

Every country on [the Wikipedia list of countries and territories by
number of land
borders](https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_number_of_land_borders)
with a border is included as of October 6th 2026. The names used in
the game may differ from the ones used in the list, with the following
caveats:

- The following countries that have land borders are nevertheless not
  included for convenience: United Kingdom, Ireland, Dominican
  Republic, Haiti.
- France shares a border with Suriname and Brazil through its
  overseas department French Guiana.
- France does not share a border with the Netherlands through its
  Collectivity of Saint Martin and the dutch Sint Maarten.
- Denmark does not share a border with Canada through the autonomous
  territory of Greenland.
- South Ossetia is not included.

The borders listed in the article have not been compared with those
used in this app in detail. If you notice a discrepancy, please let me
know.

## Where does the data come from?

GeoNames (CC BY 4.0), distributed by
[countries.dev](https://countries.dev/). Last collected on September
28th 2026.

## What's wrong?

- The game will occasionally crash on start with a ValueError: no such vertex
- The game crashes when no more countries are on screen

## What's left?

See TODO. 


