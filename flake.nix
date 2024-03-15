{
  description = "libraries for account and server management";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self }:
    let
      pythons = [ "python37" "python38" "python39" "python310" "python311" ];

      packageOverrides = python-final: python-prev: {
        ocflib = python-final.callPackage ./default.nix { };
      };

      overlay = (final: prev:
        builtins.listToAttrs (map
          (python: {
            name = python;
            value = prev.${python}.override { inherit packageOverrides; };
          })
          pythons)
      );
    in
    {
      overlays.ocflib = overlay;
      overlays.default = overlay;
    };
}
