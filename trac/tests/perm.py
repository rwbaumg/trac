# -*- coding: utf-8 -*-
#
# Copyright (C) 2004-2013 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.

import unittest

from trac import perm
from trac.core import *
from trac.resource import Resource
from trac.test import EnvironmentStub


class DefaultPermissionStoreTestCase(unittest.TestCase):

    def setUp(self):
        self.env = \
            EnvironmentStub(enable=[perm.DefaultPermissionStore,
                                    perm.DefaultPermissionGroupProvider])
        self.store = perm.DefaultPermissionStore(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_simple_actions(self):
        self.env.db_transaction.executemany(
            "INSERT INTO permission VALUES (%s,%s)",
            [('john', 'WIKI_MODIFY'),
             ('john', 'REPORT_ADMIN'),
             ('kate', 'TICKET_CREATE')])
        self.assertEqual(['REPORT_ADMIN', 'WIKI_MODIFY'],
                         sorted(self.store.get_user_permissions('john')))
        self.assertEqual(['TICKET_CREATE'],
                         self.store.get_user_permissions('kate'))

    def test_simple_group(self):
        self.env.db_transaction.executemany(
            "INSERT INTO permission VALUES (%s,%s)",
            [('dev', 'WIKI_MODIFY'),
             ('dev', 'REPORT_ADMIN'),
             ('john', 'dev')])
        self.assertEqual(['REPORT_ADMIN', 'WIKI_MODIFY'],
                         sorted(self.store.get_user_permissions('john')))

    def test_nested_groups(self):
        self.env.db_transaction.executemany(
            "INSERT INTO permission VALUES (%s,%s)",
            [('dev', 'WIKI_MODIFY'),
             ('dev', 'REPORT_ADMIN'),
             ('admin', 'dev'),
             ('john', 'admin')])
        self.assertEqual(['REPORT_ADMIN', 'WIKI_MODIFY'],
                         sorted(self.store.get_user_permissions('john')))

    def test_mixed_case_group(self):
        self.env.db_transaction.executemany(
            "INSERT INTO permission VALUES (%s,%s)",
            [('Dev', 'WIKI_MODIFY'),
             ('Dev', 'REPORT_ADMIN'),
             ('Admin', 'Dev'),
             ('john', 'Admin')])
        self.assertEqual(['REPORT_ADMIN', 'WIKI_MODIFY'],
                         sorted(self.store.get_user_permissions('john')))

    def test_builtin_groups(self):
        self.env.db_transaction.executemany(
            "INSERT INTO permission VALUES (%s,%s)",
            [('authenticated', 'WIKI_MODIFY'),
             ('authenticated', 'REPORT_ADMIN'),
             ('anonymous', 'TICKET_CREATE')])
        self.assertEqual(['REPORT_ADMIN', 'TICKET_CREATE', 'WIKI_MODIFY'],
                         sorted(self.store.get_user_permissions('john')))
        self.assertEqual(['TICKET_CREATE'],
                         self.store.get_user_permissions('anonymous'))

    def test_get_all_permissions(self):
        self.env.db_transaction.executemany(
            "INSERT INTO permission VALUES (%s,%s)",
            [('dev', 'WIKI_MODIFY'),
             ('dev', 'REPORT_ADMIN'),
             ('john', 'dev')])
        expected = [('dev', 'WIKI_MODIFY'),
                    ('dev', 'REPORT_ADMIN'),
                    ('john', 'dev')]
        for res in self.store.get_all_permissions():
            self.assertIn(res, expected)


class TestPermissionRequestor(Component):
    implements(perm.IPermissionRequestor)

    def get_permission_actions(self):
        return ['TEST_CREATE', 'TEST_DELETE', 'TEST_MODIFY',
                ('TEST_CREATE', []),
                ('TEST_ADMIN', ['TEST_CREATE', 'TEST_DELETE']),
                ('TEST_ADMIN', ['TEST_MODIFY'])]


class PermissionErrorTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()

    def test_default_message(self):
        permission_error = perm.PermissionError()
        self.assertIsNone(permission_error.action)
        self.assertIsNone(permission_error.resource)
        self.assertIsNone(permission_error.env)
        self.assertEqual("Insufficient privileges to perform this operation.",
                         unicode(permission_error))
        self.assertEqual("Forbidden", permission_error.title)
        self.assertEqual(unicode(permission_error), permission_error.message)

    def test_message_specified(self):
        message = "The message."
        permission_error = perm.PermissionError(msg=message)
        self.assertEqual(message, unicode(permission_error))

    def test_message_from_action(self):
        action = 'WIKI_VIEW'
        permission_error = perm.PermissionError(action)
        self.assertEqual(action, permission_error.action)
        self.assertIsNone(permission_error.resource)
        self.assertIsNone(permission_error.env)
        self.assertEqual("WIKI_VIEW privileges are required to perform this "
                         "operation. You don't have the required "
                         "permissions.", unicode(permission_error))

    def test_message_from_action_and_resource(self):
        action = 'WIKI_VIEW'
        resource = Resource('wiki', 'WikiStart')
        permission_error = perm.PermissionError(action, resource, self.env)
        self.assertEqual(action, permission_error.action)
        self.assertEqual(resource, permission_error.resource)
        self.assertEqual(self.env, permission_error.env)
        self.assertEqual("WIKI_VIEW privileges are required to perform this "
                         "operation on WikiStart. You don't have the "
                         "required permissions.", unicode(permission_error))


class PermissionSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=[perm.PermissionSystem,
                                           perm.DefaultPermissionStore,
                                           TestPermissionRequestor])
        self.perm = perm.PermissionSystem(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_all_permissions(self):
        self.assertEqual({'TRAC_ADMIN': True, 'TEST_CREATE': True,
                          'TEST_DELETE': True, 'TEST_MODIFY': True,
                          'TEST_ADMIN': True},
                         self.perm.get_user_permissions())

    def test_simple_permissions(self):
        self.perm.grant_permission('bob', 'TEST_CREATE')
        self.perm.grant_permission('jane', 'TEST_DELETE')
        self.perm.grant_permission('jane', 'TEST_MODIFY')
        self.assertEqual({'TEST_CREATE': True},
                         self.perm.get_user_permissions('bob'))
        self.assertEqual({'TEST_DELETE': True, 'TEST_MODIFY': True},
                         self.perm.get_user_permissions('jane'))

    def test_meta_permissions(self):
        self.perm.grant_permission('bob', 'TEST_CREATE')
        self.perm.grant_permission('jane', 'TEST_ADMIN')
        self.assertEqual({'TEST_CREATE': True},
                         self.perm.get_user_permissions('bob'))
        self.assertEqual({'TEST_CREATE': True, 'TEST_DELETE': True,
                          'TEST_MODIFY': True,  'TEST_ADMIN': True},
                         self.perm.get_user_permissions('jane'))

    def test_undefined_permissions(self):
        """Only defined actions are returned in the dictionary."""
        self.perm.grant_permission('bob', 'TEST_CREATE')
        self.perm.grant_permission('jane', 'TEST_DELETE')
        self.perm.grant_permission('jane', 'TEST_MODIFY')

        self.env.disable_component(TestPermissionRequestor)

        self.assertEqual({}, self.perm.get_user_permissions('bob'))
        self.assertEqual({}, self.perm.get_user_permissions('jane'))

    def test_grant_permission_differs_from_action_by_casing(self):
        """`TracError` is raised when granting a permission that differs
        from an action by casing.
        """
        self.assertRaises(TracError, self.perm.grant_permission, 'user1',
                          'Test_Create')

    def test_grant_permission_already_granted(self):
        """`PermissionExistsError` is raised when granting a permission
        that has already been granted.
        """
        self.perm.grant_permission('user1', 'TEST_CREATE')
        self.assertRaises(perm.PermissionExistsError,
                          self.perm.grant_permission, 'user1', 'TEST_CREATE')

    def test_grant_permission_already_in_group(self):
        """`PermissionExistsError` is raised when adding a user to
        a group of which they are already a member.
        """
        self.perm.grant_permission('user1', 'group1')
        self.assertRaises(perm.PermissionExistsError,
                          self.perm.grant_permission, 'user1', 'group1')

    def test_get_all_permissions(self):
        self.perm.grant_permission('bob', 'TEST_CREATE')
        self.perm.grant_permission('jane', 'TEST_ADMIN')
        expected = [('bob', 'TEST_CREATE'),
                    ('jane', 'TEST_ADMIN')]
        for res in self.perm.get_all_permissions():
            self.assertIn(res, expected)

    def test_get_groups_dict(self):
        permissions = [
            ('user2', 'group1'),
            ('user1', 'group1'),
            ('user3', 'group1'),
            ('user3', 'group2')
        ]
        for perm_ in permissions:
            self.perm.grant_permission(*perm_)

        groups = self.perm.get_groups_dict()
        self.assertEqual(2, len(groups))
        self.assertEqual(['user1', 'user2', 'user3'], groups['group1'])
        self.assertEqual(['user3'], groups['group2'])

    def test_get_users_dict(self):
        permissions = [
            ('user2', 'TEST_CREATE'),
            ('user1', 'TEST_DELETE'),
            ('user1', 'TEST_ADMIN'),
            ('user1', 'TEST_CREATE')
        ]
        for perm_ in permissions:
            self.perm.grant_permission(*perm_)

        users = self.perm.get_users_dict()
        self.assertEqual(2, len(users))
        self.assertEqual(['TEST_ADMIN', 'TEST_CREATE', 'TEST_DELETE'],
                         users['user1'])
        self.assertEqual(['TEST_CREATE'], users['user2'])

    def test_expand_actions_iter_7467(self):
        # Check that expand_actions works with iterators (#7467)
        perms = {'TRAC_ADMIN', 'TEST_DELETE', 'TEST_MODIFY', 'TEST_CREATE',
                 'TEST_ADMIN'}
        self.assertEqual(perms, self.perm.expand_actions(['TRAC_ADMIN']))
        self.assertEqual(perms, self.perm.expand_actions(iter(['TRAC_ADMIN'])))


class PermissionCacheTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=[perm.DefaultPermissionStore,
                                           perm.DefaultPermissionPolicy,
                                           TestPermissionRequestor])
        self.env.config.set('trac', 'permission_policies',
                            'DefaultPermissionPolicy')
        self.perm_system = perm.PermissionSystem(self.env)
        # by-pass DefaultPermissionPolicy cache:
        perm.DefaultPermissionPolicy.CACHE_EXPIRY = -1
        self.perm_system.grant_permission('testuser', 'TEST_MODIFY')
        self.perm_system.grant_permission('testuser', 'TEST_ADMIN')
        self.perm = perm.PermissionCache(self.env, 'testuser')

    def tearDown(self):
        self.env.reset_db()

    def test_contains(self):
        self.assertIn('TEST_MODIFY', self.perm)
        self.assertIn('TEST_ADMIN', self.perm)
        self.assertNotIn('TRAC_ADMIN', self.perm)

    def test_has_permission(self):
        self.assertTrue(self.perm.has_permission('TEST_MODIFY'))
        self.assertTrue(self.perm.has_permission('TEST_ADMIN'))
        self.assertFalse(self.perm.has_permission('TRAC_ADMIN'))

    def test_require(self):
        self.perm.require('TEST_MODIFY')
        self.perm.require('TEST_ADMIN')
        self.assertRaises(perm.PermissionError, self.perm.require,
                          'TRAC_ADMIN')

    def test_assert_permission(self):
        self.perm.assert_permission('TEST_MODIFY')
        self.perm.assert_permission('TEST_ADMIN')
        self.assertRaises(perm.PermissionError,
                          self.perm.assert_permission, 'TRAC_ADMIN')

    def test_cache(self):
        self.perm.assert_permission('TEST_MODIFY')
        self.perm.assert_permission('TEST_ADMIN')
        self.perm_system.revoke_permission('testuser', 'TEST_ADMIN')
        # Using cached GRANT here
        self.perm.assert_permission('TEST_ADMIN')

    def test_cache_shared(self):
        # we need to start with an empty cache here (#7201)
        perm1 = perm.PermissionCache(self.env, 'testcache')
        perm1 = perm1('ticket', 1)
        perm2 = perm1('ticket', 1) # share internal cache
        self.perm_system.grant_permission('testcache', 'TEST_ADMIN')
        perm1.assert_permission('TEST_ADMIN')
        self.perm_system.revoke_permission('testcache', 'TEST_ADMIN')
        # Using cached GRANT here (from shared cache)
        perm2.assert_permission('TEST_ADMIN')

    def test_has_permission_on_resource_none(self):
        """'PERM' in perm(None) should cache the same value as
        'PERM' in perm(None) (#12597).
        """
        'TEST_ADMIN' in self.perm
        self.assertEqual(1, len(self.perm._cache))
        'TEST_ADMIN' in self.perm(None)
        self.assertEqual(1, len(self.perm._cache))


class TestPermissionPolicy(Component):
    implements(perm.IPermissionPolicy)

    def __init__(self):
        self.allowed = {}
        self.results = {}

    def grant(self, username, permissions):
        self.allowed.setdefault(username, set()).update(permissions)

    def revoke(self, username, permissions):
        self.allowed.setdefault(username, set()).difference_update(permissions)

    def check_permission(self, action, username, resource, perm):
        result = action in self.allowed.get(username, set()) or None
        self.results[(username, action)] = result
        return result


class PermissionPolicyTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=[perm.DefaultPermissionStore,
                                           perm.DefaultPermissionPolicy,
                                           TestPermissionPolicy,
                                           TestPermissionRequestor])
        self.env.config.set('trac', 'permission_policies',
                            'TestPermissionPolicy')
        self.policy = TestPermissionPolicy(self.env)
        self.perm = perm.PermissionCache(self.env, 'testuser')

    def tearDown(self):
        self.env.reset_db()

    def test_no_permissions(self):
        self.assertRaises(perm.PermissionError,
                          self.perm.assert_permission, 'TEST_MODIFY')
        self.assertRaises(perm.PermissionError,
                          self.perm.assert_permission, 'TEST_ADMIN')
        self.assertEqual(self.policy.results,
                         {('testuser', 'TEST_MODIFY'): None,
                          ('testuser', 'TEST_ADMIN'): None})

    def test_grant_revoke_permissions(self):
        self.policy.grant('testuser', ['TEST_MODIFY', 'TEST_ADMIN'])
        self.assertIn('TEST_MODIFY', self.perm)
        self.assertIn('TEST_ADMIN', self.perm)
        self.assertEqual(self.policy.results,
                         {('testuser', 'TEST_MODIFY'): True,
                          ('testuser', 'TEST_ADMIN'): True})

    def test_policy_chaining(self):
        self.env.config.set('trac', 'permission_policies',
                            'TestPermissionPolicy,DefaultPermissionPolicy')
        self.policy.grant('testuser', ['TEST_MODIFY'])
        system = perm.PermissionSystem(self.env)
        system.grant_permission('testuser', 'TEST_ADMIN')

        self.assertEqual(list(system.policies),
                         [self.policy,
                          perm.DefaultPermissionPolicy(self.env)])
        self.assertIn('TEST_MODIFY', self.perm)
        self.assertIn('TEST_ADMIN', self.perm)
        self.assertEqual(self.policy.results,
                         {('testuser', 'TEST_MODIFY'): True,
                          ('testuser', 'TEST_ADMIN'): None})


class RecursivePolicyTestCase(unittest.TestCase):
    """Test case for policies that perform recursive permission checks."""

    def setUp(self):
        self.env = EnvironmentStub()
        self.env.clear_component_registry()
        decisions = []
        self.decisions = decisions

        class PermissionPolicy1(Component):

            implements(perm.IPermissionPolicy)

            def __init__(self):
                self.call_count = 0

            def check_permission(self, action, username, resource, perm):
                self.call_count += 1
                decision = None
                if 'ACTION_2' in perm(resource):
                    decision = None
                elif action == 'ACTION_1':
                    decision = username == 'user1'
                decisions.append(('policy1', action, decision))
                return decision

        class PermissionPolicy2(Component):

            implements(perm.IPermissionPolicy)

            def __init__(self):
                self.call_count = 0

            def check_permission(self, action, username, resource, perm):
                self.call_count += 1
                decision = None
                if action == 'ACTION_2':
                    decision = username == 'user2'
                decisions.append(('policy2', action, decision))
                return decision

        self.env.enable_component(PermissionPolicy1)
        self.env.enable_component(PermissionPolicy2)
        self.env.config.set('trac', 'permission_policies',
                            'PermissionPolicy1, PermissionPolicy2')
        self.ps = perm.PermissionSystem(self.env)

    def tearDown(self):
        self.env.restore_component_registry()
        self.env.reset_db()

    def test_user1_allowed_by_policy1(self):
        """policy1 consulted for ACTION_1. policy1 and policy2 consulted
        for ACTION_2.
        """
        perm_cache = perm.PermissionCache(self.env, 'user1')
        self.assertIn('ACTION_1', perm_cache)
        self.assertEqual(2, self.ps.policies[0].call_count)
        self.assertEqual(1, self.ps.policies[1].call_count)
        self.assertEqual([
            ('policy1', 'ACTION_2', None),
            ('policy2', 'ACTION_2', False),
            ('policy1', 'ACTION_1', True),
        ], self.decisions)

    def test_user2_denied_by_no_decision(self):
        """policy1 and policy2 consulted for ACTION_1. policy1 and
        policy2 consulted for ACTION_2.
        """
        perm_cache = perm.PermissionCache(self.env, 'user2')
        self.assertNotIn('ACTION_1', perm_cache)
        self.assertEqual(2, self.ps.policies[0].call_count)
        self.assertEqual(2, self.ps.policies[1].call_count)
        self.assertEqual([
            ('policy1', 'ACTION_2', None),
            ('policy2', 'ACTION_2', True),
            ('policy1', 'ACTION_1', None),
            ('policy2', 'ACTION_1', None),
        ], self.decisions)

    def test_user1_denied_by_policy2(self):
        """policy1 consulted for ACTION_2. policy2 consulted for ACTION_2.
        """
        perm_cache = perm.PermissionCache(self.env, 'user1')
        self.assertNotIn('ACTION_2', perm_cache)
        self.assertEqual(1, self.ps.policies[0].call_count)
        self.assertEqual(1, self.ps.policies[1].call_count)
        self.assertEqual([
            ('policy1', 'ACTION_2', None),
            ('policy2', 'ACTION_2', False),
        ], self.decisions)

    def test_user1_allowed_by_policy2(self):
        """policy1 consulted for ACTION_2. policy2 consulted for ACTION_2.
        """
        perm_cache = perm.PermissionCache(self.env, 'user2')
        self.assertIn('ACTION_2', perm_cache)
        self.assertEqual(1, self.ps.policies[0].call_count)
        self.assertEqual(1, self.ps.policies[1].call_count)
        self.assertEqual([
            ('policy1', 'ACTION_2', None),
            ('policy2', 'ACTION_2', True),
        ], self.decisions)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DefaultPermissionStoreTestCase))
    suite.addTest(unittest.makeSuite(PermissionErrorTestCase))
    suite.addTest(unittest.makeSuite(PermissionSystemTestCase))
    suite.addTest(unittest.makeSuite(PermissionCacheTestCase))
    suite.addTest(unittest.makeSuite(PermissionPolicyTestCase))
    suite.addTest(unittest.makeSuite(RecursivePolicyTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
