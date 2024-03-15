{ lib
, buildPythonPackage
, fetchPypi
, pythonOlder

# build system
, poetry-core

# system dependencies
, cracklib

# python dependencies
, attrs
, cached-property
, dnspython
, jinja2
, ldap3
, pexpect
, pycryptodome
, pygithub
, pymysql
, pysnmp
, pyyaml
, redis
, requests
, sqlalchemy_1_4
}:

let
  cracklib-pypi = buildPythonPackage rec {
    pname = "cracklib";
    version = "2.9.6";
    src = fetchPypi {
      inherit pname version;
      hash = "sha256-o/S6jNIOrppRbridviJJghx3EIsERyMFW0W/eTYVABI=";
    };
    propagatedBuildInputs = [ cracklib ];
  };
in

buildPythonPackage {
  pname = "ocflib";
  version = "2024-03-14";
  format = "pyproject";
  disabled = pythonOlder "3.7";
  src = ./.;

  buildInputs = [
    cracklib # cracklib system library
  ];

  propagatedBuildInputs = [
    attrs
    cached-property
    cracklib-pypi # cracklib python package
    dnspython
    jinja2
    ldap3
    pexpect
    pycryptodome
    pygithub
    pymysql
    pysnmp
    pyyaml
    redis
    requests
    sqlalchemy_1_4
    poetry-core
  ];

  meta = with lib; {
    description = "libraries for account and server management";
    homepage = "https://github.com/ocf/ocflib";
    license = [ licenses.mit licenses.gpl2Plus ];
    platforms = platforms.unix;
  };
}
