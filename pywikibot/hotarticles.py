#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Met à jour les modèles {{User:ZéroBot/Articles chauds}}.
"""
#
# (C) Toto Azéro, 2016
# (C) Ryan Kaldari, 2013-2015 
#
# Distribué sous licence GNU AGPLv3
# Distributed under the terms of the GNU AGPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: hotarticles.py 0100 2016-09-29 00:07:23 (CEST) Toto Azéro $'
#

from maj_articles_recents import check_and_return_parameter
from pywikibot import pagegenerators, config, textlib
import almalog2
import pywikibot
import pickle
import md5
import os
import MySQLdb
import time
import datetime
import traceback

def encode_sql(string):
        return string.replace('"', '\\"').replace(' ', '_').encode('utf-8')

def page_to_sql_string(page, asLink = False, withNamespace=False):
        return encode_sql(page.title(asLink = asLink, withNamespace = withNamespace))

def decode_sql(string, remove_underscores=True):
        if remove_underscores:
                string = string.replace('_', ' ')
        return string.decode('utf-8')
        
class BotArticlesChauds():
        def __init__(self, main_page, modele, dry=False):
                self.site = pywikibot.Site()
                self.main_page = main_page
                self.modele = modele
                self.dry = dry
                
                self.matchDebut = u"<!-- Ce tableau est créé automatiquement par un robot. Articles Chauds DEBUT -->"
                self.matchFin = u"\n<!-- Ce tableau est créé automatiquement par un robot. Articles Chauds FIN -->"
                
                self.cat = None
                self.nbMax = None
                self.minimum = None
                self.delai = None
                self.orange = None
                self.rouge = None
                self.actions = None
                self.mineures = None
                self.contributeurs = None
                self.minimum_contributeurs = None
                self.bots_inclus = None
                self.bots_inclus_str = None
                self.transclusion = None
                self.diff = None
                self.lien_historique = None
                
                self.comment = u'Bot: Mise à jour des articles chauds'
                
        def get_params(self):
                text = self.main_page.get()

                templates = textlib.extract_templates_and_params(text)
                template_in_use = None
                for tuple in templates:
                        if tuple[0] == modele.title(asLink=False):
                                template_in_use = tuple[1]
                                break
                
                if not template_in_use:
                        pywikibot.output(u"Aucun modèle {{%s}} détecté sur la page %s" % (modele.title(asLink=False), main_page.title()))
                        return False

                titre_categorie = check_and_return_parameter(template_in_use, u'catégorie')
                if not titre_categorie:
                        return False
                self.cat = pywikibot.Category(site, titre_categorie)
                if not self.cat.exists():
                        pywikibot.output(u"Erreur : la catégorie n'existe pas")
                        return False
                
                self.nbMax = check_and_return_parameter(template_in_use, 'nbMax', -1)
                try:
                        self.nbMax = int(self.nbMax)
                except:
                        pywikibot.output(u'Erreur : nbMax incorrect')
                        return False

                self.minimum = check_and_return_parameter(template_in_use, 'minimum', '10')
                try:
                        self.minimum = int(self.minimum)
                except:
                        pywikibot.output(u'Erreur : minimum incorrect')
                        return False
        
                self.actions = check_and_return_parameter(template_in_use, 'actions', '0,1,3')
                try:
                        [int(k) for k in self.actions.split(',')]
                except:
                        pywikibot.output(u'Erreur : des actions spécifiées ne sont pas des entiers')
                        return False

                self.delai = check_and_return_parameter(template_in_use, u'délai', '7')
                try:
                        self.delai = int(self.delai)
                        if self.delai <= 0:
                                pywikibot.output(u'Erreur : délai négatif')
                                return False
                except:
                        pywikibot.output(u'Erreur : délai incorrect')
                        return False

                self.orange = check_and_return_parameter(template_in_use, 'limite_orange', '20')
                try:
                        self.orange = int(self.orange)
                except:
                        pywikibot.output(u'Erreur : orange incorrect')
                        return False

                self.rouge = check_and_return_parameter(template_in_use, 'limite_rouge', '40')
                try:
                        self.rouge = int(self.rouge)
                except:
                        pywikibot.output(u'Erreur : rouge incorrect')
                        return False

                self.mineures = check_and_return_parameter(template_in_use, 'mineures', '0')
                try:
                        self.mineures = int(self.mineures)
                except:
                        pywikibot.output(u'Erreur : mineures incorrect')
                        return False

                self.contributeurs = check_and_return_parameter(template_in_use, 'contributeurs', '0')
                try:
                        self.contributeurs = int(self.contributeurs)
                except:
                        pywikibot.output(u'Erreur : contributeurs incorrect')
                        return False

                self.minimum_contributeurs = check_and_return_parameter(template_in_use, 'minimum_contributeurs', '1')
                try:
                        self.minimum_contributeurs = int(self.minimum_contributeurs)
                except:
                        pywikibot.output(u'Erreur : minimum_contributeurs incorrect')
                        return False

                self.bots_inclus = check_and_return_parameter(template_in_use, 'bots_inclus', '1')
                try:
                        self.bots_inclus = int(self.bots_inclus)
                except:
                        pywikibot.output(u'Erreur : bots_inclus incorrect')
                        return False
                
                self.bots_inclus_str = ''
                if self.bots_inclus == 0: # ne pas prendre les bots en compte
                        # rc_bot indique une modification faite par un bot
                        self.bots_inclus_str = 'AND rc_bot = 0'

                self.transclusion = check_and_return_parameter(template_in_use, 'transclusion', '0')
                try:
                        self.transclusion = int(self.transclusion)
                except:
                        pywikibot.output(u'Erreur : transclusion incorrect')
                        return False

                self.diff = check_and_return_parameter(template_in_use, 'diff', '0')
                try:
                        self.diff = int(self.diff)
                except:
                        pywikibot.output(u'Erreur : diff incorrect')
                        return False

                self.lien_historique = check_and_return_parameter(template_in_use, 'lien_historique', '0')
                try:
                        self.lien_historique = int(self.lien_historique)
                except:
                        pywikibot.output(u'Erreur : diff incorrect')
                        return False

                self.namespaces = check_and_return_parameter(template_in_use, 'namespaces', '0')
                print self.namespaces
                try:
                        # Check namespaces specified are actually numbers,
                        # and preformat them for the SQL request
                        self.namespaces = "(" + ",".join([str(int(k)) for k in self.namespaces.split(",")]) + ")"
                except:
                        pywikibot.output(u'Erreur : namespaces incorrect')
                        return False
                
                return True
        
        def build_table(self):
                frwiki_p = MySQLdb.connect(host='frwiki.labsdb', db='frwiki_p', read_default_file="/data/project/totoazero/replica.my.cnf")
        
                frwiki_p.query("SELECT s.rev_id, s.rev_timestamp FROM revision AS s \
                WHERE s.rev_timestamp > DATE_FORMAT(DATE_SUB(NOW(), INTERVAL %i DAY),'%%Y%%m%%d%%H%%i%%s') \
                ORDER BY s.rev_timestamp ASC LIMIT 1;" % self.delai)
                results = frwiki_p.store_result()
                result = results.fetch_row(how=1)[0]

                rev_timestamp = int(result['rev_timestamp'])
                rev_id = int(result['rev_id'])
                
                query = "SELECT page_id, page_title, COUNT(*) AS count_changes, SUM(rc_minor) \
AS count_minor, COUNT(DISTINCT rc_actor) as nb_users, SUM(rc_new_len - rc_old_len) as diff \
FROM recentchanges \
JOIN (SELECT page_id, page_title FROM categorylinks \
JOIN page ON page_id=cl_from AND page_namespace IN %(namespaces)s \
WHERE cl_to='%(category)s' AND page_latest > %(rev_id)i) AS main \
ON rc_cur_id=page_id \
WHERE rc_timestamp>%(rev_timestamp)i AND rc_type IN (%(actions)s) %(bots_inclus_str)s \
GROUP BY page_id HAVING count_changes >= %(limit)i AND nb_users >= %(minimum_contributeurs)i \
ORDER BY count_changes DESC;" % {
        'category':page_to_sql_string(self.cat), \
        'rev_id':rev_id, 'rev_timestamp':rev_timestamp, \
        'limit':self.minimum, 'actions':self.actions.encode('utf-8'),
        'minimum_contributeurs':self.minimum_contributeurs,
        'bots_inclus_str':self.bots_inclus_str,
        'namespaces': self.namespaces}
                
                if self.nbMax > 0:
                        query = query[:-1] + " LIMIT %i;" % self.nbMax
                
                print query
                frwiki_p.query(query)
                results = frwiki_p.store_result()
                
                text = u""
                
                # Il peut ne pas être nécessaire d'effectuer les transclusions
                # si le nombre de résultats n'excède par le paramètre transclusion
                # renseigné.
                if self.transclusion and results.num_rows() > self.transclusion:
                        do_transclude = True
                else:
                        do_transclude = False
                
                if do_transclude:
                        text += "<onlyinclude>"
                        
                text += u"{|"
                for i in range(results.num_rows()):
                        if do_transclude and i == self.transclusion:
                                # on vient d'atteindre le nombre de transclusions
                                text += "</onlyinclude>"
                        
                        result = results.fetch_row(how=1)[0]
                        count = int(result['count_changes'])
                        count_minor = int(result['count_minor'])
                        page = result['page_title']
                        nb_users = result['nb_users']
                        diff_value = result['diff']
                        
                        color = ''
                        if count > self.rouge:
                                color = "#c60d27"
                        elif count > self.orange:
                                color = "#f75a0d"
                        else:
                                color = "#ff9900"
                        
                        diff_str = ''
                        if self.diff:
                                signe = ''
                                gras = ""
                                if diff_value > 0:
                                        classe = "mw-plusminus-pos"
                                        signe = '+'
                                elif diff_value < 0:
                                        classe = "mw-plusminus-neg"
                                        # signe - déjà présent
                                else:
                                        classe = "mw-plusminus-null"
                                        
                                if abs(diff_value) >= 500:
                                        gras = "'''"
                                
                                diff_str = ' <span class="(classe)s">%(gras)s(%(signe)s{{formatnum:%(diff_value)i}})%(gras)s</span>' % {'classe':classe, \
                                        'signe':signe, 'gras':gras, 'diff_value':diff_value}
                        
                        actions_str = u"""'''%i'''&nbsp;<span style="font-size:60%%">actions</span>""" % count
                        if self.lien_historique:
                                actions_str = u"[//fr.wikipedia.org/w/index.php?title=" + decode_sql(page, remove_underscores=False) + \
                                        u"&action=history" + actions_str + u"]"
                        
                        if self.mineures and self.contributeurs:
                                text += u"""\n|-
| style="text-align:center; font-size:130%%; color:white; background:%(color)s; padding: 0 0.2em" | %(actions_str)s
| rowspan="3" style="padding: 0.4em;" | [[%(page)s]]%(diff)s
|-
| style="text-align:center; font-size:65%%; color:white; background:%(color)s; padding: 0 0.2em" | ('''%(count_minor)i'''&nbsp;mineures)
|-
| style="text-align:center; font-size:65%%; color:white; background:%(color)s; padding: 0 0.2em" | ('''%(nb_users)i'''&nbsp;contributeurs)
|-
|""" % {'color':color, 'actions_str':actions_str, 'page':decode_sql(page), 'count_minor':count_minor, 'nb_users':nb_users, 'diff':diff_str}
                        elif self.contributeurs:
                                text += u"""\n|-
| style="text-align:center; font-size:130%%; color:white; background:%(color)s; padding: 0 0.2em" | %(actions_str)s
| rowspan="2" style="padding: 0.4em;" | [[%(page)s]]%(diff)s
|-
| style="text-align:center; font-size:65%%; color:white; background:%(color)s; padding: 0 0.2em" | ('''%(nb_users)i'''&nbsp;contributeurs)
|-
|""" % {'color':color, 'actions_str':actions_str, 'page':decode_sql(page), 'nb_users':nb_users, 'diff':diff_str}
                        elif self.mineures:
                                text += u"""\n|-
| style="text-align:center; font-size:130%%; color:white; background:%(color)s; padding: 0 0.2em" | %(actions_str)s
| rowspan="2" style="padding: 0.4em;" | [[%(page)s]]%(diff)s
|-
| style="text-align:center; font-size:65%%; color:white; background:%(color)s; padding: 0 0.2em" | ('''%(count_minor)i'''&nbsp;mineures)
|-
|""" % {'color':color, 'actions_str':actions_str, 'page':decode_sql(page), 'count_minor':count_minor, 'diff':diff_str}
                        else:
                                text += u"""\n|-
| style="text-align:center; font-size:130%%; color:white; background:%(color)s; padding: 0 0.2em" | %(actions_str)s
| style="padding: 0.4em;" | [[%(page)s]]%(diff)s""" % {'color':color, 'actions_str':actions_str, \
                                               'page':decode_sql(page), 'diff':diff_str}
                
                text += "\n"
                
                if do_transclude:
                        text += "<onlyinclude>\n"
                        
                text += "|}"
                
                if do_transclude:
                        text += "</onlyinclude>"
                        
                return text
                        
        def edit_page(self):
                text = self.main_page.get()
                
                # Définition d'une nouvelle variable pour éviter toute suppression
                # involontaire dans text.
                new_text = text[:text.index(self.matchDebut)]
                new_text += self.matchDebut
                new_text += "\n"
                new_text += self.build_table()
                new_text += self.matchFin
                new_text += text[text.index(self.matchFin)+len(self.matchFin):]
                
                if not self.dry:
                        page.put(new_text, self.comment)
                else:
                        pywikibot.output(new_text)
                
        def run(self):
                pywikibot.output(u"\n=== Doing page %s ===" % self.main_page.title())                           
                if not self.get_params():
                        pywikibot.output(u"Erreur lors de la récupération des paramètres")
                        return False

                self.edit_page()
                return True
                                
if __name__ == '__main__':
        try:
                # parser des arguments
                dry = False
                test = False
                gen = []
                for arg in pywikibot.handleArgs():
                        if arg == "-dry":
                                dry = True
                                pywikibot.output(u'(dry is ON)')
                        
                        elif arg[0:6] == "-test:":
                                test = True
                                titre_page_test = arg[6:]
                                gen.append(titre_page_test)
                                
                                # pour afficher la mention uniquement
                                # la première fois que l'argument est rencontré
                                if not test:
                                        pywikibot.output(u'(test is ON)')
                        
                site = pywikibot.Site()
                titre_modele = u"Utilisateur:ZéroBot/Articles chauds"
                modele = pywikibot.Page(site, titre_modele)#, ns = 10)
                cat = pywikibot.Category(site, u"Catégorie:Page mise à jour par un bot/Articles chauds")
                
                
                # le générateur a été créé via la lecture des arguments
                # dans le cas où le mode test est actif.
                if not test:
                        #gen = pagegenerators.ReferringPageGenerator(modele, onlyTemplateInclusion = True)
                        gen = cat.articles()
                else:
                        gen = [pywikibot.Page(site, titre) for titre in gen]

                for page in gen:
                        try:
                                bot = BotArticlesChauds(page, modele, dry)
                                if not bot.run():
                                        pywikibot.output(u'Page %s not done' % page.title())
                        except Exception:
                                pywikibot.output(traceback.format_exc())
                                pywikibot.output("An error occurred while doing page %s" % page.title())
        except Exception, myexception:
                if not (test or dry):
                        pywikibot.output(traceback.format_exc())
                        almalog2.error(u'maj_articles_manquants', traceback.format_exc())
                raise
        finally:
                pywikibot.stopme()
