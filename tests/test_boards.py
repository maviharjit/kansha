# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import json
import unittest

from elixir import metadata as __metadata__
from nagare import database

from kansha.board.models import DataBoard
from kansha.board import comp as board_module
from kansha.board import boardsmanager
from kansha.user import user_profile
from kansha import notifications
from . import helpers

database.set_metadata(__metadata__, 'sqlite:///:memory:', False, {})


class BoardTest(unittest.TestCase):

    def setUp(self):
        helpers.setup_db(__metadata__)
        services = helpers.create_services()
        self.boards_manager = boardsmanager.BoardsManager('', '', '', {}, None, services)

    def tearDown(self):
        helpers.teardown_db(__metadata__)

    def test_add_board(self):
        """Create a new board"""
        helpers.set_dummy_context()
        self.assertEqual(DataBoard.query.count(), 0)
        helpers.create_board()
        self.assertEqual(DataBoard.query.filter_by(is_template=False).count(), 1)

    def test_add_column_ok(self):
        """Add a column to a board"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        self.assertIsNotNone(board.archive_column)
        self.assertEqual(board.count_columns(), 3)
        board.create_column(0, helpers.word())
        self.assertEqual(board.count_columns(), 4)

    def test_add_column_ko(self):
        """Add a column with empty title to a board"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        self.assertEqual(board.count_columns(), 3)
        self.assertFalse(board.create_column(0, ''))

    def test_delete_column(self):
        """Delete column from a board"""
        helpers.set_dummy_context()
        user = helpers.create_user()
        helpers.set_context(user)
        board = helpers.create_board()
        self.assertIsNotNone(board.archive_column)
        self.assertEqual(board.count_columns(), 3)
        column_id = board.columns[0]().db_id
        board.delete_column(column_id)
        self.assertEqual(board.count_columns(), 2)

    def test_set_visibility_1(self):
        """Test set visibility method 1

        Initial State:
         - board:private
         - allow_comment: off
         - allow_votes: members

        End state
         - board:public
         - allow_comment: off
         - allow_votes: members
        """
        helpers.set_dummy_context()
        board = helpers.create_board()
        board.data.visibility = 0
        board.data.comments_allowed = 0
        board.data.votes_allowed = 1

        board.set_visibility(board_module.BOARD_PUBLIC)

        self.assertEqual(board.data.visibility, 1)
        self.assertEqual(board.data.comments_allowed, 0)
        self.assertEqual(board.data.votes_allowed, 1)

    def test_set_visibility_2(self):
        """Test set visibility method 2

        Initial State:
         - board:public
         - allow_comment: public
         - allow_votes: public

        End state
         - board:private
         - allow_comment: members
         - allow_votes: members
        """
        helpers.set_dummy_context()
        board = helpers.create_board()
        board.data.visibility = 1
        board.data.comments_allowed = 2
        board.data.votes_allowed = 2

        board.set_visibility(board_module.BOARD_PRIVATE)

        self.assertEqual(board.data.visibility, 0)
        self.assertEqual(board.data.comments_allowed, 1)
        self.assertEqual(board.data.votes_allowed, 1)

    def test_set_visibility_3(self):
        """Test set visibility method 3

        Initial State:
         - board:public
         - allow_comment: members
         - allow_votes: off

        End state
         - board:private
         - allow_comment: members
         - allow_votes: off
        """
        helpers.set_dummy_context()
        board = helpers.create_board()
        board.data.visibility = 1
        board.data.comments_allowed = 1
        board.data.votes_allowed = 0

        board.set_visibility(board_module.BOARD_PRIVATE)

        self.assertEqual(board.data.visibility, 0)
        self.assertEqual(board.data.comments_allowed, 1)
        self.assertEqual(board.data.votes_allowed, 0)

    def test_save_as_template(self):
        title = helpers.word()
        description = helpers.word()
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user()
        helpers.set_context(user)
        template = board.save_as_template(title, description, False)
        self.assertEqual(template.data.title, title)
        self.assertEqual(template.data.description, description)
        self.assertTrue(template.data.is_template)
        self.assertEqual(template.data.visibility, board_module.BOARD_PRIVATE)
        template = board.save_as_template(title, description, True)
        self.assertEqual(template.data.visibility, board_module.BOARD_PUBLIC)

    def test_switch_view(self):
        board = helpers.create_board()
        self.assertEqual(board.model, 'columns')
        board.switch_view()
        self.assertEqual(board.model, 'calendar')
        board.switch_view()
        self.assertEqual(board.model, 'columns')

    def test_has_member_1(self):
        """Test has member 1"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user()
        helpers.set_context(user)
        data = board.data  # don't collect
        members = data.members
        members.append(user.data)
        self.assertTrue(board.has_member(user))

    def test_has_member_2(self):
        """Test has member 2"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        user_2 = helpers.create_user(suffixe='2')
        data = board.data  # don't collect
        data.managers.append(user_2.data)
        self.assertFalse(board.has_member(user))

    def test_has_manager_1(self):
        """Test has manager 1"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        self.assertFalse(board.has_manager(user))
        user.data.managed_boards.append(board.data)
        user.data.boards.append(board.data)
        self.assertTrue(board.has_manager(user))

    def test_has_manager_2(self):
        """Test has manager 2"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        user_2 = helpers.create_user(suffixe='2')
        self.assertFalse(board.has_manager(user))
        data = board.data  # don't collect
        data.managers.append(user_2.data)
        data.members.append(user_2.data)
        database.session.flush()
        self.assertFalse(board.has_manager(user))

    def test_add_member_1(self):
        """Test add member"""
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('bis')
        helpers.set_context(user)
        self.assertFalse(board.has_member(user))
        board.add_member(user)
        self.assertTrue(board.has_member(user))

    def test_change_role(self):
        '''Test change role'''
        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user('test')
        board.add_member(user)
        board.update_members()

        def find_board_member():
            for member in board.all_members:
                if member().get_user_data().username == user.username:
                    return member()

        member = find_board_member()
        self.assertEqual(len(board.members), 1)
        self.assertEqual(len(board.managers), 1)

        member.dispatch('toggle_role', '')
        member = find_board_member()
        board.update_members()
        self.assertEqual(len(board.members), 0)
        self.assertEqual(len(board.managers), 2)

        member.dispatch('toggle_role', '')
        board.update_members()
        self.assertEqual(len(board.members), 1)
        self.assertEqual(len(board.managers), 1)

    def test_get_boards(self):
        '''Test get boards methods'''

        helpers.set_dummy_context()
        board = helpers.create_board()
        user = helpers.create_user()
        user2 = helpers.create_user('bis')
        board.add_member(user2, 'member')
        self.assertTrue(board.has_manager(user))
        self.assertFalse(board.has_manager(user2))

        helpers.set_context(user)
        user_boards = user_profile.UserBoards('', '', '', {}, user.get_user_data(), None, None, helpers.create_services())
        self.assertIn(board.id, user_boards.last_modified_boards)
        self.assertNotIn(board.id, user_boards.guest_boards)
        self.assertIn(board.id, user_boards.my_boards)
        self.assertNotIn(board.id, user_boards.archived_boards)

        helpers.set_context(user2)
        user_boards = user_profile.UserBoards('', '', '', {}, user2.get_user_data(), None, None, helpers.create_services())
        self.assertIn(board.id, user_boards.last_modified_boards)
        self.assertIn(board.id, user_boards.guest_boards)
        self.assertNotIn(board.id, user_boards.my_boards)
        self.assertNotIn(board.id, user_boards.archived_boards)

        board.archive_board()
        user_boards.reload_boards()
        self.assertIn(board.id, user_boards.archived_boards)

    def test_get_by(self):
        '''Test get_by_uri and get_by_id methods'''
        helpers.set_dummy_context()
        orig_board = helpers.create_board()
        board = self.boards_manager.get_by_id(orig_board.id)
        self.assertEqual(orig_board.data.id, board.data.id)
        self.assertEqual(orig_board.data.title, board.data.title)
        board = self.boards_manager.get_by_uri(orig_board.data.uri)
        self.assertEqual(orig_board.data.id, board.data.id)
        self.assertEqual(orig_board.data.title, board.data.title)
