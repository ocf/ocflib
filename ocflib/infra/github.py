from github import Github

class GithubCredentials():
    """Basic class to store Github credentials and verify input"""

    def __init__(self, username=None, password=None, token=None):
        if not (username or password or token):
            raise ValueError('No credentials supplied')

        if (username and password and token):
            raise ValueError('Can\'t pass in both username/password and token')

        if (username and not password) or (password and not username):
            raise ValueError('Username/password supplied but not the other')

        self.username = username
        self.password = password
        self.token = token


class GitRepo():
    """
    Extension of PyGithub with a couple of other helper methods.
    """

    def __init__(self, repo_name, credentials=None):
        """Retrieves a Repository by its fully qualified name. If credentials are passed
        they will be used."""
        if not credentials:
            self._github = Github().get_repo(repo_name)
        elif credentials.token:
            self._github = Github(credentials.token).get_repo(repo_name)
        else:
            self._github = Github(credentials.username, credentials.password).get_repo(repo_name)

    @property
    def github(self):
        """
        Direct access to the underlying PyGithub object.
        """
        return self._github

    def get_file(self, filename):
        """Fetch and decode the file from the master branch.
        Note that GitHub's API only supports files up to 1MB in size."""
        return self._github.get_contents(filename).decoded_content.decode('utf-8')

    def modify_and_branch(self, base_branch, new_branch_name, commit_message, file_path, file_contents):
        """Create a new branch from base_branch, makes changes to a file, and
        commits it to the new branch."""
        
        base_sha = self._github.get_branch(base_branch).commit.sha
        self._github.create_git_ref('refs/heads/{}'.format(new_branch_name), base_sha)
        current_contents = self._github.get_contents(file_path, ref=new_branch_name)
        self._github.update_file(file_path,
                                 commit_message,
                                 file_contents,
                                 current_contents.sha,
                                 branch=new_branch_name)

        
