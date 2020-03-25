#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Permet de remonter les erreurs dans Sentry.
Doit être appelé en premier dans la chaîne des dépendances.

Dernières modifications :
* 0001 : Première version
"""
from __future__ import unicode_literals, print_function
#
# (C) Framawiki, 2019
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: _errorhandler.py 0001 2019-09-21 Framawiki $'
#

import os
import traceback
import sys


def initiate():
    filename = os.path.join(os.path.expanduser('~'), '.pywikibot/sentry-key')
    if not os.path.exists(filename):
        print(u'Sentry (error reporting) disabled because no key found')
    else:
        with open(filename, 'r') as f:
            sentry.init(f.readline())


def add_tags(addtags):
    with sentry.configure_scope() as scope:
        for tag, value in addtags.items():
            scope.set_tag(tag, value)
        
        scope.set_tag('script', sys.argv[0].split('/')[-1])
        
        try:
            import pywikibot
            scope.set_tag('pwb_version', pywikibot.version.getversion())
        except ImportError:
            pass


def log_context(message, category=None):
    if sentry:
        # sentry enabled means production, so no need to log everything, only inform sentry in case error appends later
        sentry.add_breadcrumb(message=message, category=category)
    else:
        if category:
            print('%s: %s' % (category, message))
        else:
            print(message)

def print_event_id(event_id):
    print(u'Event reported to Sentry as [%s]' % event_id)


def handle(exception, level='error', addtags={}, fatal=True):
    if fatal:
        print(u'Fatal %s:' % level)

    if sentry:
        add_tags(addtags)
        event_id = sentry.capture_exception(exception)
        print_event_id(event_id)
    else:
        print(traceback.format_exc())


def message(message, addtags={}):
    print(u'Message: %s (%s)' % (message, addtags))

    if sentry:
        add_tags(addtags)
        event_id = sentry.capture_message(message)
        print_event_id(event_id)


try:
    import sentry_sdk
except ImportError:
    print(u'Sentry (error reporting) disabled because no sdk lib found')
    sentry = None
else:
    sentry = sentry_sdk
    try:
        initiate()
    except Exception as e:
        print('Sentry (envoi des erreurs) initialisation échouée')
        raise
