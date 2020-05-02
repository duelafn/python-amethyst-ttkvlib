# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: GPL-3.0
__all__ = ['ToastBehavior']

import collections
import threading
import time

from kivy.clock import Clock
from kivy.factory import Factory

class ToastBehavior(object):
    errstr = Factory.StringProperty()
    errtime = Factory.NumericProperty()

    def __init__(self, *args, **kwargs):
        self.toastlock = threading.RLock()
        self.toastjournal = collections.deque(maxlen=5)
        self.toastclock = None
        super().__init__(*args, **kwargs)

    def _update_toast(self, *args):
        with self.toastlock:
            if self.toastclock:
                self.toastclock.cancel()
                self.toastclock = None
            now = time.time()
            if not self.errstr or (self.errtime and now > self.errtime):
                self.pop_toast()
            if self.errstr and self.errtime and now < self.errtime:
                self.toastclock = Clock.schedule_once(self._update_toast, self.errtime - now)

    def pop_toast(self):
        with self.toastlock:
            if self.toastjournal:
                self.errstr, self.errtime = self.toastjournal.popleft()
                if self.errtime:
                    self.errtime += time.time()
                self._update_toast()
            else:
                self.errstr, self.errtime = '', 0
                if self.toastclock:
                    self.toastclock.cancel()
                    self.toastclock = None

    def toast(self, msg, timeout=None):
        with self.toastlock:
            self.toastjournal.append( (msg, timeout) )
            if not self.toastclock:
                self._update_toast()

    def error(self, msg, timeout=None):
        self.toast(f'[color=#f44336]{msg}[/color]', timeout)
    def warning(self, msg, timeout=None):
        self.toast(f'[color=#ffc107]{msg}[/color]', timeout)
