"""Methods specific to Kerberos functionality. High-level methods like checking
and changing passwords should go elsewhere."""

import socket

# TODO: settings location

def _kadmin_command(user_account):
    user_account = clean_user_account(user_account)
    return "%(kadmin_location)s -K %(kerberos_keytab)s -p %(kerberos_principal)s cpw %(user_account)s" % {
            "kadmin_location": settings.KADMIN_LOCATION,
            "kerberos_keytab": settings.KRB_KEYTAB,
            "kerberos_principal": "chpass/" + socket.getfqdn(),
            "user_account": user_account
        }
