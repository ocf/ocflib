{ lib
, buildPythonPackage
, fetchPypi
, fetchpatch
, pythonOlder

# build system
, poetry-core

# system dependencies

# python dependencies
, attrs
, dnspython
, jinja2
, pexpect
, pycryptodome
, pygithub
, pymysql
, pyyaml
, redis
, requests
, sqlalchemy_1_4
, dos2unix
, pyasn1
, zxcvbn
}:

let
  pysnmp-pypi = buildPythonPackage rec {
    pname = "pysnmp";
    version = "4.4.12";
    format = "setuptools";
    src = fetchPypi {
      inherit pname version;
      hash = "sha256-DD2+8vlYysqWBx/lwZ3kPpwbBISrAqDPCLGQvO52i6k=";
    };
    # https://github.com/NixOS/nixpkgs/blob/689fed12a013f56d4c4d3f612489634267d86529/pkgs/development/python-modules/pysnmp/default.nix#L20C3-L20C67
    patches = [ ./patches/setup.py-Fix-the-setuptools-version-check.patch ];
    doCheck = false;
  };
  cached-property-pypi = buildPythonPackage rec {
    pname = "cached-property";
    version = "1.5.2";
    format = "setuptools";
    src = fetchPypi {
      inherit pname version;
      hash = "sha256-n6V1WDjuy7LSNMOqOQvYD706xraGkQm/wbSZ972JoTA=";
    };
    doCheck = false;
  };
  ldap3 = buildPythonPackage rec {
  pname = "ldap3";
  version = "2.9.1";
  format = "setuptools";
  src = fetchPypi {
    inherit pname version;
    sha256 = "f3e7fc4718e3f09dda568b57100095e0ce58633bcabbed8667ce3f8fbaa4229f";
  };
  prePatch = ''
    # patch fails to apply because of line endings
    dos2unix ldap3/utils/asn1.py
  '';
  patches = [
    # fix pyasn1 0.5.0 compatibility
    # https://github.com/cannatag/ldap3/pull/983
    (fetchpatch {
      url = "https://github.com/cannatag/ldap3/commit/ca689f4893b944806f90e9d3be2a746ee3c502e4.patch";
      hash = "sha256-A8qI0t1OV3bkKaSdhVWHFBC9MoSkWynqxpgznV+5gh8=";
    })
  ];
  nativeBuildInputs = [ dos2unix ];
  propagatedBuildInputs = [ pyasn1 ];
  doCheck = false; # requires network
};
in

buildPythonPackage {
  pname = "ocflib";
  version = "2025-08-28";
  format = "pyproject";
  disabled = pythonOlder "3.7";
  src = ./.;

  buildInputs = [
  ];

  propagatedBuildInputs = [
    attrs
    cached-property-pypi
    dnspython
    jinja2
    ldap3
    pexpect
    pycryptodome
    pygithub
    pymysql
    pysnmp-pypi
    pyyaml
    redis
    requests
    sqlalchemy_1_4
    poetry-core
    zxcvbn
  ];

  meta = with lib; {
    description = "libraries for account and server management";
    homepage = "https://github.com/ocf/ocflib";
    license = [ licenses.mit licenses.gpl2Plus ];
    platforms = platforms.unix;
  };
}
