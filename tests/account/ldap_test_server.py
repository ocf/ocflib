import tempfile
import shutil
import os
from contextlib import contextmanager
from ldap3 import Server, Connection, ALL, MOCK_SYNC
from ldap3.core.exceptions import LDAPException


class LDAPTestServer:
    """A real LDAP test server with predefined test data."""
    
    def __init__(self):
        self.server = None
        self.connection = None
        self.base_dn = 'dc=OCF,dc=Berkeley,dc=EDU'
        self.people_dn = 'ou=People,dc=OCF,dc=Berkeley,dc=EDU'
        
    def start(self):
        """Start the mock LDAP server and populate with test data."""
        # Create mock server
        self.server = Server('mock_server', get_info=ALL)
        self.connection = Connection(self.server, client_strategy=MOCK_SYNC)
        self.connection.open()
        
        # Create base structure
        self._create_base_structure()
        
        # Populate with test data
        self._populate_test_data()
        
    def stop(self):
        """Stop the LDAP server."""
        if self.connection:
            self.connection.unbind()
            
    @contextmanager
    def ldap_connection(self):
        """Context manager that yields LDAP connection."""
        try:
            yield self.connection
        finally:
            pass
            
    def _create_base_structure(self):
        """Create the base LDAP structure."""
        # Create base DN
        self.connection.add(
            self.base_dn,
            ['dcObject', 'organization'],
            {'dc': 'OCF', 'o': 'Open Computing Facility'}
        )
        
        # Create People OU
        self.connection.add(
            self.people_dn,
            ['organizationalUnit'],
            {'ou': 'People'}
        )
        
    def _populate_test_data(self):
        """Populate LDAP with test user data."""
        # Test users for UID number tests
        test_users = [
            {
                'dn': 'uid=testuser1,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                'attributes': {
                    'uid': 'testuser1',
                    'cn': 'Test User 1',
                    'uidNumber': 999000,
                    'gidNumber': 1000,
                    'homeDirectory': '/home/t/te/testuser1',
                    'loginShell': '/bin/bash',
                    'objectClass': ['ocfAccount', 'account', 'posixAccount']
                }
            },
            {
                'dn': 'uid=testuser2,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                'attributes': {
                    'uid': 'testuser2',
                    'cn': 'Test User 2', 
                    'uidNumber': 999100,
                    'gidNumber': 1000,
                    'homeDirectory': '/home/t/te/testuser2',
                    'loginShell': '/bin/bash',
                    'objectClass': ['ocfAccount', 'account', 'posixAccount']
                }
            },
            {
                'dn': 'uid=testuser3,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                'attributes': {
                    'uid': 'testuser3',
                    'cn': 'Test User 3',
                    'uidNumber': 999200,
                    'gidNumber': 1000,
                    'homeDirectory': '/home/t/te/testuser3',
                    'loginShell': '/bin/bash',
                    'objectClass': ['ocfAccount', 'account', 'posixAccount']
                }
            },
            {
                'dn': 'uid=reservedtest,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                'attributes': {
                    'uid': 'reservedtest',
                    'cn': 'Reserved Test User',
                    'uidNumber': 61183,
                    'gidNumber': 1000,
                    'homeDirectory': '/home/r/re/reservedtest',
                    'loginShell': '/bin/bash',
                    'objectClass': ['ocfAccount', 'account', 'posixAccount']
                }
            },
            {
                'dn': 'uid=reservedtest2,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                'attributes': {
                    'uid': 'reservedtest2',
                    'cn': 'Reserved Test User 2',
                    'uidNumber': 60000,
                    'gidNumber': 1000,
                    'homeDirectory': '/home/r/re/reservedtest2',
                    'loginShell': '/bin/bash',
                    'objectClass': ['ocfAccount', 'account', 'posixAccount']
                }
            },
            # Existing users for username validation
            {
                'dn': 'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                'attributes': {
                    'uid': 'ckuehl',
                    'cn': 'Chris Kuehl',
                    'uidNumber': 1001,
                    'gidNumber': 1000,
                    'homeDirectory': '/home/c/ck/ckuehl',
                    'loginShell': '/bin/bash',
                    'objectClass': ['ocfAccount', 'account', 'posixAccount']
                }
            }
        ]
        
        # Add many users for _KNOWN_UID test
        for i in range(1000):
            uid_num = 70000 + i  # Start from 70000 to simulate realistic UIDs
            username = f'bulkuser{i:04d}'
            test_users.append({
                'dn': f'uid={username},ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                'attributes': {
                    'uid': username,
                    'cn': f'Bulk User {i}',
                    'uidNumber': uid_num,
                    'gidNumber': 1000,
                    'homeDirectory': f'/home/b/bu/{username}',
                    'loginShell': '/bin/bash',
                    'objectClass': ['ocfAccount', 'account', 'posixAccount']
                }
            })
        
        # Add all test users
        for user in test_users:
            try:
                self.connection.add(
                    user['dn'],
                    user['attributes']['objectClass'],
                    user['attributes']
                )
            except LDAPException as e:
                print(f"Failed to add user {user['dn']}: {e}")
                
    def reset_data(self):
        """Reset and repopulate test data."""
        # Delete all entries under People
        self.connection.delete(self.people_dn, controls=[('1.2.840.113556.1.4.805', True, None)])
        
        # Recreate structure and data
        self._create_base_structure()
        self._populate_test_data()
        
    def add_test_user(self, username, uid_number, **kwargs):
        """Add a specific test user."""
        dn = f'uid={username},ou=People,dc=OCF,dc=Berkeley,dc=EDU'
        attributes = {
            'uid': username,
            'cn': kwargs.get('cn', f'Test User {username}'),
            'uidNumber': uid_number,
            'gidNumber': kwargs.get('gidNumber', 1000),
            'homeDirectory': kwargs.get('homeDirectory', f'/home/{username[0]}/{username[:2]}/{username}'),
            'loginShell': kwargs.get('loginShell', '/bin/bash'),
            'objectClass': kwargs.get('objectClass', ['ocfAccount', 'account', 'posixAccount'])
        }
        
        # Add any additional attributes
        for key, value in kwargs.items():
            if key not in attributes:
                attributes[key] = value
                
        self.connection.add(dn, attributes['objectClass'], attributes)


# Global test server instance
ldap_test_server = LDAPTestServer()
