import re
from textwrap import dedent

import mock

from .application_test import VHOSTS_EXAMPLE as VHOSTS_APP_EXAMPLE
from .web_test import VHOSTS_EXAMPLE as VHOSTS_WEB_EXAMPLE
from ocflib.vhost.config import build_app_config
from ocflib.vhost.config import build_web_config


class TestBuildConfig:
    @mock.patch(
        'ocflib.vhost.web.get_vhost_db',
        return_value=VHOSTS_WEB_EXAMPLE.splitlines(),
    )
    def test_build_web_config(self, _):
        config = build_web_config()

        # Actually testing config files is hard, so just match some regexes
        m = re.match(dedent("""\
            # archive\.asuc\.org \(user asucarch\)
            (.*)
            # docs\.ocf\.berkeley\.edu \(user ocfwiki\)
            (.*)
            # contrib\.berkeley\.edu \(user staff\)
            (.*)\
        """), config, re.DOTALL)

        # Should find all aliases
        assert re.search('ServerAlias www\.archive\.asuc\.org modern\.asuc\.org www\.modern\.asuc\.org', m.group(1))

        # Should find a VirtualHost for each port
        assert re.search('\*:443.*\*:80', m.group(1), re.DOTALL)

        # Should find correct docroot
        assert re.search('DocumentRoot /services/http/users/s/staff', m.group(3))

        # Shouldn't find SSL when [nossl] is present
        assert not re.search('SSL', m.group(3))

    @mock.patch(
        'ocflib.vhost.application.get_app_vhost_db',
        return_value=VHOSTS_APP_EXAMPLE.splitlines(),
    )
    def test_build_app_config(self, _):
        config = build_app_config()

        # Actually testing config files is hard, so just match some regexes
        m = re.match(dedent("""\
            # api\.asuc\.ocf\.berkeley\.edu \(user asucapp\)
            (.*)
            # dev-app\.ocf\.berkeley\.edu \(user ggroup\)
            (.*)
            # upe\.berkeley\.edu \(user upe\)
            (.*)\
        """), config, re.DOTALL)

        # Should find all aliases
        assert re.search(
            'server_name "api\.asuc\.ocf\.berkeley\.edu"'
            ' "api-asuc-ocf-berkeley-edu\.apphost\.ocf\.berkeley\.edu"'
            ' "api\.asuc\.org";',
            m.group(1)
        )

        # Should find a vhost for each port
        assert re.search('listen 443;.*listen \[::\]:443;.*listen 80;.*listen \[::\]:80;', m.group(1), re.DOTALL)

        # Should find correct socket
        assert re.search('proxy_pass http://unix:/srv/apps/asucapp/prod\.sock', m.group(1))
        assert re.search('proxy_pass http://unix:/srv/apps/upe/upe\.sock', m.group(3))
