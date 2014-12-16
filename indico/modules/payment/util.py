# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
from indico.core.db import db
from indico.core.plugins import plugin_engine
from indico.modules.payment import PaymentPluginMixin
from indico.modules.payment.notifications import notify_double_payment
from indico.modules.payment.models.transactions import PaymentTransaction

remove_prefix_re = re.compile('^payment_')


def get_payment_plugins():
    """Returns a dict containing the available payment plugins."""
    return {remove_prefix_re.sub('', p.name): p for p in plugin_engine.get_active_plugins().itervalues()
            if isinstance(p, PaymentPluginMixin)}


def get_active_payment_plugins(event):
    """Returns a dict containing the active payment plugins of an event."""
    return {name: plugin for name, plugin in get_payment_plugins().iteritems()
            if plugin.event_settings.get(event, 'enabled')}


def register_transaction(event_id, registrant_id, amount, currency, action, provider=None, data=None):
    new_transaction, double_payment = PaymentTransaction.create_next(event_id=event_id, registrant_id=registrant_id,
                                                                     amount=amount, currency=currency, action=action,
                                                                     provider=provider, data=data)
    if new_transaction:
        db.session.add(new_transaction)
        db.session.flush()
        if double_payment:
            notify_double_payment(event_id, registrant_id)
        return new_transaction
