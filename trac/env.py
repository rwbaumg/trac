# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003, 2004, 2005 Edgewall Software
# Copyright (C) 2003, 2004, 2005 Jonas Borgstr�m <jonas@edgewall.com>
#
# Trac is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Trac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Author: Jonas Borgstr�m <jonas@edgewall.com>
# 

from __future__ import generators

from trac import db, db_default, util
from trac.config import Configuration
from trac.core import Component, ComponentManager, Interface, ExtensionPoint, \
                      TracError

import os
import os.path

db_version = db_default.db_version


class IEnvironmentSetupParticipant(Interface):
    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created():
        """Called when a new Trac environment is created."""


class Environment(Component, ComponentManager):
    """Trac stores project information in a Trac environment.

    A Trac environment consists of a directory structure containing among other
    things:
     * a configuration file.
     * an SQLite database (stores tickets, wiki pages...)
     * Project specific templates and wiki macros.
     * wiki and ticket attachments.
    """   
    setup_participants = ExtensionPoint(IEnvironmentSetupParticipant)

    def __init__(self, path, create=False, db_str=None):
        """Initialize the Trac environment.
        
        @param path:   the absolute path to the Trac environment
        @param create: if `True`, the environment is created and populated with
                       default data; otherwise, the environment is expected to
                       already exist.
        @param db_str: the database connection string
        """
        ComponentManager.__init__(self)

        try: # Use binary I/O on Windows
            import msvcrt, sys
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        except ImportError:
            pass

        self.path = path
        self.__cnx_pool = None
        if create:
            self.create(db_str)
        else:
            self.verify()
            self.load_config()
        self.setup_log()

        from trac.loader import load_components
        load_components(self)

        if create:
            for setup_participant in self.setup_participants:
                setup_participant.environment_created()

    def component_activated(self, component):
        """Initialize additional member variables for components.
        
        Every component activated through the `Environment` object gets three
        member variables: `env` (the environment object), `config` (the
        environment configuration) and `log` (a logger object)."""
        component.env = self
        component.config = self.config
        component.log = self.log

    def is_component_enabled(self, cls):
        """Implemented to only allow activation of components that are not
        disabled in the configuration.
        
        This is called by the `ComponentManager` base class when a component is
        about to be activated. If this method returns false, the component does
        not get activated."""
        component_name = (cls.__module__ + '.' + cls.__name__).lower()
        for name,value in self.config.options('disabled_components'):
            if value in util.TRUE and component_name.startswith(name):
                return False
        return True

    def verify(self):
        """Verify that the provided path points to a valid Trac environment
        directory."""
        fd = open(os.path.join(self.path, 'VERSION'), 'r')
        assert fd.read(26) == 'Trac Environment Version 1'
        fd.close()

    def get_db_cnx(self):
        """Return a database connection from the connection pool."""
        if not self.__cnx_pool:
            self.__cnx_pool = db.get_cnx_pool(self)
        return self.__cnx_pool.get_cnx()
    
    def shutdown(self):
        """Close the environment."""
        if self.__cnx_pool:
            self.__cnx_pool.shutdown()

    def get_repository(self, authname=None):
        """Return the version control repository configured for this
        environment.
        
        The repository is wrapped in a `CachedRepository`.
        
        @param authname: user name for authorization
        """
        from trac.versioncontrol.cache import CachedRepository
        from trac.versioncontrol.svn_authz import SubversionAuthorizer
        from trac.versioncontrol.svn_fs import SubversionRepository
        repos_dir = self.config.get('trac', 'repository_dir')
        if not repos_dir:
            raise EnvironmentError, 'Path to repository not configured'
        authz = None
        if authname:
            authz = SubversionAuthorizer(self, authname)
        repos = SubversionRepository(repos_dir, authz, self.log)
        return CachedRepository(self.get_db_cnx(), repos, authz, self.log)

    def create(self, db_str=None):
        """Create the basic directory structure of the environment, initialize
        the database and populate the configuration file with default values."""
        def _create_file(fname, data=None):
            fd = open(fname, 'w')
            if data: fd.write(data)
            fd.close()
        # Create the directory structure
        os.mkdir(self.path)
        os.mkdir(os.path.join(self.path, 'conf'))
        os.mkdir(self.get_log_dir())
        os.mkdir(self.get_attachments_dir())
        os.mkdir(self.get_templates_dir())
        os.mkdir(os.path.join(self.path, 'wiki-macros'))
        # Create a few files
        _create_file(os.path.join(self.path, 'VERSION'),
                     'Trac Environment Version 1\n')
        _create_file(os.path.join(self.path, 'README'),
                    'This directory contains a Trac project.\n'
                    'Visit http://trac.edgewall.com/ for more information.\n')
        _create_file(os.path.join(self.path, 'conf', 'trac.ini'))
        _create_file(os.path.join(self.get_templates_dir(), 'README'),
                     'This directory contains project-specific custom templates and style sheet.\n')
        _create_file(os.path.join(self.get_templates_dir(), 'site_header.cs'),
                     """<?cs
####################################################################
# Site header - Contents are automatically inserted above Trac HTML
?>
""")
        _create_file(os.path.join(self.get_templates_dir(), 'site_footer.cs'),
                     """<?cs
#########################################################################
# Site footer - Contents are automatically inserted after main Trac HTML
?>
""")
        _create_file(os.path.join(self.get_templates_dir(), 'site_css.cs'),
                     """<?cs
##################################################################
# Site CSS - Place custom CSS, including overriding styles here.
?>
""")

        # Setup the default configuration
        self.load_config()
        for section,name,value in db_default.default_config:
            self.config.set(section, name, value)
        self.config.set('trac', 'database', db_str)
        self.config.save()

        # Create the database
        cnx = db.init_db(self.path, db_str)
        self._insert_default_data(cnx)

    def _insert_default_data(self, db=None):
        """Insert default data into the database.

        @param db: the database connection; if ommitted, a new connection is
                   retrieved.
        """
        if not db:
            db = self.get_db_cnx()
        cursor = db.cursor()
        for table, cols, vals in db_default.data:
            cursor.executemany("INSERT INTO %s (%s) VALUES (%s)" % (table,
                               ','.join(cols), ','.join(['%s' for c in cols])),
                               vals)
        db.commit()

    def get_version(self):
        """Return the current version of the database."""
        cnx = self.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("SELECT value FROM system WHERE name='database_version'")
        row = cursor.fetchone()
        return row and int(row[0])

    def load_config(self):
        """Load the configuration file."""
        self.config = Configuration(os.path.join(self.path, 'conf', 'trac.ini'))
        for section,name,value in db_default.default_config:
            self.config.setdefault(section, name, value)

    def get_attachments_dir(self):
        """Return absolute path to the attachments directory."""
        return os.path.join(self.path, 'attachments')

    def get_templates_dir(self):
        """Return absolute path to the templates directory."""
        return os.path.join(self.path, 'templates')

    def get_log_dir(self):
        """Return absolute path to the log directory."""
        return os.path.join(self.path, 'log')

    def setup_log(self):
        """Initialize the logging sub-system."""
        from trac.log import logger_factory
        logtype = self.config.get('logging', 'log_type')
        loglevel = self.config.get('logging', 'log_level')
        logfile = self.config.get('logging', 'log_file')
        logfile = os.path.join(self.get_log_dir(), logfile)
        logid = self.path # Env-path provides process-unique ID
        self.log = logger_factory(logtype, logfile, loglevel, logid)

    def get_known_users(self, cnx=None):
        """Generator that yields information about all known users, i.e. users
        that have logged in to this Trac environment and possibly set their name
        and email.

        This function generates one tuple for every user, of the form
        (username, name, email) ordered alpha-numerically by username.

        @param cnx: the database connection; if ommitted, a new connection is
                    retrieved
        """
        if not cnx:
            cnx = self.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("SELECT DISTINCT s.sid, n.var_value, e.var_value "
                       "FROM session AS s "
                       " LEFT JOIN session AS n ON (n.sid=s.sid "
                       "  AND n.authenticated=1 AND n.var_name = 'name') "
                       " LEFT JOIN session AS e ON (e.sid=s.sid "
                       "  AND e.authenticated=1 AND e.var_name = 'email') "
                       "WHERE s.authenticated=1 ORDER BY s.sid")
        for username,name,email in cursor:
            yield username, name, email

    def backup(self, dest=None):
        """Simple SQLite-specific backup of the database.

        @param dest: Destination file; if not specified, the backup is stored in
                     a file called db_name.trac_version.bak
        """
        import shutil

        db_str = self.config.get('trac', 'database')
        if db_str[:7] != 'sqlite:':
            raise EnvironmentError, 'Can only backup sqlite databases'
        db_name = os.path.join(self.path, db_str[7:])
        if not dest:
            dest = '%s.%i.bak' % (db_name, self.get_version())
        shutil.copy (db_name, dest)

    def upgrade(self, backup=None, backup_dest=None):
        """Upgrade database.
        
        Each db version should have its own upgrade module, names
        upgrades/dbN.py, where 'N' is the version number (int).

        @param backup: whether or not to backup before upgrading
        @param backup_dest: name of the backup file
        @return: whether the upgrade was performed
        """
        dbver = self.get_version()
        if dbver == db_default.db_version:
            return upgrade_requestors
        elif dbver > db_default.db_version:
            raise TracError, 'Database newer than Trac version'
        else:
            if backup:
                self.backup(backup_dest)
            cnx = self.get_db_cnx()
            cursor = cnx.cursor()
            import upgrades
            for i in range(dbver + 1, db_default.db_version + 1):
                try:
                    upg  = 'db%i' % i
                    __import__('upgrades', globals(), locals(),[upg])
                    d = getattr(upgrades, upg)
                except AttributeError:
                    err = 'No upgrade module for version %i (%s.py)' % (i, upg)
                    raise TracError, err
                d.do_upgrade(self, i, cursor)
            cursor.execute("UPDATE system SET value=%s WHERE "
                           "name='database_version'", (db_default.db_version))
            self.log.info('Upgraded db version from %d to %d',
                          dbver, db_default.db_version)
            cnx.commit()
            return True


def open_environment(env_path=None):
    """Open an existing environment object, and verify that the database is up
    to date.

    @param: env_path absolute path to the environment directory; if ommitted,
            the value of the `TRAC_ENV` environment variable is used
    @return: the `Environment` object
    """
    if not env_path:
        env_path = os.getenv('TRAC_ENV')
    if not env_path:
        raise TracError, 'Missing environment variable "TRAC_ENV". Trac ' \
                         'requires this variable to point to a valid Trac ' \
                         'environment.'

    env = Environment(env_path)
    version = env.get_version()
    if version < db_version:
        raise TracError, 'The Trac Environment needs to be upgraded. Run ' \
                         'trac-admin %s upgrade"' % env_path
    elif version > db_version:
        raise TracError, 'Unknown Trac Environment version (%d).' % version
    return env
