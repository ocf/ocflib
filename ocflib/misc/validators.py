"""Misc validators for things like emails, domains, etc."""
import re
import socket

import dns.resolver


def host_exists(host):
    try:
        host_info = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    else:
        return bool(host_info)


def email_host_exists(email_addr):
    """Verifies that the host of the email address exists"""
    if '@' in email_addr:
        host = email_addr.rsplit('@', 1).pop()
        return host_exists(host)
    return False


def valid_email(email):
    """Check the email with naive regex and check for the domain's MX record.
    Returns True for valid email, False for bad email."""
    regex = r'^[a-zA-Z0-9._%\-+]+@([a-zA-Z0-9._%\-]+.[a-zA-Z]{2,6})$'

    m = re.match(regex, email)
    if m:
        domain = m.group(1)
        try:
            # Check that the domain has MX record(s)
            return bool(dns.resolver.query(domain, 'MX'))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
    return False
