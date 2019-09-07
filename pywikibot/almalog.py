#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
** (fr) **
Script de log.

** (en) **
Log script.
"""
#
# (C) Nakor
# (C) Toto Azéro, 2011
#
# Distribué sous licence MIT.
# Distributed under the terms of the MIT license.
#
import wikipedia

def error(title, log):
    site = wikipedia.getSite()
    #pagename = u'User:AlmabotJunior/Log/Erreurs'
    pagename = u'User:ZéroBot/Log/Erreurs'
    page=wikipedia.Page(site, pagename)
    text=page.get()
    
    text+=u'\n==%s==\n%s' % (title, log)

    page.put(text, u'Erreur lors de l\'éxécution de %s' % title)
