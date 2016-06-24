""" test_apt_custom_sources_list
Test templating of custom sources list
"""
import logging
import os
import shutil
import tempfile

from unittest import TestCase

import yaml
import mock

from curtin import util
from curtin.commands import apt_source

LOG = logging.getLogger(__name__)

TARGET = "/"

# Input and expected output for the custom template
YAML_TEXT_CUSTOM_SL = """
apt_mirror: http://archive.ubuntu.com/ubuntu
apt_custom_sources_list: |

    ## Note, this file is written by curtin at install time. It should not end
    ## up on the installed system itself.
    #
    # See http://help.ubuntu.com/community/UpgradeNotes for how to upgrade to
    # newer versions of the distribution.
    deb $MIRROR $RELEASE main restricted
    deb-src $MIRROR $RELEASE main restricted
    deb $PRIMARY $RELEASE universe restricted
    deb $SECURITY $RELEASE-security multiverse
    # FIND_SOMETHING_SPECIAL
"""

EXPECTED_CONVERTED_CONTENT = """
## Note, this file is written by curtin at install time. It should not end
## up on the installed system itself.
#
# See http://help.ubuntu.com/community/UpgradeNotes for how to upgrade to
# newer versions of the distribution.
deb http://archive.ubuntu.com/ubuntu fakerel main restricted
deb-src http://archive.ubuntu.com/ubuntu fakerel main restricted
deb http://archive.ubuntu.com/ubuntu fakerel universe restricted
deb http://archive.ubuntu.com/ubuntu fakerel-security multiverse
# FIND_SOMETHING_SPECIAL
"""

# mocked to be independent to the unittest system
MOCKED_APT_SRC_LIST = """
deb http://archive.ubuntu.com/ubuntu/ notouched main restricted
deb-src http://archive.ubuntu.com/ubuntu/ notouched main restricted
deb http://archive.ubuntu.com/ubuntu/ notouched-updates main restricted
deb http://security.ubuntu.com/ubuntu notouched-security main restricted
"""

EXPECTED_BASE_CONTENT = ("""
deb http://archive.ubuntu.com/ubuntu/ notouched main restricted
deb-src http://archive.ubuntu.com/ubuntu/ notouched main restricted
deb http://archive.ubuntu.com/ubuntu/ notouched-updates main restricted
deb http://security.ubuntu.com/ubuntu notouched-security main restricted
""")

EXPECTED_MIRROR_CONTENT = ("""
deb http://test.archive.ubuntu.com/ubuntu/ notouched main restricted
deb-src http://test.archive.ubuntu.com/ubuntu/ notouched main restricted
deb http://test.archive.ubuntu.com/ubuntu/ notouched-updates main restricted
deb http://test.archive.ubuntu.com/ubuntu notouched-security main restricted
""")

EXPECTED_PRIMSEC_CONTENT = ("""
deb http://test.archive.ubuntu.com/ubuntu/ notouched main restricted
deb-src http://test.archive.ubuntu.com/ubuntu/ notouched main restricted
deb http://test.archive.ubuntu.com/ubuntu/ notouched-updates main restricted
deb http://test.security.ubuntu.com/ubuntu notouched-security main restricted
""")


def load_tfile_or_url(*args, **kwargs):
    """ load_tfile_or_url
    load file and return content after decoding
    """
    return util.decode_binary(util.read_file_or_url(*args, **kwargs).contents)


class TestAptSourceConfigSourceList(TestCase):
    """TestAptSourceConfigSourceList - Class to test sources list rendering"""
    def setUp(self):
        super(TestAptSourceConfigSourceList, self).setUp()
        self.new_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.new_root)
        # self.patchUtils(self.new_root)

    @staticmethod
    def _apt_source_list(cfg, expected):
        "_apt_source_list - Test rendering from template (generic)"

        with mock.patch.object(util, 'write_file') as mockwrite:
            # keep it side effect free and avoid permission errors
            with mock.patch.object(os, 'rename'):
                with mock.patch.object(util, 'lsb_release',
                                       return_value={'codename': 'fakerel'}):
                    # make test independent to executing system
                    with mock.patch.object(util, 'load_file',
                                           return_value=MOCKED_APT_SRC_LIST):
                        apt_source.handle_apt_source(cfg, TARGET)

        mockwrite.assert_called_once_with(
            TARGET + '/etc/apt/sources.list',
            expected,
            mode=420)

    def test_apt_source_list(self):
        """test_apt_source_list - Test with neither custom sources nor parms"""
        cfg = {}

        self._apt_source_list(cfg, EXPECTED_BASE_CONTENT)

    def test_apt_source_list_mirror(self):
        """test_apt_source_list_mirror - Test specifying mirrors"""
        cfg = {'apt_mirror': 'http://test.archive.ubuntu.com/ubuntu'}
        self._apt_source_list(cfg, EXPECTED_MIRROR_CONTENT)

    def test_apt_source_list_psm(self):
        """test_apt_source_list_psm - Test specifying prim+sec mirrors"""
        cfg = {'apt_primary_mirror': 'http://test.archive.ubuntu.com/ubuntu',
               'apt_security_mirror': 'http://test.security.ubuntu.com/ubuntu'}

        self._apt_source_list(cfg, EXPECTED_PRIMSEC_CONTENT)

    @staticmethod
    def test_apt_srcl_custom():
        """test_apt_srcl_custom - Test rendering a custom source template"""
        cfg = yaml.safe_load(YAML_TEXT_CUSTOM_SL)

        with mock.patch.object(util, 'write_file') as mockwrite:
            # keep it side effect free and avoid permission errors
            with mock.patch.object(os, 'rename'):
                with mock.patch.object(util, 'lsb_release',
                                       return_value={'codename': 'fakerel'}):
                    apt_source.handle_apt_source(cfg, TARGET)

        mockwrite.assert_called_once_with(
            TARGET + '/etc/apt/sources.list',
            EXPECTED_CONVERTED_CONTENT,
            mode=420)


# vi: ts=4 expandtab
