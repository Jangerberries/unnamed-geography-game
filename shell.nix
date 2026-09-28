{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  packages = with pkgs; [uv ruff ty hatch python314];
  strictDeps = true;
  depsBuildBuild = [];
  nativeBuildInputs = [];
}
