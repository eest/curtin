#   Copyright (C) 2016 Canonical Ltd.
#
#   Author: Scott Moser <scott.moser@canonical.com>
#
#   Curtin is free software: you can redistribute it and/or modify it under
#   the terms of the GNU Affero General Public License as published by the
#   Free Software Foundation, either version 3 of the License, or (at your
#   option) any later version.
#
#   Curtin is distributed in the hope that it will be useful, but WITHOUT ANY
#   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
#   more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with Curtin.  If not, see <http://www.gnu.org/licenses/>.

import contextlib
import imp
import importlib
import mock
import os
import shutil
import tempfile
from unittest import TestCase


def builtin_module_name():
    options = ('builtins', '__builtin__')
    for name in options:
        try:
            imp.find_module(name)
        except ImportError:
            continue
        else:
            print('importing and returning: %s' % name)
            importlib.import_module(name)
            return name


@contextlib.contextmanager
def simple_mocked_open(content=None):
    if not content:
        content = ''
    m_open = mock.mock_open(read_data=content)
    mod_name = builtin_module_name()
    m_patch = '{}.open'.format(mod_name)
    with mock.patch(m_patch, m_open, create=True):
        yield m_open


class CiTestCase(TestCase):
    """Common testing class which all curtin unit tests subclass."""

    def tmp_dir(self, dir=None, cleanup=True):
        """Return a full path to a temporary directory for the test run."""
        if dir is None:
            tmpd = tempfile.mkdtemp(
                prefix="curtin-ci-%s." % self.__class__.__name__)
        else:
            tmpd = tempfile.mkdtemp(dir=dir)
        self.addCleanup(shutil.rmtree, tmpd)
        return tmpd

    def tmp_path(self, path, _dir=None):
        # return an absolute path to 'path' under dir.
        # if dir is None, one will be created with tmp_dir()
        # the file is not created or modified.
        if _dir is None:
            _dir = self.tmp_dir()
        return os.path.normpath(os.path.abspath(os.path.join(_dir, path)))
