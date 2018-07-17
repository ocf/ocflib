"""Google Admin Directory API for some mailing lists"""
import googleapiclient.discovery
from google.oauth2 import service_account


class GAppsAdmin:
    def __init__(self, service_account_file_path):
        scopes = [
            'https://www.googleapis.com/auth/admin.directory.group.member',
        ]
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file_path,
            scopes=scopes,
        )
        delegated_credentials = credentials.with_subject(
            'ocfbot@ocf.berkeley.edu'
        )

        self.groupadmin = googleapiclient.discovery.build(
            'admin',
            'directory_v1',
            credentials=delegated_credentials,
        )

    def list_members(self, list_name):
        """List all the OCF members (@ocf.berkeley.edu emails) in a GApps
        mailing list. Strips email addresses, so this only returns email
        addresses.

        Ignores non-ocf.berkeley.edu emails and ocfbot@ocf.berkeley.edu.
        """
        response = self.groupadmin.members().list(groupKey=list_name).execute()
        emails = (m['email'].split('@') for m in response['members'])

        return [
            username
            for username, domain in emails
            if domain == 'ocf.berkeley.edu'
            if username != 'ocfbot'
        ]

    def add_to_list(self, email, list_name):
        """Adds an email address to a Google mailing list."""
        body = {'email': email}

        self.groupadmin.members().insert(
            groupKey=list_name,
            body=body,
        ).execute()
