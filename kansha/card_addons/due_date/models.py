# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from elixir import using_options
from elixir import ManyToOne
from elixir import Field, Date

from kansha.models import Entity


class DataCardDueDate(Entity):
    using_options(tablename='card_due_date')

    due_date = Field(Date, default=u'')
    card = ManyToOne('DataCard')

    @classmethod
    def get_data_by_card(cls, card):
        q = cls.query
        q = q.filter_by(card=card)
        return q.first()
