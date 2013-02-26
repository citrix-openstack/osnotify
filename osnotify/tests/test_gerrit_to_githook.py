import unittest
from osnotify import gerrit

merge_commit = """
{
    "type":"change-merged",
    "change":
    {
        "project":"openstack/nova",
        "branch":"master"
    }
}
"""

class TestToGitHook(unittest.TestCase):
    def test_is_valid(self):
        go = gerrit.GerritMessage(merge_commit)
        self.assertTrue(go.valid)

    def test_is_merge(self):
        go = gerrit.GerritMessage(merge_commit)
        self.assertTrue(go.is_merge)

    def test_project(self):
        go = gerrit.GerritMessage(merge_commit)
        self.assertEquals('openstack/nova', go.project)

    def test_user(self):
        go = gerrit.GerritMessage(merge_commit)
        self.assertEquals('openstack', go.user)

    def test_repo(self):
        go = gerrit.GerritMessage(merge_commit)
        self.assertEquals('nova', go.repo)

    def test_branch(self):
        go = gerrit.GerritMessage(merge_commit)
        self.assertEquals('master', go.branch)

    def test_repo_name(self):
        go = gerrit.GerritMessage(merge_commit)
        payload = gerrit.to_hook_payload(go)

        self.assertEquals('nova', payload['repository']['name'])

    def test_owner_name(self):
        go = gerrit.GerritMessage(merge_commit)
        payload = gerrit.to_hook_payload(go)

        self.assertEquals('openstack', payload['repository']['owner']['name'])

    def test_ref(self):
        go = gerrit.GerritMessage(merge_commit)
        payload = gerrit.to_hook_payload(go)

        self.assertEquals('refs/heads/master', payload['ref'])
