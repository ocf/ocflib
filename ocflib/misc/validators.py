"""Misc validators for things like emails, domains, etc."""

def email_host(email_addr):
    """Returns the host in the email address argument"""
    if "@" in email_addr:
        return email_addr.rsplit("@", 1).pop()
    return None


def host_exists(host):
    try:
        host_info = getaddrinfo(host, None)
    except gaierror:
        return False
    else:
        return host_info


def validate_email_host_exists(email_addr):
    """Verifies that the host of the email address exists"""
    host = email_host(email_addr)
    if not host_exists(host):
        raise ValidationError("E-mail address host does not exist.")

def check_email(email):
    """Check the email with naive regex and check for the domain's MX record.
    Returns True for valid email, False for bad email."""
    regex = r'^[a-zA-Z0-9._%\-+]+@([a-zA-Z0-9._%\-]+.[a-zA-Z]{2,6})$'

    m = match(regex, email)
    if m:
        domain = m.group(1)
        try:
            # Check that the domain has MX record(s)
            answer = resolver.query(domain, 'MX')
            if answer:
                return True
        except (resolver.NoAnswer, resolver.NXDOMAIN):
            pass
    return False
