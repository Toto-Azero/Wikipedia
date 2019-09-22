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
        print(u'Sentry (envoi des erreurs) désactivé car clé introuvable')
    else:
        with open(filename, 'r') as f:
            sentry.init(f.readline())
        with sentry.configure_scope() as scope:
            scope.set_tag('script', sys.argv[0].split('/')[-1])


def add_tags(addtags):
    with sentry.configure_scope() as tdict:
        for tag, value in addtags.items():
            tdict.set_tag(tag, value)


def handle(exception, level='error', addtags={}):
    print(u'Fatal %s:' % level)

    if sentry:
        add_tags(addtags)
        sentry.capture_exception(exception)
    else:
        print(traceback.format_exc())


def message(message, addtags={}):
    print(u'Message: %s' % message)

    if sentry:
        add_tags(addtags)
        sentry.capture_message(message)


try:
    import sentry_sdk
except ImportError:
    print(u'Sentry (envoi des erreurs) désactivé car sdk pas installé')
    sentry = None
else:
    sentry = sentry_sdk
    try:
        initiate()
    except Exception as e:
        print('Sentry (envoi des erreurs) initialisation échouée')
        raise
