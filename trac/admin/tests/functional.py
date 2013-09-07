#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2013 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.

from trac.tests.functional import *
from trac.util.text import unicode_to_base64, unicode_from_base64


class AuthorizationTestCaseSetup(FunctionalTwillTestCaseSetup):
    def test_authorization(self, href, perms, h2_text):
        """Check permissions required to access an administration panel. A
        fine-grained permissions test will also be executed if ConfigObj is
        installed.

        :param href: the relative href of the administration panel
        :param perms: list or tuple of permissions required to access
                      the administration panel
        :param h2_text: the body of the h2 heading on the administration
                        panel"""
        self._tester.logout()
        self._tester.login('user')
        if isinstance(perms, basestring):
            perms = (perms, )

        try:
            for perm in perms:
                try:
                    tc.go(href)
                    tc.find("No administration panels available")
                    self._testenv.grant_perm('user', perm)
                    tc.go(href)
                    tc.find(r"<h2>%s</h2>" % h2_text)
                finally:
                    self._testenv.revoke_perm('user', perm)
                try:
                    tc.go(href)
                    tc.find("No administration panels available")
                    self._testenv.enable_authz_permpolicy({
                        href.strip('/').replace('/', ':', 1): {'user': perm},
                    })
                    tc.go(href)
                    tc.find(r"<h2>%s</h2>" % h2_text)
                except ImportError:
                    pass
                finally:
                    self._testenv.disable_authz_permpolicy()
        finally:
            self._tester.logout()
            self._tester.login('admin')


class TestBasicSettings(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Check basic settings."""
        self._tester.go_to_admin()
        tc.formvalue('modbasic', 'url', 'https://my.example.com/something')
        tc.submit()
        tc.find('https://my.example.com/something')


class TestBasicSettingsAuthorization(AuthorizationTestCaseSetup):
    def runTest(self):
        """Check permissions required to access Basic Settings panel."""
        self.test_authorization('/admin/general/basics', 'TRAC_ADMIN',
                                "Basic Settings")


class TestLoggingNone(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Turn off logging."""
        # For now, we just check that it shows up.
        self._tester.go_to_admin("Logging")
        tc.find('trac.log')
        tc.formvalue('modlog', 'log_type', 'none')
        tc.submit()
        tc.find('selected="selected">None</option')


class TestLoggingAuthorization(AuthorizationTestCaseSetup):
    def runTest(self):
        """Check permissions required to access Logging panel."""
        self.test_authorization('/admin/general/logging', 'TRAC_ADMIN',
                                "Logging")


class TestLoggingToFile(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Turn logging back on."""
        # For now, we just check that it shows up.
        self._tester.go_to_admin("Logging")
        tc.find('trac.log')
        tc.formvalue('modlog', 'log_type', 'file')
        tc.formvalue('modlog', 'log_file', 'trac.log2')
        tc.formvalue('modlog', 'log_level', 'INFO')
        tc.submit()
        tc.find('selected="selected">File</option')
        tc.find('id="log_file".*value="trac.log2"')
        tc.find('selected="selected">INFO</option>')


class TestLoggingToFileNormal(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Setting logging back to normal."""
        # For now, we just check that it shows up.
        self._tester.go_to_admin("Logging")
        tc.find('trac.log')
        tc.formvalue('modlog', 'log_file', 'trac.log')
        tc.formvalue('modlog', 'log_level', 'DEBUG')
        tc.submit()
        tc.find('selected="selected">File</option')
        tc.find('id="log_file".*value="trac.log"')
        tc.find('selected="selected">DEBUG</option>')


class TestPermissionsAuthorization(AuthorizationTestCaseSetup):
    def runTest(self):
        """Check permissions required to access Permissions panel."""
        self.test_authorization('/admin/general/perm',
                                ('PERMISSION_GRANT', 'PERMISSION_REVOKE'),
                                "Manage Permissions and Groups")


class TestCreatePermissionGroup(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Create a permissions group"""
        self._tester.go_to_admin("Permissions")
        tc.find('Manage Permissions')
        tc.formvalue('addperm', 'gp_subject', 'somegroup')
        tc.formvalue('addperm', 'action', 'REPORT_CREATE')
        tc.submit()
        somegroup = unicode_to_base64('somegroup')
        REPORT_CREATE = unicode_to_base64('REPORT_CREATE')
        tc.find('%s:%s' % (somegroup, REPORT_CREATE))


class TestAddUserToGroup(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Add a user to a permissions group"""
        self._tester.go_to_admin("Permissions")
        tc.find('Manage Permissions')
        tc.formvalue('addsubj', 'sg_subject', 'authenticated')
        tc.formvalue('addsubj', 'sg_group', 'somegroup')
        tc.submit()
        authenticated = unicode_to_base64('authenticated')
        somegroup = unicode_to_base64('somegroup')
        tc.find('%s:%s' % (authenticated, somegroup))


class TestRemoveUserFromGroup(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Remove a user from a permissions group"""
        self._tester.go_to_admin("Permissions")
        tc.find('Manage Permissions')
        authenticated = unicode_to_base64('authenticated')
        somegroup = unicode_to_base64('somegroup')
        tc.find('%s:%s' % (authenticated, somegroup))
        tc.formvalue('revokeform', 'sel', '%s:%s' % (authenticated, somegroup))
        tc.submit()
        tc.notfind('%s:%s' % (authenticated, somegroup))


class TestRemovePermissionGroup(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Remove a permissions group"""
        self._tester.go_to_admin("Permissions")
        tc.find('Manage Permissions')
        somegroup = unicode_to_base64('somegroup')
        REPORT_CREATE = unicode_to_base64('REPORT_CREATE')
        tc.find('%s:%s' % (somegroup, REPORT_CREATE))
        tc.formvalue('revokeform', 'sel', '%s:%s' % (somegroup, REPORT_CREATE))
        tc.submit()
        tc.notfind('%s:%s' % (somegroup, REPORT_CREATE))
        tc.notfind(somegroup)


class TestPluginSettings(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Check plugin settings."""
        self._tester.go_to_admin("Plugins")
        tc.find('Manage Plugins')
        tc.find('Install Plugin')


class TestPluginsAuthorization(AuthorizationTestCaseSetup):
    def runTest(self):
        """Check permissions required to access Logging panel."""
        self.test_authorization('/admin/general/plugin', 'TRAC_ADMIN',
                                "Manage Plugins")


class RegressionTestTicket11069(FunctionalTwillTestCaseSetup):
    def runTest(self):
        """Test for regression of http://trac.edgewall.org/ticket/11069
        The permissions list should only be populated with permissions that
        the user can grant."""
        self._tester.logout()
        self._tester.login('user')
        self._testenv.grant_perm('user', 'PERMISSION_GRANT')
        env = self._testenv.get_trac_environment()
        from trac.perm import PermissionSystem
        user_perms = PermissionSystem(env).get_user_permissions('user')
        all_actions = PermissionSystem(env).get_actions()
        try:
            self._tester.go_to_admin("Permissions")
            for action in all_actions:
                option = r"<option>%s</option>" % action
                if action in user_perms and user_perms[action] is True:
                    tc.find(option)
                else:
                    tc.notfind(option)
        finally:
            self._testenv.revoke_perm('user', 'PERMISSION_GRANT')
            self._tester.logout()
            self._tester.login('admin')


class RegressionTestTicket11117(FunctionalTwillTestCaseSetup):
    """Test for regression of http://trac.edgewall.org/ticket/11117
    Hint should be shown on the Basic Settings admin panel when pytz is not
    installed.
    """
    def runTest(self):
        self._tester.go_to_admin("Basic Settings")
        pytz_hint = "Install pytz for a complete list of timezones."
        from trac.util.datefmt import pytz
        if pytz is None:
            tc.find(pytz_hint)
        else:
            tc.notfind(pytz_hint)


class RegressionTestTicket11257(FunctionalTwillTestCaseSetup):
    """Test for regression of http://trac.edgewall.org/ticket/11257
    Hints should be shown on the Basic Settings admin panel when Babel is not
    installed.
    """
    def runTest(self):
        self._tester.go_to_admin("Basic Settings")
        babel_hints = ("Install Babel for extended language support.",
                       "Install Babel for localized date formats.")
        try:
            import babel
        except ImportError:
            babel = None
        for hint in babel_hints:
            if babel is None:
                tc.find(hint)
            else:
                tc.notfind(hint)


def functionalSuite(suite=None):
    if not suite:
        import trac.tests.functional.testcases
        suite = trac.tests.functional.testcases.functionalSuite()
    suite.addTest(TestBasicSettings())
    suite.addTest(TestBasicSettingsAuthorization())
    suite.addTest(TestLoggingNone())
    suite.addTest(TestLoggingAuthorization())
    suite.addTest(TestLoggingToFile())
    suite.addTest(TestLoggingToFileNormal())
    suite.addTest(TestPermissionsAuthorization())
    suite.addTest(TestCreatePermissionGroup())
    suite.addTest(TestAddUserToGroup())
    suite.addTest(TestRemoveUserFromGroup())
    suite.addTest(TestRemovePermissionGroup())
    suite.addTest(TestPluginSettings())
    suite.addTest(TestPluginsAuthorization())
    suite.addTest(RegressionTestTicket11069())
    suite.addTest(RegressionTestTicket11117())
    suite.addTest(RegressionTestTicket11257())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='functionalSuite')
