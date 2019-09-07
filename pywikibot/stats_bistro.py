#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Statistiques fixes dans la section [[#Aujourd.27hui.2C_dans_Wikip.C3.A9dia|#Aujourd'hui, dans Wikipédia]] du bistro du jour.
Voir cette discussion :
	http://fr.wikipedia.org/w/index.php?oldid=77299088#Stat.E2.80.99_globales_live
"""

#
# (C) Framawiki, 2019
# (C) Toto Azéro, 2012-2013
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: stats_bistro.py 120 2019-09-07 Framawiki $'
#

import almalog2
import pywikibot
from pywikibot import config, page, textlib
import locale, re
from datetime import datetime
import complements


def main():
	locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
		
	site = pywikibot.Site()
	now = datetime.now()
	
	page = pywikibot.Page(site, u"Wikipédia:Le Bistro/%i %s" % (int(now.strftime("%d")), now.strftime("%B %Y").decode('utf-8')))
	
	text = page.get()
	text_part = text[text.index(u"\n== Aujourd'hui, dans Wikipédia =="):]
	text_part_old = text_part
	text_part = text_part.replace(u"Actuellement, Wikipédia compte", u"Le ~~~~~, Wikipédia comptait")
	text_part = text_part.replace(u"{{NUMBEROFARTICLES}}", u"{{subst:NUMBEROFARTICLES}}")
	text_part = text_part.replace(u"{{Nombre d'articles de qualité}}", u"{{subst:formatnum:{{subst:#expr:{{subst:PAGESINCATEGORY:Article de qualité|R}}-3}}}}")
	text_part = text_part.replace(u"{{Nombre de bons articles}}", u"{{subst:formatnum:{{subst:#expr:{{subst:PAGESINCATEGORY:Bon article|R}}-3}}}}")
	text_part = text_part.replace(u"{{Nombre d'articles géolocalisés sur Terre}}", u"{{subst:formatnum:{{subst:#expr:{{subst:PAGESINCATEGORY:Article géolocalisé sur Terre|R}}}}}}")
	text_part = text_part.replace(u"{{Wikipédia:Le Bistro/Labels}}", u"{{subst:Wikipédia:Le Bistro/Labels}}")
	text_part = text_part.replace(u"{{Wikipédia:Le Bistro/Test}}", u"{{subst:Wikipédia:Le Bistro/Test}}")
	
	text = text.replace(text_part_old, text_part)
	
	page.put(text, comment = u"Bot: Substitution des modèles afin de rendre fixes les statistiques fixes dans la section [[#Aujourd.27hui.2C_dans_Wikip.C3.A9dia|#Aujourd'hui, dans Wikipédia]]")
	
	
if __name__ == '__main__':
    try:
        main()
    except Exception, myexception:
        almalog2.error(u'stats_bistro', u'%s %s'% (type(myexception), myexception.args))
        #print u'%s %s' % (type(myexception), myexception.args)
        raise
    finally:
        almalog2.writelogs(u'stats_bistro')
        pywikibot.stopme()
