{ lib
, buildPythonPackage
, fetchPypi
, fetchpatch
, pythonOlder

# build system
, poetry-core
, setuptools

# system dependencies

# python dependencies
, attrs
, dnspython
, jinja2
, ldap3
, passlib
, pexpect
, pycryptodome
, pygithub
, pymysql
, pyyaml
, redis
, requests
, sqlalchemy
, x690
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
  puresnmp-pypi = buildPythonPackage rec {
    pname = "puresnmp";
    version = "2.0.1";
    format = "pyproject";
    src = fetchPypi {
      inherit pname version;
      sha256 = "08a147249a6ff92d3f463b77e21b9221ca7a836ff7401e0b8dfe47135ed4cf56";
    };
    nativeBuildInputs = [ setuptools ];
    propagatedBuildInputs = [ x690 ];
    doCheck = false;
  };
in

buildPythonPackage {
  pname = "ocflib";
  version = "2026-06-09";
  format = "pyproject";
  disabled = pythonOlder "3.7";
  src = ./.;

  buildInputs = [
  ];

  propagatedBuildInputs = [
    attrs
    dnspython
    jinja2
    ldap3
    passlib
    pexpect
    pycryptodome
    pygithub
    pymysql
    puresnmp-pypi
    pyyaml
    redis
    requests
    sqlalchemy
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
