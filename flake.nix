{
  description = "libraries for account and server management";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";
    systems.url = "github:nix-systems/default";
  };

  outputs =
    {
      self,
      nixpkgs,
      systems,
    }:
    let
      pythons = [
        "python38"
        "python39"
        "python310"
        "python311"
        "python312"
        # adding python313 causes an insecure package error on evaluation of the
        # overlay due to:
        # - pypy2.7-setuptools-44.0.0 due to CVE-2025-47273
        # - pypy2.7-pip-20.3.4 due to CVE-2021-2836
        #"python313"
        "python314"
      ];

      packageOverrides = python-final: python-prev: {
        ocflib = python-final.callPackage ./default.nix { };
      };

      overlay = (
        final: prev:
        builtins.listToAttrs (
          map (python: {
            name = python;
            value = prev.${python}.override { inherit packageOverrides; };
          }) pythons
        )
      );

      pkgsFor = system: import nixpkgs { inherit system; };
      forAllSystems = fn: nixpkgs.lib.genAttrs (import systems) (system: fn (pkgsFor system));
    in
    {
      overlays.ocflib = overlay;
      overlays.default = overlay;

      formatter = forAllSystems (pkgs: pkgs.nixfmt-tree);

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            poetry
            python3
            mariadb
            heimdal
          ];
        };
      });
    };
}
