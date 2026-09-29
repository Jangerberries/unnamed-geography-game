{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  packages = with pkgs; [uv ruff ty hatch python314 pre-commit python313];
  strictDeps = true;
  shellHook = ''
    alias ch='ruff check; ruff format; ty check'
    alias gt='uv tool install .; textual run --dev ~/probe/geotui/src/geotui/app.py'
    PATH=~/.local/bin/:$PATH
  '';
  depsBuildBuild = [];
  nativeBuildInputs = [];
}
