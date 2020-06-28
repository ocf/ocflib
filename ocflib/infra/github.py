from github import Github
from github import InputGitTreeElement

OCF_GITHUB_ORG = 'ocf'


class GithubCredentials():
    """Basic class to store Github credentials and verify input"""

    def __init__(self, username=None, password=None, token=None):
        if (username and password and token) or not (username or password or token):
            raise ValueError('Pass in either a username/password pair or token')

        if (username and not password) or (password and not username):
            raise ValueError('Username/passwod supplied but not the other')

        self.username = username
        self.password = password
        self.token = token


def get_repo(repo_name, credentials=None):
    """Retrieves a Repository by its fully qualified name. If credentials are passed
    they will be used. The repo can be manipulated with the PyGithub API."""
    if not credentials:
        return Github().get_repo(repo_name)

    if credentials.token:
        return Github(credentials.token).get_repo(repo_name)

    return Github(credentials.username, credentials.password).get_repo(repo_name)


def get_github_file(repo_name, filename):
    """Fetch and decode the file from master. Right now this method only supports public repos
    and the repo name must be fully qualified e.g. ocf/etc.
    Note that GitHub's API only supports files up to 1MB in size."""
    return Github().get_repo(repo_name).get_contents(filename).decoded_content.decode('utf-8')


def modify_and_branch(repo, base_branch, new_branch_name, commit_message, filename, file_content):
    """Create a new branch from base_branch, makes changes to a file, and
    commits it to the new branch."""

    base_sha = repo.get_git_ref('heads/{}'.format(base_branch)).object.sha
    base_tree = repo.get_git_tree(base_sha)
    element = InputGitTreeElement(filename, '100644', 'blob', file_content)
    tree = repo.create_git_tree([element], base_tree)

    parent = repo.get_git_commit(base_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])

    repo.create_git_ref('refs/heads/{}'.format(new_branch_name), commit.sha)
