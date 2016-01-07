# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import dateutil.parser

from peak.rules import when

from nagare.i18n import _
from nagare import component, security

from kansha import title
from kansha import events
from kansha.services.actionlog.messages import render_event

from .models import DataCard


class NewCard(object):

    """New card component
    """

    def __init__(self, column):
        self.column = column
        self.needs_refresh = False

    def toggle_refresh(self):
        self.needs_refresh = not self.needs_refresh


class Card(events.EventHandlerMixIn):

    """Card component
    """

    def __init__(self, id_, column, card_extensions, action_log, services_service, data=None):
        """Initialization

        In:
            - ``id_`` -- the id of the card in the database
            - ``column`` -- father
        """
        self.db_id = id_
        self.id = 'card_' + str(self.db_id)
        self.column = column # still used by extensions, not by the card itself
        self.card_extensions = card_extensions
        self.action_log = action_log.for_card(self)
        self._services = services_service
        self._data = data
        self.extensions = ()
        self.refresh()

    def copy(self, parent, additional_data):
        new_data = self.data.copy(parent.data)
        new_card = self._services(Card, new_data.id, parent, {}, parent.action_log, data=new_data)
        new_card.extensions = [(name, component.Component(extension().copy(new_card, additional_data)))
                               for name, extension in self.extensions]
        return new_card


    def refresh(self):
        """Refresh the sub components
        """
        self.title = component.Component(
            title.EditableTitle(self.get_title)).on_answer(self.set_title)
        self.extensions = [(name, component.Component(self._services(extension, self, self.action_log)))
                                for name, extension in self.card_extensions.items()]

    @property
    def data(self):
        """Return the card object from the database
        """
        if self._data is None:
            self._data = DataCard.get(self.db_id)
        return self._data

    def __getstate__(self):
        self._data = None
        return self.__dict__

    @property
    def archived(self):
        return self.data.archived

    @property
    def index(self):
        return self.data.index

    def set_title(self, title):
        """Set title

        In:
            - ``title`` -- new title
        """
        values = {'from': self.data.title, 'to': title}
        self.action_log.add_history(security.get_user(), u'card_title', values)
        self.data.title = title

    def get_title(self):
        """Get title

        Return :
            - the card title
        """
        return self.data.title

    def delete(self):
        """Prepare for deletion"""
        for __, extension in self.extensions:
            extension().delete()

    def card_dropped(self, request, response):
        """
        Dropped on new date (calendar view).
        """
        start = dateutil.parser.parse(request.GET['start']).date()
        for __, extension in self.extensions:
            extension().new_card_position(start)

    def emit_event(self, comp, kind, data=None):
        if kind == events.PopinClosed:
            kind = events.CardEditorClosed
        return super(Card, self).emit_event(comp, kind, data)

    ################################
    # Feature methods, persistency #
    ################################

    @property
    def board(self):  # still needed by some extensions, no the card itself.
        return self.column.board

    # Members

    def get_available_users(self):
        """
        Return:
            - a set of user (UserData instance)
        """
        return set(self.column.get_available_users()) | set(self.column.get_pending_users()) - set(self.data.members)

    def add_member(self, new_data_member):
        data = self.data
        added = False
        if (new_data_member not in data.members and
                new_data_member in self.get_available_users()):
            data.members.append(new_data_member)
            added = True
        return added

    def remove_member(self, data_member):
        self.data.remove_member(data_member)

    @property
    def members(self):
        return self.data.members

    @property
    def favorites(self):
        """Return favorites users for a given card

        Ask favorites to self.column
        Store favorites in self._favorites to avoid CallbackLookupError

        Return:
            - list of favorites (usernames)
        """
        # to be optimized later if still exists
        member_usernames = set(member.username for member in self.members)
        # FIXME: don't reference parent
        board_user_stats = [(nb_cards, username) for username, nb_cards in self.column.favorites.iteritems()]
        board_user_stats.sort(reverse=True)
        # Take the 5 most popular that are not already affected to this card
        self._favorites = [username
                           for (__, username) in board_user_stats
                           if username not in member_usernames]
        return self._favorites[:5]

    def remove_board_member(self, member):
        """Member removed from board

        If member is linked to a card, remove it
        from the list of members

        In:
            - ``member`` -- Board Member instance to remove
        """
        self.data.remove_member(member.get_user_data())
        self.refresh()  # brute force solution until we have proper communication between extensions

    # Cover methods

    def make_cover(self, asset):
        """Make card cover with asset

        In:
            - ``asset`` -- New cover, Asset component
        """
        self.data.make_cover(asset)

    def has_cover(self):
        return self.data.cover is not None

    def get_cover(self):
        return self.data.cover

    def remove_cover(self):
        self.data.remove_cover()

    # Label methods

    def get_available_labels(self):
        return self.column.get_available_labels()

    def get_datalabels(self):
        return self.data.labels

    # Weight

    @property
    def weight(self):
        return self.data.weight

    @weight.setter
    def weight(self, value):
        values = {'from': self.data.weight, 'to': value, 'card': self.data.title}
        self.action_log.add_history(security.get_user(), u'card_weight', values)
        self.data.weight = value

    def weighting_on(self):
        return self.board.weighting_cards

    # Comments

    def get_comments(self):
        return self.data.comments

    # Description

    def get_description(self):
        return self.data.description

    def set_description(self, value):
        self.data.description = value

    # Due Date

    @property
    def due_date(self):
        return self.data.due_date

    @due_date.setter
    def due_date(self, value):
        self.data.due_date = value


############### Extension components ###################


@when(render_event, "action=='card_weight'")
def render_event_card_weight(action, data):
    return _(u'Card "%(card)s" has been weighted from (%(from)s) to (%(to)s)') % data


@when(render_event, "action=='card_add_member'")
def render_event_card_add_member(action, data):
    return _(u'User %(user)s has been assigned to card "%(card)s"') % data


@when(render_event, "action=='card_remove_member'")
def render_event_card_remove_member(action, data):
    return _(u'User %(user)s has been unassigned from card "%(card)s"') % data
