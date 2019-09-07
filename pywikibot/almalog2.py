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
import pywikibot

logs=u''

def error(title, log):
  site = pywikibot.getSite()
  #pagename = u'User:AlmabotJunior/Log/Erreurs'
  pagename = u'User:ZéroBot/Log/Erreurs'
  page=pywikibot.Page(site, pagename)
  text=page.get()

  text+=u'\n==%s==\n%s' % (title, log)

  try:
    page.put(text, u"Erreur lors de l'éxécution de %s" % title)
  except:
    pywikibot.output(u"L'erreur n'a pas pu être reportée correctement !")

def writelogs(title):
  if len(logs):
    site = pywikibot.getSite()
    #pagename = u'User:AlmabotJunior/Log/Avertissements'
    pagename = u'User:ZéroBot/Log/Avertissements'
    page=pywikibot.Page(site, pagename)
    text=page.get()
    
    text+=u'\n==%s==\n%s' % (title, logs)

  try:
    page.put(text, u"Avertissement lors de l'éxécution de %s" % title)
  except:
    pywikibot.output(u"L'avertissement n'a pas pu être reportée correctement !")
