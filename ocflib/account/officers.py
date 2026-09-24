"""Methods for managing officer role history."""
from collections import namedtuple

from ldap3.utils.conv import escape_filter_chars

import ocflib.infra.ldap as ldap
from ocflib.account.utils import dn_for_username
from ocflib.infra.ldap import modify_ldap_entry
from ocflib.infra.ldap import OCF_LDAP_PEOPLE

ROLES = ('gm', 'sm', 'dgm', 'dsm', 'head')

OFFICER_OBJECT_CLASSES = [
    'account', 'posixAccount', 'ocfAccount', 'ocfOfficer'
]

OfficerRole = namedtuple(
    'OfficerRole', ['uid', 'name', 'role', 'term', 'committee']
)


def encode(role, term, committee=None):
    parts = ['role={}'.format(role)]
    if committee:
        parts.append('committee={}'.format(committee))
    parts.append('term={}'.format(term))
    return ';'.join(parts)


def decode(uid, name, raw):
    fields = dict(part.split('=', 1) for part in raw.split(';'))
    return OfficerRole(
        uid=uid,
        name=name,
        role=fields['role'],
        term=fields['term'],
        committee=fields.get('committee'),
    )


def officer_roles(uid):
    """Returns a list of OfficerRoles held by uid, oldest first.

    Returns an empty list if uid has never been an officer.
    """
    with ldap.ldap_ocf() as c:
        c.search(
            OCF_LDAP_PEOPLE,
            '(uid={})'.format(escape_filter_chars(uid)),
            attributes=('cn', 'ocfOfficerRole'),
        )
        if not c.response:
            return []
        attrs = c.response[0]['attributes']
        name, = attrs['cn']
        return [
            decode(uid, name, raw)
            for raw in attrs.get('ocfOfficerRole', [])
        ]


def all_officer_roles():
    """Returns a list of every OfficerRole ever recorded, across all users.

    Used to render the full officer history. Not cheap, so callers should
    cache the result.
    """
    with ldap.ldap_ocf() as c:
        c.search(
            OCF_LDAP_PEOPLE,
            '(objectClass=ocfOfficer)',
            attributes=('uid', 'cn', 'ocfOfficerRole'),
        )
        return [
            decode(
                entry['attributes']['uid'][0],
                entry['attributes']['cn'][0],
                raw
            )
            for entry in c.response
            for raw in entry['attributes'].get('ocfOfficerRole', [])
        ]


def is_officer(uid):
    """Returns whether uid has ever held an officer role."""
    return bool(officer_roles(uid))


def add_officer_role(uid, role, term, committee=None, **kwargs):
    """Records a new officer role for uid while preserving their rest.

    :param uid: username to grant the role to
    :param role: one of ROLES
    :param term: e.g. 'Fall 2026'
    :param committee: name of the committee headed, if role is 'head'
    :param **kwargs: passed on to modify_ldap_entry
    """
    if role not in ROLES:
        raise ValueError('role must be one of {}'.format(ROLES))
    if role == 'head' and not committee:
        raise ValueError('committee is required when role is head')

    existing = [
        encode(r.role, r.term, r.committee)
        for r in officer_roles(uid)
    ]
    new_role = encode(role, term, committee)
    if new_role in existing:
        raise ValueError('{} already has this role for {}'.format(uid, term))

    modify_ldap_entry(
        dn_for_username(uid),
        {
            'objectClass': OFFICER_OBJECT_CLASSES,
            'ocfOfficerRole': existing + [new_role],
        },
        **kwargs
    )


def remove_officer_role(uid, role, term, committee=None, **kwargs):
    """Removes a previously recorded officer role from uid.

    :param uid: username to remove the role from
    :param role: one of ROLES
    :param term: e.g. 'Fall 2026'
    :param committee: name of the officer role, if role is 'head'
    :param **kwargs: passed on to modify_ldap_entry
    """
    existing = [
        encode(r.role, r.term, r.committee)
        for r in officer_roles(uid)
    ]
    target = encode(role, term, committee)
    if target not in existing:
        raise ValueError('{} does not have this role for {}'.format(uid, term))

    existing.remove(target)
    modify_ldap_entry(
        dn_for_username(uid),
        {'ocfOfficerRole': existing},
        **kwargs
    )
