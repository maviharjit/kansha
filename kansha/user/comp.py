# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import pkg_resources
import peak.rules

from nagare import presentation, component, i18n
from nagare.security import common as security_common
from nagare.i18n import _

from . import usermanager
from ..models import DataToken


class User(security_common.User):

    """User component"""

    def __init__(self, username, *args, **kw):
        """Initialization

        In:
            - ``username`` -- the id of the user
        """
        super(User, self).__init__(username, *args)
        self.username = username
        self._data = kw.get('data')

    @property
    def data(self):
        """Return the user object from database
        """
        if not self._data:
            self._data = usermanager.UserManager().get_by_username(self.username)
        return self._data

    def __getstate__(self):
        self._data = None
        return self.__dict__

    def get_user_data(self):
        return self.data

    @property
    def email(self):
        return self.data.email

    @property
    def is_local(self):
        """Test if it's a application user

        Return:
         - True if user is an application user
        """
        return self.data.source == 'application'

    def get_locale(self):
        if self.data.language == 'fr':
            return i18n.Locale('fr', 'FR')
        return i18n.Locale('en', 'US')

    def update_password(self, new_password):
        """Update the password of the connected user

        In:
         - ``new_password`` -- the new password
        """
        self.set_id(self.username, new_password)

    def set_last_board(self, board):
        """Update last board used

        In;
         - ``board`` -- last board used
        """
        self.data.last_board = board.data

    def get_last_board(self):
        """Return last used board

        In;
         - ``board`` -- last board used
        """
        return self.data.last_board

    def has_avatar(self):
        """Return True if user have an avatar

        Return:
         - True if user have an avatar
        """
        return self.data.picture is not None

    def get_avatar(self):
        """Return picture

        Return:
         - URL or URI of the picture
        """
        return self.data.get_picture()

    @property
    def initials(self):
        """ Return user's intials

        Return:
         - a string with initials made with user full name
        """
        return ''.join([n[0].upper() for n in self.data.fullname.split()])

    def best_friends(self, exclude_list=(), size=None):
        """ Return user's friends

        Return users which have most boards in common with user

        In:
         - ``size`` -- list size (None for all)
        Return:
         - list of Users (User Instances)
        """
        return self.data.best_friends(exclude_list, size)

    def add_board(self, board, role="member"):
        """Add board to user's board lists

        In:
         - ``board`` -- DataBoard instance to add
         - ``role`` -- user is member or manager
        """
        self.data.add_board(board, role)

    def is_manager(self, board):
        """Return True if user is manager of the board

        In:
         - ``board`` -- DataBoard instance
        Return:
         - True if user is manager of the board
        """
        return board in self.data.managed_boards


@peak.rules.when(usermanager.get_user_class, """source == 'application'""")
def get_user_class(source):
    return User


class PendingUser(object):

    """ Class for pending user of a board

    Store token id, to get the invited user
    """

    def __init__(self, token_id):
        self.token_id = token_id

    @property
    def data(self):
        return DataToken.get(self.token_id)

    @property
    def username(self):
        return self.data.username

    @property
    def email(self):
        return self.data.username
