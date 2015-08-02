"""Module for dealing with student groups."""
from urllib.parse import urlencode
from xml.etree import ElementTree

import requests

import ocflib.account.search as search


_API = {
    'BASE': 'https://studentservices.berkeley.edu/WebServices/StudentGroupServiceV2/Service.asmx',  # noqa
    'SERVICE': {
        'ORGS': 'CalLinkOrganizations',
        'SIGNATORIES_BY_OID': 'CalLinkGroupSignatories',
        'SIGNAT_ACTIVE': 'SignatoriesActiveStudentGroups',
        'SIGNAT_ALL': 'SignatoriesStudentGroups'
    }
}


# TODO: add method(s) for using CalLinkOrganizations service


# TODO: add option to not resolve accounts for speed
def signatories_for_group(oid):
    """Return list of signatories for a group, including name and OCF account.

    >>> signatories_for_group(46187)
    {646431: {'accounts': ['sanjayk'], 'name': 'Sanjay Krishnan'},
     872544: {'accounts': ['daradib'], 'name': 'Mr. Dara Adib'},
     1029873: {'accounts': ['kpengboy'], 'name': 'KEVIN YANG PENG'},
     1031366: {'accounts': ['mattmcal'], 'name': 'Matthew James McAllister'},
     1031553: {'accounts': ['willh'], 'name': 'WILLIAM HO'},
     1032668: {'accounts': ['nickimp'], 'name': 'NICHOLAS DANIEL IMPICCICHE'},
     1034192: {'accounts': ['ckuehl'], 'name': 'CHRISTOPHER B KUEHL'}}
    """
    def parser(root):
        def parse(student):
            uid = int(student.findtext('Username'))

            attrs = search.user_attrs_ucb(uid)
            name = None

            if attrs:
                name = attrs.get('displayName', [None])[0]

            users = search.users_by_calnet_uid(uid)
            return uid, {'name': name, 'accounts': users}

        xml_members = root.findall('Items/Membership')
        return {uid: details for uid, details in map(parse, xml_members)}

    return _get_osl({'organizationId': oid},
                    _API['SERVICE']['SIGNATORIES_BY_OID'], parser)


# TODO: add option to not resolve accounts for speed
def groups_by_student_signat(uid, service=_API['SERVICE']['SIGNAT_ACTIVE']):
    """Return active groups a student is a signatory for.

    >>> groups_by_student_signat(1034192)
    {46187: {'name': 'Open Computing Facility', accounts: ['decal', 'linux']}}
    """
    def parser(root):
        def parse(group):
            oid = int(group.findtext('groupId'))
            return oid, {
                'name': group.findtext('groupName'),
                'accounts':
                    [] if oid == 0 else search.users_by_callink_oid(oid)}

        xml_groups = root.findall('StudentGroupData/StudentGroupDatum')
        return {oid: name for oid, name in map(parse, xml_groups)}

    return _get_osl({'UID': uid}, service, parser)


def groups_by_student_signat_all(uid):
    """Return all (active and inactive) groups a student is a signatory for."""
    return groups_by_student_signat(uid, service=_API['SERVICE']['SIGNAT_ALL'])


def _get_osl(query, service, parser):
    """Query web service for student group information in XML format.

    You should probably use one of the nicer methods instead."""

    url = '{}/{}?{}'.format(_API['BASE'], service, urlencode(query))

    r = requests.get(url)
    return _parse_osl(ElementTree.fromstring(r.text), parser)


def _parse_osl(root, parser):
    """Assemble Python dictionaries of groups from XML document"""
    if root.findtext('Succeeded') == 'false':
        try:
            error_reason = root.findtext('Reason')
        except:
            error_reason = 'unknown reason'
        raise Exception('Lookup failed: ' + error_reason)

    return parser(root)
