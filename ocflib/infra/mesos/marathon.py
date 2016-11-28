import time
from functools import partial

import requests

MARATHON_URL = 'https://marathon.ocf.berkeley.edu'


class DeploymentException(Exception):
    pass


class MarathonClient:

    def __init__(self, user, password, url=MARATHON_URL):
        self.user = user
        self.password = password
        self.url = url

        self.get = partial(self.request, 'get')
        self.put = partial(self.request, 'put')
        self.delete = partial(self.request, 'delete')
        self.post = partial(self.request, 'post')

    def request(self, method, path, *args, expected_status=200, **kwargs):
        req = requests.request(
            method,
            self.url + path,
            auth=(self.user, self.password),
            *args,
            **kwargs
        )
        assert req.status_code == expected_status, req.status_code
        return req

    def app_status(self, app):
        req = self.get('/v2/apps/' + app)
        return req.json()

    def deploy_app(
            self,
            app,
            version,
            report=lambda *args, **kwargs: None,
            force=False,
            timeout=180,
    ):
        status = self.app_status(app)
        image, tag = status['app']['container']['docker']['image'].split(':')

        deployments = status['app']['deployments']
        if deployments:
            report('A deployment is already in progress:')
            report(deployments)

            if not force:
                raise DeploymentException(
                    'A deployment is already in process:\n{}'.format(deployments),
                )
            else:
                report('You specified force, so going ahead anyway.')

        report('Updating from current tag "{}" to "{}"'.format(tag, version))
        status['app']['container']['docker']['image'] = '{}:{}'.format(image, version)
        self.put(
            '/v2/apps/' + app + ('?force=true' if force else ''),
            json={'container': status['app']['container']},
        )

        # wait for deployment to finish, report status
        status = None
        for _ in range(timeout):
            status = self.app_status(app)
            if not status['app']['deployments']:
                report('Deployment finished!')
                return 0
            else:
                report('Waiting for deployment to finish: {}'.format(status['app']['deployments']))
                time.sleep(1)
        else:
            bad_deployment, = status['app']['deployments']
            self.delete('/v2/deployments/' + bad_deployment['id'])

            raise DeploymentException(
                'Gave up waiting for deployment {} after {} seconds.\n'
                'Automatically rolling back.'.format(
                    bad_deployment,
                    timeout,
                ),
            )
