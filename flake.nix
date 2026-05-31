{
  description = "libraries for account and server management";

  outputs = { self }:
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
