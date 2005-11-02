# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2005 Edgewall Software
# Copyright (C) 2005 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Christopher Lenz <cmlenz@gmx.de>

from __future__ import generators
from trac.perm import PermissionError
from trac.core import *

### Source Configuration Management interface and manager

class IScmBackend(Interface):
    """SCM backend for Trac"""

    def identifiers(self):
        """SCM string prefixes that are supported by the backend,
        and their relative priorities.

        Highest number is highest priority.
        """

    def repository(self, scheme, args, authname):
        """Get a Repository object.

        `scheme` is the scheme that was used to select this backend,
        `args` is the remaining specification for the repository and
        `authname` is the user name, for authentication purpose.
        """

    def init_repository(self, **params): # TBD
        """Initialize a repository"""


class ScmBackendManager(Component):
    """TODO: share some code with the DatabaseBackendManager"""

    backends = ExtensionPoint(IScmBackend)

    def __init__(self):
        self._backend_map = None

    def get_repository(self, repos_str, authname):
        if ':' in repos_str and len(repos_str) > 2 and repos_str[1] != ':':
            scheme, args = repos_str.split(':', 1)
        else:
            scheme, args = 'svn', repos_str
        backend = self._get_backend(scheme)
        return backend.repository(scheme, args, authname)

    def _get_backend(self, scheme):
        if not self._backend_map:
            self._backend_map = {}
            for backend in self.backends:
                for ident, prio in backend.identifiers():
                    if ident in self._backend_map:
                        highest = self._backend_map[ident][1]
                    else:
                        highest = 0
                    if prio > highest:
                        self._backend_map[ident] = (backend, prio)
        if not scheme in self._backend_map:
            raise TracError, 'Unsupported SCM "%s"' % scheme
        return self._backend_map[scheme][0]


### Abstract classes for the backends

class Repository(object):
    """
    Base class for a repository provided by a version control system.
    """

    def __init__(self, name, authz, log):
        self.name = name
        self.authz = authz or Authorizer()
        self.log = log

    def close(self):
        """
        Close the connection to the repository.
        """
        raise NotImplementedError

    def get_changeset(self, rev):
        """
        Retrieve a Changeset object that describes the changes made in
        revision 'rev'.
        """
        raise NotImplementedError

    def has_node(self, path, rev):
        """
        Tell if there's a node at the specified (path,rev) combination.
        """
        try:
            self.get_node()
            return True
        except TracError:
            return False        
    
    def get_node(self, path, rev=None):
        """
        Retrieve a Node (directory or file) from the repository at the
        given path. If the rev parameter is specified, the version of the
        node at that revision is returned, otherwise the latest version
        of the node is returned.
        """
        raise NotImplementedError

    def get_oldest_rev(self):
        """
        Return the oldest revision stored in the repository.
        """
        raise NotImplementedError
    oldest_rev = property(lambda x: x.get_oldest_rev())

    def get_youngest_rev(self):
        """
        Return the youngest revision in the repository.
        """
        raise NotImplementedError
    youngest_rev = property(lambda x: x.get_youngest_rev())

    def previous_rev(self, rev):
        """
        Return the revision immediately preceding the specified revision.
        """
        raise NotImplementedError

    def next_rev(self, rev):
        """
        Return the revision immediately following the specified revision.
        """
        raise NotImplementedError

    def rev_older_than(self, rev1, rev2):
        """
        Return True if rev1 is older than rev2, i.e. if rev1 comes before rev2
        in the revision sequence.
        """
        raise NotImplementedError

    def get_youngest_rev_in_cache(self, db):
        """
        Return the youngest revision currently cached.
        The way revisions are sequenced is version control specific.
        By default, one assumes that the revisions are sequenced in time.
        """
        cursor = db.cursor()
        cursor.execute("SELECT rev FROM revision ORDER BY time DESC LIMIT 1")
        row = cursor.fetchone()
        return row and row[0] or None

    def get_path_history(self, path, rev=None, limit=None):
        """
        Retrieve all the revisions containing this path (no newer than 'rev').
        The result format should be the same as the one of Node.get_history()
        """
        raise NotImplementedError

    def normalize_path(self, path):
        """
        Return a canonical representation of path in the repos.
        """
        return NotImplementedError

    def normalize_rev(self, rev):
        """
        Return a canonical representation of a revision in the repos.
        'None' is a valid revision value and represents the youngest revision.
        """
        return NotImplementedError

    def short_rev(self, rev):
        """
        Return a compact representation of a revision in the repos.
        """
        return self.normalize_rev(rev)
        

class Node(object):
    """
    Represents a directory or file in the repository.
    """

    DIRECTORY = "dir"
    FILE = "file"

    def __init__(self, path, rev, kind):
        assert kind in (Node.DIRECTORY, Node.FILE), "Unknown node kind %s" % kind
        self.path = str(path)
        self.rev = rev
        self.kind = kind

    def get_content(self):
        """
        Return a stream for reading the content of the node. This method
        will return None for directories. The returned object should provide
        a read([len]) function.
        """
        raise NotImplementedError

    def get_entries(self):
        """
        Generator that yields the immediate child entries of a directory, in no
        particular order. If the node is a file, this method returns None.
        """
        raise NotImplementedError

    def get_history(self, limit=None):
        """
        Generator that yields (path, rev, chg) tuples, one for each revision in which
        the node was changed. This generator will follow copies and moves of a
        node (if the underlying version control system supports that), which
        will be indicated by the first element of the tuple (i.e. the path)
        changing.
        Starts with an entry for the current revision.
        """
        raise NotImplementedError

    def get_properties(self):
        """
        Returns a dictionary containing the properties (meta-data) of the node.
        The set of properties depends on the version control system.
        """
        raise NotImplementedError

    def get_content_length(self):
        raise NotImplementedError
    content_length = property(lambda x: x.get_content_length())

    def get_content_type(self):
        raise NotImplementedError
    content_type = property(lambda x: x.get_content_type())

    def get_name(self):
        return self.path.split('/')[-1]
    name = property(lambda x: x.get_name())

    def get_last_modified(self):
        raise NotImplementedError
    last_modified = property(lambda x: x.get_last_modified())

    isdir = property(lambda x: x.kind == Node.DIRECTORY)
    isfile = property(lambda x: x.kind == Node.FILE)


class Changeset(object):
    """
    Represents a set of changes of a repository.
    """

    ADD = 'add'
    COPY = 'copy'
    DELETE = 'delete'
    EDIT = 'edit'
    MOVE = 'move'

    def __init__(self, rev, message, author, date):
        self.rev = rev
        self.message = message
        self.author = author
        self.date = date

    def get_changes(self):
        """
        Generator that produces a (path, kind, change, base_rev, base_path)
        tuple for every change in the changeset, where change can be one of
        Changeset.ADD, Changeset.COPY, Changeset.DELETE, Changeset.EDIT or
        Changeset.MOVE, and kind is one of Node.FILE or Node.DIRECTORY.
        """
        raise NotImplementedError


class PermissionDenied(PermissionError):
    """
    Exception raised by an authorizer if the user has insufficient permissions
    to view a specific part of the repository.
    """
    def __str__(self):
        return self.action


class Authorizer(object):
    """
    Base class for authorizers that are responsible to granting or denying
    access to view certain parts of a repository.
    """

    def assert_permission(self, path):
        if not self.has_permission(path):
            raise PermissionDenied, \
                  'Insufficient permissions to access %s' % path

    def assert_permission_for_changeset(self, rev):
        if not self.has_permission_for_changeset(rev):
            raise PermissionDenied, \
                  'Insufficient permissions to access changeset %s' % rev

    def has_permission(self, path):
        return 1
    
    def has_permission_for_changeset(self, rev):
        return 1

