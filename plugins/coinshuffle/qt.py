#!/usr/bin/env python
#
# Electrum - Lightweight Bitcoin Client
# Copyright (C) 2015 Thomas Voegtlin
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import

import time
import threading
import base64
from functools import partial

# from PyQt5.QtGui import *
# from PyQt5.QtCore import *
# import PyQt5.QtCore as QtCore
# import PyQt5.QtGui as QtGui
# from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QGridLayout, QLineEdit)

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
# from PyQt4.QtWidgets import (QVBoxLayout, QLabel, QGridLayout, QLineEdit)
from PyQt4.QtGui import (QVBoxLayout, QLabel, QGridLayout, QLineEdit)


from electroncash.plugins import BasePlugin, hook
# from electroncash.paymentrequest import PaymentRequest
from electroncash.i18n import _
from electroncash_gui.qt.util import EnterButton, Buttons, CloseButton
from electroncash_gui.qt.util import OkButton, WindowModalDialog

class Plugin(BasePlugin):

    def fullname(self):
        return 'CoinShuffle'

    def description(self):
        return _("Configure Coinshuffle Protocol")

    def is_available(self):
        return True

    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)
        self.server = self.config.get('coinshuffleserver', '')
        # self.username = self.config.get('user', '')
        # self.password = self.config.get('password', '')

    def requires_settings(self):
        return True

    def settings_widget(self, window):
        return EnterButton(_('Settings'), partial(self.settings_dialog, window))

    def settings_dialog(self, window):
        d = WindowModalDialog(window, _("Coinshuffle settings"))
        d.setMinimumSize(500, 200)

        vbox = QVBoxLayout(d)
        vbox.addWidget(QLabel(_('Coinshuffle server')))
        grid = QGridLayout()
        vbox.addLayout(grid)
        grid.addWidget(QLabel('server'), 0, 0)
        server_e = QLineEdit()
        server_e.setText(self.server)
        grid.addWidget(server_e, 0, 1)

        # grid.addWidget(QLabel('user'), 1, 0)
        # username_e = QLineEdit()
        # username_e.setText(self.username)
        # grid.addWidget(username_e, 1, 1)
        #
        # grid.addWidget(QLabel('password'), 2, 0)
        # password_e = QLineEdit()
        # password_e.setText(self.password)
        # grid.addWidget(password_e, 2, 1)

        vbox.addStretch()
        vbox.addLayout(Buttons(CloseButton(d), OkButton(d)))

        if not d.exec_():
            return

        server = str(server_e.text())
        self.config.set_key('coinshuffleserver', server)

        # username = str(username_e.text())
        # self.config.set_key('user', username)
        #
        # password = str(password_e.text())
        # self.config.set_key('password', password)
