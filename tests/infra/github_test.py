import mock

from ocflib.infra.github import GithubCredentials
from ocflib.infra.github import GitRepo


TEST_REPO_NAME = 'ocftest'


class TestGithub:

    @mock.patch('ocflib.infra.github.Github')
    def test_get_repo_no_credentials(self, github_mock):
        gh = github_mock.return_value
        GitRepo(TEST_REPO_NAME)
        assert github_mock.call_count == 1
        gh.get_repo.assert_called_once_with(TEST_REPO_NAME)

    @mock.patch('ocflib.infra.github.Github')
    def test_get_repo_with_username_and_password(self, github_mock):
        gh = github_mock.return_value
        creds = GithubCredentials(
            username='testusername', password='testpassword'
        )
        GitRepo(TEST_REPO_NAME, credentials=creds)
        assert github_mock.call_count == 1
        github_mock.assert_called_once_with('testusername', 'testpassword')
        gh.get_repo.assert_called_once_with(TEST_REPO_NAME)

    @mock.patch('ocflib.infra.github.Github')
    def test_get_repo_with_token(self, github_mock):
        gh = github_mock.return_value
        creds = GithubCredentials(
            token='testtoken',
        )
        GitRepo(TEST_REPO_NAME, credentials=creds)
        assert github_mock.call_count == 1
        github_mock.assert_called_once_with('testtoken')
        gh.get_repo.assert_called_once_with(TEST_REPO_NAME)

    def test_get_ocf_file(self):
        assert GitRepo('ocf/ocflib').get_file('README.md')

    @mock.patch('ocflib.infra.github.Github')
    @mock.patch('ocflib.infra.github.InputGitTreeElement')
    def test_modify_and_branch(self, github_mock, inputtreeelem_mock):
        r = GitRepo('ocf')
        r.modify_and_branch('master', 'new_branch', 'testcommit', 'testfilename', 'testcontent')

        # new ref must be created
        assert github_mock.call_count == 1
        assert r.github.create_git_ref.call_args[0][0] == 'refs/heads/new_branch'

        # at some point the new tree element must be created
        assert inputtreeelem_mock.call_count == 1
