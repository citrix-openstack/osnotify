import json


def to_hook_payload(message):
    try:
        return dict(
            ref='refs/heads/' + message.branch,
            repository=dict(
                name=message.repo,
                owner=dict(
                    name=message.user
                )
            )
        )
    except:
        return None


class GerritMessage(object):
    def __init__(self, raw_message):
        self.raw_message = raw_message
        self._message = None

    @property
    def message(self):
        if self._message is None:
            self._message = json.loads(self.raw_message)
        return self._message

    @property
    def is_merge(self):
        return self._value_of('type') == 'change-merged'

    @property
    def project(self):
        return self._value_of('change', 'project')

    @property
    def branch(self):
        return self._value_of('change', 'branch')

    def _value_of(self, *keys):
        try:
            msg = self.message
            for key in keys:
                msg = msg[key]
            return msg
        except:
            return 'unknown'

    @property
    def repo(self):
        return self.project.split('/')[1]

    @property
    def user(self):
        return self.project.split('/')[0]
