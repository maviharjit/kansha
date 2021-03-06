# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from .board.models import create_template_empty, create_template_todo


def populate():
    """Populate database
    """
    create_template_empty()
    create_template_todo()
