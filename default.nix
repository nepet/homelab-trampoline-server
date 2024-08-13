# file: default.nix
let
  sources = import ./nix/sources.nix;
  pkgs = import sources.nixpkgs { };
  poetry2nix = import sources.poetry2nix { inherit pkgs; };
  homelab_trampoline_server = poetry2nix.mkPoetryApplication { projectDir = ./.; };
in
homelab_trampoline_server