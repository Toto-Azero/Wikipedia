#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

"""
Pour http://tools.wmflabs.org/totoazero/articles_manquants.php
"""
#
# (C) Toto Azéro, 2016
#
# Distribué sous licence GNU AGPLv3
# Distributed under the terms of the GNU AGPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: maj_articles_manquants.py 0005 2016-02-06 22:24:45 (CET) Toto Azéro $'
#

from maj_articles_recents import check_and_return_parameter
from pywikibot import pagegenerators, config, textlib
import _errorhandler
import pywikibot
import pickle
import md5
import os
import MySQLdb
import time
import datetime

def encode_sql(string):
	return string.replace('"', '\\"').encode('utf-8')

def page_to_sql_string(page, asLink = False):
	return encode_sql(page.title(asLink = asLink))

class BotArticlesManquants():
	def __init__(self, category, name=None):
		self.site = pywikibot.Site()
		self.category = category
		self.name = name

	def get_id(self, name=None):
		"""
		Renvoie l'id (de type int) de la catégorie rentrée dans la base.
		Si nécessaire crée cette id.
		"""
		db=MySQLdb.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
		db.query('SELECT id FROM am_correspondance WHERE cat="%s"' % page_to_sql_string(self.category))
		results = db.store_result()
		result = results.fetch_row(how=0)
		if result:
			return int(result[0][0])
		else:
			pywikibot.output('No id found, creating one.')
			db.query('SELECT id FROM am_correspondance ORDER BY id DESC LIMIT 1')
			results = db.store_result()
			last_id = int(results.fetch_row(how=0)[0][0])
			if not name:
				name = self.category.title(asLink=False, withNamespace=False).replace(u'/Articles liés', '')
			db.query('INSERT INTO am_correspondance VALUES ("%s", "%s", %i)' % (encode_sql(name), page_to_sql_string(self.category), last_id+1))
			return last_id+1

	def update_tables(self):
		"""
		Met à jour les tables SQL am_recensement et am_denombrement.
		"""
		hash = md5.new(self.category.title().encode('utf-8')).hexdigest()
		id = self.get_id(self.name)

		pywikibot.output("Hash for category is %s, id is %i" % (hash, id))

		db=MySQLdb.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")

		i = 0
		total = self.category.categoryinfo['pages']

		begin_time = time.time()
		time_remaining = 'calculating...'
		for page in self.category.articles():
			i +=1
			page_sql = page_to_sql_string(page)

			db.query('DELETE FROM am_recensement WHERE page="%s"' % page_sql)
			db.query('DELETE FROM am_denombrement WHERE page="%s"' % page_sql)

			count_total_links = 0
			linked_list = page.linkedPages(namespaces=[0])
			for linked_page in linked_list:
				count_total_links += 1

				linked_page_sql = page_to_sql_string(linked_page)
				db.query('SELECT page, existe FROM am_denombrement WHERE page="%s"' % linked_page_sql)
				results = db.store_result()
				result = results.fetch_row(how=1)

				#pywikibot.output("\t\tpage is %s", linked_page)
				if not linked_page.exists():
					db.query('INSERT INTO am_recensement VALUES ("%s", "%s", %i)' % (page_sql, linked_page_sql, id))

					#if result:
					#	nb_liens = int(result[0]['nb_liens'])
					#	nb_liens += 1
					#	db.query('UPDATE am_denombrement SET nb_liens = %i WHERE page = "%s"' % (nb_liens, linked_page_sql))
					#else:
					#	db.query('INSERT INTO am_denombrement VALUES ("%s", 1, FALSE)' % linked_page_sql)

					total_liens = len([p for p in linked_page.backlinks(namespaces=[0])])
					pywikibot.output("\t\t*count for %s : %i" % (linked_page, total_liens))
					if result:
						db.query('UPDATE am_denombrement SET nb_liens=%i, existe=FALSE WHERE page="%s"' % (total_liens, linked_page_sql))
					else:
						db.query('INSERT INTO am_denombrement VALUES ("%s", %i, FALSE)' % (linked_page_sql, total_liens))
				else:
					# le test result[0]['page'].decode('utf-8') == linked_page.title()
					# permet de s'assurer que la case pour le titre est correcte
					if result and result[0]['page'].decode('utf-8') == linked_page.title() and int(result[0]['existe']) == 0:
						pywikibot.output(u'\t\tupdating page %s that now exists' % linked_page)
						total_liens = len([p for p in linked_page.backlinks(namespaces=[0])])
						db.query('UPDATE am_denombrement SET nb_liens=%i, existe=TRUE WHERE page="%s"' % (total_liens, linked_page_sql))
						pywikibot.output('\t\tupdate finished')

			now = time.time()
			if now - begin_time > 60:
				time_remaining = str(datetime.timedelta(seconds=now-begin_time)*(total-i)/i)
			db.query('INSERT INTO am_denombrement VALUES ("%s", %i, TRUE)' % (page_sql, count_total_links))

			pywikibot.output(u'\tDid %s (%i out of %i; remaining time: %s)' % (page, i, total, time_remaining))#, end='\r')

		pywikibot.output(u"\tAll done for category %s" % category.title())

	def make_html(self):
		"""
		Crée un fichier HTML à partir des tables SQL, pour une consultation
		plus fluide et moins consommatrice de ressources.
		"""
		id = self.get_id(self.name)

		db=MySQLdb.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
		db.query('SELECT am_denombrement.page, COUNT(*) as count_red, nb_liens, \
(1 - COUNT(*)/nb_liens)*100 as avancement FROM am_denombrement \
JOIN am_recensement ON am_recensement.page = am_denombrement.page \
WHERE id = %(id)i GROUP BY page ORDER BY avancement DESC;' % {'id':id})
		results = db.store_result()

		text = """
<div class="bs-callout bs-callout-info" id="apercu">
<h4>Aperçu : tableau d\'avancement page par page</h4>
Donne pour chaque page de la catégorie :
<ul>
<li>le nombre de liens rouges présents sur la page,</li>
<li>le nombre total de liens présents sur la page,</li>
<li>un ratio <code>liens rouges/total liens</code>.</li>
</ul>
Sont exclus les articles ne comportant pas de lien rouge.
</div>

<table class="table">
	<thead>
        <col style="width:50%%">
        <col style="width:10%%">
        <col style="width:10%%">
        <col style="width:30%%">

		<tr>
			<th>Page</th>
			<th>Liens rouges</th>
			<th>Total liens</th>
			<th>Avancement</th>
		</tr>
	</thead>
 	<tbody>
"""

		result = results.fetch_row(how=1)
		while result:
			result = result[0]
			if result['avancement'] < 10:
				classe = ' class="danger"'
			elif result['avancement'] < 30:
				classe = ' class="warning"'
			else:
				classe = ''
			text += """
	<tr>
		<td><a href="https://fr.wikipedia.org/wiki/%(page)s">%(page)s</a></td>
		<td>%(count_red)i</td>
		<td>%(nb_liens)i</td>
		<td%(classe)s>
				<div class="progress-bar" role="progressbar" aria-valuenow="%(avancement)f" aria-valuemin="0" aria-valuemax="100" style="width: %(avancement)f%%;">
    				%(avancement).2f&nbsp;%%
    			</div>
  		</td>
	</tr>
""" % {'page': result['page'], 'count_red':result['count_red'], \
	   'nb_liens':result['nb_liens'], 'avancement':result['avancement'],
	   'classe':classe}

			result = results.fetch_row(how=1)

		text += """</tbody>
</table>
</fieldset>"""

		db=MySQLdb.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
		db.query('SELECT page, count_in_cat, nb_liens, count_in_cat/nb_liens AS percentage_in_cat \
FROM am_denombrement AS amd JOIN \
(SELECT page_rouge, COUNT(*) as count_in_cat, id FROM am_recensement GROUP BY page_rouge) AS amr \
ON page = page_rouge WHERE id = %(id)i AND existe=0 AND nb_liens >= 10 ORDER BY nb_liens DESC;' \
% {'id':id})
		results = db.store_result()

		text += """<div class="bs-callout bs-callout-info" id="demandes">
<h4>Tableau des articles demandés</h4>
Donne pour chaque page inexistante liée à au moins 10 autres pages de la catégorie :
<ul>
<li>le nombre de liens rouges trouvés dans les articles de la catégorie,</li>
<li>le nombre total d\'articles comportant un lien vers cette page,</li>
<li>un ratio <code>occurrences dans la catégorie/occurrences totales</code>, qui donne un indice de spécifité de la page à la catégorie.</li>
</ul>
</div>

<table class="table">
	<thead>
        <col style="width:60%">
        <col style="width:15%">
        <col style="width:15%">
        <col style="width:10%">

		<tr>
			<th>Page (inexistante)</th>
			<th>Occurrences dans la catégorie</th>
			<th>Occurrences totales</th>
			<th>Indice de spécificité</th>
		</tr>
	</thead>
 	<tbody>"""

		result = results.fetch_row(how=1)
		while result:
			result = result[0]
			text += """
	<tr>
		<td><a href="https://fr.wikipedia.org/wiki/%(page)s">%(page)s</a></td>
		<td>%(count_in_cat)i</td>
		<td>%(nb_liens)i</td>
		<td>%(percentage_in_cat).2f</td>
	</tr>
""" % {'page': result['page'], 'count_in_cat':result['count_in_cat'], \
	   'nb_liens':result['nb_liens'], 'percentage_in_cat':result['percentage_in_cat']}
			result = results.fetch_row(how=1)

		text += """</tbody>
</table>
</fieldset>"""

		with open('/data/project/totoazero/public_html/articles_manquants/%i.html' % id, 'w') as f:
			f.write(text)


	def run(self):
		pywikibot.output(u"Doing category %s" % self.category.title())
		self.update_tables()
		self.make_html()
		return True

if __name__ == '__main__':
	try:
		#gen = pagegenerators.ReferringPageGenerator(self.modele, onlyTemplateInclusion = True)
		#gen = [pywikibot.Page(self.site, u'User:Toto Azéro/Bac à sable 2')]
		#gen = [pywikibot.Page(pywikibot.Site(), u'Projet:Astronomie/Articles manquants')]
		site = pywikibot.Site()
		main_page = pywikibot.Page(site, u"User:ZéroBot/Articles manquants")
		#begin = '*'
		text = main_page.get()
		#text = text[text.index(begin):]
		li = text.split('\n')

		gen = []
		for item in li:
			# item est du type "* [[:catégorie:truc|nom]]"
			item = item[5:-2]
			couple = item.split('|')
			category = pywikibot.Category(site, couple[0])
			if len(couple) > 1:
				name = couple[1]
			else:
				name = None
			gen.append((category, name))

		for couple in gen:
			#try:
			(category, name) = couple
			bot = BotArticlesManquants(category, name=None)
			if not bot.run():
				pywikibot.output(u'Category %s not done' % category.title())
			#except Exception, myexception:
			#	pywikibot.output(u'%s %s'% (type(myexception), myexception.args))
				pywikibot.output("An error occurred while doing page %s" % page.title())
	except Exception, myexception:
		#if not (test or dry):
		_errorhandler.handle(myexception)
		raise
	finally:
		pywikibot.stopme()
