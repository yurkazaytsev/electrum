#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from util import *
from electroncash.i18n import _
from electroncash_plugins.coinshuffle.client import protocolThread
from electroncash.bitcoin import regenerate_key
# from electroncash.bitcoin import is_address

# def start_protocol(parent, input_address, change_address, amount, fee, password = None):
#     if parent.wallet.has_password():
#         try:
#             password = parent.password_dialog(parent=parent)
#             if password is None:
#                 # User cancelled password input
#                 return
#
    # parent.coinshuffle_start_button.setEnabled(False)
    # print(input_address)
    # priv_key = parent.wallet.get_private_key(input_address, password )
    # sk = regenerate_key(priv_key)
    # addr_new = parent.wallet.create_new_address(False)
    # pThread = protocolThread("localhost", 8080, parent.network, amount, fee, sk, addr_new, change_address)
    # pThread.start()



class InputAdressWidget(QComboBox):

    def __init__(self, decimal_point, parent = None):
        QComboBox.__init__(self, parent)
        self.decimal_point = decimal_point

    def amounted_value(self, value):
        p = self.decimal_point()
        units = {2:"bits", 5:"mBCH", 8:"BCH"}
        if p not in  [2,5,8]:
            p = 8
        return str(value * (10**(- p))) + " " + units[p]


    def clear_addresses(self):
        self.inputsArray = []
        self.clear()

    def setItmes(self, wallet):
        self.inputsArray = wallet.get_utxos()
        for utxo in self.inputsArray:
            self.addItem(utxo.get('address')+': '+ self.amounted_value(utxo['value']))

    def get_input_address(self):
        return self.inputsArray[self.currentIndex()]['address']

    def get_input_value(self):
        return self.inputsArray[self.currentIndex()]['value']

# class ConsoleOutput(QLineEdit):
#
#     def __init__(self):
#         QLineEdit.__init__(self)
#         self.setText('Console output go here')
#         self.setReadOnly(True)
#
#     # this is for using is as a channel
#     def send(self, message):
#         self.setText(str(message))
#
#     # this is for using is as a channel
#     def put(self, message):
#         self.send(message)
class ConsoleLogger(QObject):
    logUpdater  = pyqtSignal(str)

    def send(self, message):
        self.logUpdater.emit(str(message))

    def put(self, message):
        self.send(message)

class ConsoleOutput(QTextEdit):

    def __init__(self,  parent = None):
        QTextEdit.__init__(self, parent)
        self.setReadOnly(True)
        self.setText('Console output go here')

class ChangeAdressWidget(QComboBox):

    # def __init__(self,parent = None):
    #     QComboBox.__init__(self)
    #     self.inputsArray = []

    def clear_addresses(self):
        self.ChangesArray = []
        self.clear()

    def setItmes(self, wallet):
        self.ChangesArray = wallet.get_change_addresses()
        self.addItem('Not use change address')
        for addr in self.ChangesArray:
            self.addItem(addr)

    def get_change_address(self):
        i = self.currentIndex()
        if i > 0:
            return self.ChangesArray[i-1]
        else:
            return None


class ShuffleList(MyTreeWidget):
    filter_columns = [0, 2]  # Address, Label

    def __init__(self, parent=None):
        MyTreeWidget.__init__(self, parent, self.create_menu, [ _('Address'), _('Label'), _('Amount'), _('Height'), _('Output point')], 1)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def get_name(self, x):
        return x.get('prevout_hash') + ":%d"%x.get('prevout_n')

    def on_update(self):
        limit = 1e5 #(in satoshis)
        self.wallet = self.parent.wallet
        item = self.currentItem()
        self.clear()
        self.utxos = self.wallet.get_utxos()
        for x in self.utxos:
            address = x.get('address')
            height = x.get('height')
            name = self.get_name(x)
            label = self.wallet.get_label(x.get('prevout_hash'))
            amount = self.parent.format_amount(x['value'])
            utxo_item = QTreeWidgetItem([address, label, amount, '%d'%height, name[0:10] + '...' + name[-2:]])
            utxo_item.setFont(0, QFont(MONOSPACE_FONT))
            utxo_item.setFont(4, QFont(MONOSPACE_FONT))
            utxo_item.setData(0, Qt.UserRole, name)
            if self.wallet.is_frozen(address):
                utxo_item.setBackground(0, QColor('lightblue'))
            # if float(amount) >= limit:
            if x['value'] >= limit:
                self.addChild(utxo_item)

    def create_menu(self, position):
        selected = [str(x.data(0, Qt.UserRole)) for x in self.selectedItems()]
        if not selected:
            return
        menu = QMenu()
        coins = filter(lambda x: self.get_name(x) in selected, self.utxos)

        # menu.addAction(_("Spend"), lambda: self.parent.spend_coins(coins))
        menu.addAction(_("Shuffle"), lambda: QMessageBox.information(self.parent,"1","2"))
        if len(selected) == 1:
            txid = selected[0].split(':')[0]
            tx = self.wallet.transactions.get(txid)
            menu.addAction(_("Details"), lambda: self.parent.show_transaction(tx))

        menu.exec_(self.viewport().mapToGlobal(position))
