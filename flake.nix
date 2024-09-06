{
  description = "libraries for account and server management";

  outputs = { self }:
    let
      pythons = [ "python37" "python38" "python39" "python310" "python311" "python312" ];

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
