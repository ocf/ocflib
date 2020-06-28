import mock

from ocflib.infra.github import get_github_file
from ocflib.infra.github import get_repo
from ocflib.infra.github import GithubCredentials
from ocflib.infra.github import modify_and_branch
from ocflib.infra.github import OCF_GITHUB_ORG

TEST_REPO_NAME = 'ocftest'


class TestGithub:

    @mock.patch('ocflib.infra.github.Github')
    def test_get_repo_no_credentials(self, github_mock):
        gh = github_mock.return_value
        get_repo(TEST_REPO_NAME)
        assert github_mock.call_count == 1
        gh.get_repo.assert_called_once_with(TEST_REPO_NAME)

    @mock.patch('ocflib.infra.github.Github')
    def test_get_repo_with_username_and_password(self, github_mock):
        gh = github_mock.return_value
        creds = GithubCredentials(
            username='testusername', password='testpassword'
        )
        get_repo(TEST_REPO_NAME, credentials=creds)
        assert github_mock.call_count == 1
        github_mock.assert_called_once_with('testusername', 'testpassword')
        gh.get_repo.assert_called_once_with(TEST_REPO_NAME)

    @mock.patch('ocflib.infra.github.Github')
    def test_get_repo_with_token(self, github_mock):
        gh = github_mock.return_value
        creds = GithubCredentials(
            token='testtoken'
        )
        get_repo(TEST_REPO_NAME, credentials=creds)
        assert github_mock.call_count == 1
        github_mock.assert_called_once_with('testtoken')
        gh.get_repo.assert_called_once_with(TEST_REPO_NAME)

    def test_get_ocf_file(self):
        assert get_github_file(OCF_GITHUB_ORG + '/ocflib', 'README.md')

    @mock.patch('ocflib.infra.github.Github')
    @mock.patch('ocflib.infra.github.InputGitTreeElement')
    def test_modify_and_branch(self, github_mock, inputtreeelem_mock):
        repo = get_repo('ocf')
        modify_and_branch(repo, 'master', 'new_branch', 'testcommit', 'testfilename', 'testcontent')

        # new ref must be created
        assert github_mock.call_count == 1
        assert repo.create_git_ref.call_args[0][0] == 'refs/heads/new_branch'

        # at some point the new tree element must be created
        assert inputtreeelem_mock.call_count == 1
