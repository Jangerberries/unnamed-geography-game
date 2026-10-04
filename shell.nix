{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  packages = with pkgs; [uv ruff ty hatch python314 pre-commit python313];
  strictDeps = true;
  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
  ];
  shellHook = ''
    alias ch='ruff check; ruff format; ty check'
    alias gt='uv tool install .; textual run --dev ~/probe/unnamed-geography-game/src/geotui/app.py'
    alias tc='textual console -x SYSTEM -x EVENT -x WORKER'
    alias rp='python -i foo.py'
    PATH=~/.local/bin/:$PATH
    source .venv/bin/activate
  '';
  depsBuildBuild = [];
  nativeBuildInputs = [];
}
