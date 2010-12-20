# -*- coding: utf-8 -*-
#
# Caribou - text entry and UI navigation application
#
# Copyright (C) 2010 Eitan Isaacson <eitan@monotonous.org>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import caribou.common.const as const
from caribou.common.setting_types import *

import scan
import gconf
import gobject
import gtk
import pango
import sys
import virtkey
import os
import traceback
from i18n import _
try:
    import json
except ImportError:
    HAS_JSON = False
else:
    HAS_JSON = True
import xml.etree.ElementTree as ET
from xml.dom import minidom
import gettext
import i18n
from caribou.common.settings_manager import SettingsManager

class PreferencesWindow(gtk.Dialog):
    __gtype_name__ = "PreferencesWindow"

    def __init__(self):
        gtk.Dialog.__init__(self, _("Caribou Preferences"),
                            buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.set_border_width(6)

        notebook = gtk.Notebook()
        self.vbox.add(notebook)
        self._populate_settings(notebook, SettingsManager.groups)

    def _populate_settings(self, parent, setting, level=0):
        if level == 0:
            for s in setting:
                vbox = gtk.VBox()
                parent.append_page(vbox, gtk.Label(s.label))
                self._populate_settings(vbox, s, 1)
        else:
            parent.set_border_width(6)
            table = None
            row = 0
            for s in setting:
                if not isinstance(s, SettingsGroup):
                    if table is None:
                        table = gtk.Table(1, 2)
                        table.set_row_spacings(3)
                        table.set_col_spacings(3)
                        parent.pack_start(table, False, False, 0)
                    self._create_widget(table, row, s)
                    row += 1
                else:
                    table = None
                    frame = gtk.Frame()
                    frame.set_shadow_type(gtk.SHADOW_NONE)
                    label = gtk.Label()
                    label.set_markup('<b>%s</b>' % s.label)
                    frame.set_label_widget(label)
                    vbox = gtk.VBox()
                    frame.add(vbox)
                    parent.pack_start(frame, False, False, 0)
                    self._sensitivity_changed_cb(s, s.sensitive, frame, None)
                    s.connect("sensitivity-changed",
                              self._sensitivity_changed_cb,
                              frame, None)
                    self._populate_settings(vbox, s, level + 1)

    def _create_widget(self, table, row, setting, xpadding=0):
        print 'create', setting.name
        control = None
        label = None
        value_changed_cb = None
        control_changed_cb = None
        control_changed_signal = None
        if isinstance(setting, BooleanSetting):
            control = gtk.CheckButton(setting.label)
            control.set_active(setting.value)
            value_changed_cb = lambda s, v, w: w.set_active(v)
            control_changed_cb = self._checkbutton_toggled_cb
            control_changed_signal = 'toggled'
        else:
            label = gtk.Label("%s:" % setting.label)
            label.set_alignment(0.0, 0.5)

            if setting.entry_type == ENTRY_COLOR:
                control = gtk.ColorButton(
                    gtk.gdk.color_parse(setting.value))
                value_changed_cb = \
                    lambda s, v, w: w.set_color(gtk.gdk.color_parse(v))
                control_changed_cb = self._colorbutton_changed_cb
                control_changed_signal = 'color-set'
            elif setting.entry_type == ENTRY_FONT:
                control = gtk.FontButton(setting.value)
                value_changed_cb = lambda s, v, w: w.set_font_name(v)
                control_changed_cb = self._fontbutton_changed_cb
                control_changed_signal = 'font-set'
            elif setting.entry_type == ENTRY_SPIN:
                control = gtk.SpinButton()
                if isinstance(setting.value, float):
                    control.set_digits(2)
                    control.set_increments(0.01, 0.1)
                control.set_range(setting.min, setting.max)
                control.set_value(setting.value)
                control.update()
                value_changed_cb = lambda s, v, w: w.set_value(v)
                control_changed_cb = self._spinner_changed_cb
                control_changed_signal = "value-changed"
            elif setting.entry_type == ENTRY_RADIO and setting.allowed:
                if setting.children:
                    assert len(setting.children) == len(setting.allowed), \
                        "If a radio entry has children, they must be equal " \
                        "in quantity to the allowed values."
                label = None
                control = gtk.Table(
                    len(setting.allowed) + len(setting.children), 2)
                control.set_row_spacings(3)
                control.set_col_spacings(3)
                radios = []
                for string, localized in setting.allowed:
                    radios.append(gtk.RadioButton(None, localized))
                for radio in radios[1:]:
                    radio.set_group(radios[0])

                hid = setting.connect(
                    'value-changed',
                    lambda s, v, rs: \
                        rs[[a for \
                                a, b in s.allowed].index(v)].set_active(True),
                    radios)

                r = 0
                for i, radio in enumerate(radios):
                    radio.connect('toggled', self._radio_changed_cb, setting,
                                  radios, hid)
                    control.attach(radio, 0, 2, r, r + 1)
                    r += 1
                    if setting.children:
                        self._create_widget(control, r,
                                            setting.children[i], 12)
                        r += 1

            elif setting.entry_type == ENTRY_COMBO or setting.allowed:
                control = gtk.combo_box_new_text()
                for option in setting.allowed:
                    control.append_text(option[1])
                control.set_active(
                    [a for a, b in setting.allowed].index(setting.value))
                value_changed_cb = lambda s, v, w: w.set_active(
                    [a for a, b in s.allowed].index(v))
                control_changed_cb = self._combo_changed_cb
                control_changed_signal = 'changed'
            else:
                control = gtk.Entry()
                control.set_text(setting.value)
                value_changed_cb = lambda s, v, w: w.set_text(v)
                control_changed_cb = self._string_changed_cb
                control_changed_signal = 'insert-at-cursor'
            
        if label is not None:
            table.attach(label, 0, 1, row, row + 1, xpadding=xpadding)
            table.attach(control, 1, 2, row, row + 1)
        else:
            table.attach(control, 0, 2, row, row + 1, xpadding=xpadding)

        self._sensitivity_changed_cb(setting, setting.sensitive, control,
                                     label)
        setting.connect("sensitivity-changed", self._sensitivity_changed_cb,
                        control, label)

        if value_changed_cb and control_changed_signal and control_changed_cb:
            hid = setting.connect('value-changed', value_changed_cb, control)
            control.connect(control_changed_signal, control_changed_cb,
                            setting, hid)
        
    def _sensitivity_changed_cb(self, setting, sensitive, control, label):
        for w in (control, label):
            if w is not None:
                w.set_sensitive(sensitive)

    def _update_setting(self, setting, value, handler_id):
        if setting.value == value: return
        setting.handler_block(handler_id)
        setting.value = value
        setting.handler_unblock(handler_id)

    def _radio_changed_cb(self, radio, setting, radios, handler_id):
        if not radio.get_active():
            return

        i = radios.index(radio)
        self._update_setting(setting, setting.allowed[i][0], handler_id)

    def _spinner_changed_cb(self, spinner, setting, handler_id):
        self._update_setting(setting, spinner.get_value(), handler_id)

    def _checkbutton_toggled_cb(self, checkbutton, setting, handler_id):
        self._update_setting(setting, checkbutton.get_active(), handler_id)

    def _colorbutton_changed_cb(self, colorbutton, setting, handler_id):
        self._update_setting(setting, colorbutton.get_color().to_string(),
                             handler_id)

    def _fontbutton_changed_cb(self, fontbutton, setting, handler_id):
        self._update_setting(setting, fontbutton.get_font_name(), handler_id)

    def _string_changed_cb(self, entry, text, setting, handler_id):
        self._update_setting(setting, entry.get_text(), handler_id)

    def _combo_changed_cb(self, combo, setting, handler_id):
        self._update_setting(setting, setting.allowed[combo.get_active()][0],
                             handler_id)

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    w = PreferencesWindow_()
    w.show_all()
    try:
        w.run()
    except KeyboardInterrupt:
        gtk.main_quit()