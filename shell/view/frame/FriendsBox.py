# Copyright (C) 2006-2007 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import hippo

from sugar.graphics.canvasicon import CanvasIcon
from sugar.graphics import style
from sugar.presence import presenceservice
from view.BuddyIcon import BuddyIcon
from model.BuddyModel import BuddyModel

class FriendIcon(BuddyIcon):
    def __init__(self, shell, buddy):
        BuddyIcon.__init__(self, shell, buddy)
        self.get_palette().set_group_id('frame')

    def prelight(self, enter):
        if enter:
            self.props.background_color = style.COLOR_BLACK.get_int()
        else:
            self.props.background_color = style.COLOR_TOOLBAR.GREY.get_int()

class FriendsBox(hippo.CanvasBox):
    def __init__(self, shell):
        hippo.CanvasBox.__init__(self)
        self._shell = shell
        self._activity_ps = None
        self._joined_hid = -1
        self._left_hid = -1
        self._buddies = {}

        self._pservice = presenceservice.get_instance()
        self._pservice.connect('activity-appeared',
                               self.__activity_appeared_cb)

        # Add initial activities the PS knows about
        for activity in self._pservice.get_activities():
            self.__activity_appeared_cb(self._pservice, activity)

        home_model = shell.get_model().get_home()
        home_model.connect('active-activity-changed',
                           self._active_activity_changed_cb)

    def add_buddy(self, buddy):
        if self._buddies.has_key(buddy.props.key):
            return

        model = BuddyModel(buddy=buddy)
        icon = FriendIcon(self._shell, model)
        self.append(icon)

        self._buddies[buddy.props.key] = icon

    def remove_buddy(self, buddy):
        if not self._buddies.has_key(buddy.props.key):
            return

        self.remove(self._buddies[buddy.props.key])

    def clear(self):
        for item in self.get_children():
            self.remove(item)
        self._buddies = {}

    def __activity_appeared_cb(self, pservice, activity_ps):
        activity = self._shell.get_current_activity()
        if activity and activity_ps.props.id == activity.get_id():
            self._set_activity_ps(activity_ps)

    def _set_activity_ps(self, activity_ps):
        if self._activity_ps == activity_ps:
            return

        if self._joined_hid > 0:
            self._activity_ps.disconnect(self._joined_hid)
            self._joined_hid = -1
        if self._left_hid > 0:
            self._activity_ps.disconnect(self._left_hid)
            self._left_hid = -1

        self._activity_ps = activity_ps

        self.clear()

        if activity_ps != None:
            for buddy in activity_ps.get_joined_buddies():
                self.add_buddy(buddy)

            self._joined_hid = activity_ps.connect(
                            'buddy-joined', self.__buddy_joined_cb)
            self._left_hid = activity_ps.connect(
                            'buddy-left', self.__buddy_left_cb)

    def _active_activity_changed_cb(self, home_model, home_activity):
        if not home_activity:
            self._set_activity_ps(None)
            return

        activity_id = home_activity.get_activity_id()
        if not activity_id:
            self._set_activity_ps(None)
            return
        
        # HACK to suppress warning in logs when activity isn't found
        # (if it's locally launched and not shared yet)
        activity = None
        for act in self._pservice.get_activities():
            if activity_id == act.props.id:
                activity = act
                break
        if activity:
            self._set_activity_ps(activity)
        else:
            self._set_activity_ps(None)

    def __buddy_joined_cb(self, activity, buddy):
        self.add_buddy(buddy)

    def __buddy_left_cb(self, activity, buddy):
        self.remove_buddy(buddy)
