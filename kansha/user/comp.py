# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from datetime import datetime

from nagare import i18n
from nagare.security import common as security_common

from .models import DataToken, DataUser


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
            self._data = DataUser.get_by_username(self.username)
        return self._data

    def __getstate__(self):
        self._data = None
        return self.__dict__

    def __eq__(self, other):
        return self.username == other.username

    @property
    def email(self):
        return self.data.email

    @property
    def source(self):
        return self.data.source

    @property
    def is_local(self):
        """Test if it's a application user

        Return:
         - True if user is an application user
        """
        return self.data.source == 'application'

    def get_locale(self):
        if self.data.language == 'fr':
            locale = i18n.Locale('fr', 'FR')
        else:
            locale = i18n.Locale('en', 'US')

        # At this point, the locale object only knows about builtin Nagare translation directories
        # We need to register Kansha's translation directories too (get them from the current locale)
        locale.translation_directories.update(i18n.get_locale().translation_directories)

        return locale

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

    def get_avatar(self):
        """Return picture

        Return:
         - URL or URI of the picture
        """
        return self.data.get_picture()

    @property
    def fullname(self):
        return self.data.fullname

    @property
    def last_login(self):
        return self.data.last_login

    def update_last_login(self):
        self.data.last_login = datetime.utcnow()


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
