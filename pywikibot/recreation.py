# -*- encoding:utf-8 -*-
"""
Copyright (C) 2013  Xavier Combelle

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>


Ce bot permet de lister la liste des pages recrées

usage typique

python -m recreation.recreation --prefix 'Utilisateur:Xavier Combelle Bot/Journal des recréations'

ou

python -m recreation.recreation --prefix 'Utilisateur:Xavier Combelle Bot/Journal des recréations' --verbose
avec recreation.timestamp.txt un fichier contenant une seule ligne au format

2013-08-10

qui est la dernière date à laquelle le bot a été lancée

"""
from __future__ import unicode_literals, print_function
from datetime import date, timedelta, datetime
import re
import argparse
import sys
import locale
import pywikibot

from pywikibot import Page,Site
from pywikibot.exceptions import NoPage
from pywikibot.data import api


def api_query(params):
    """make a query
    
    arguments:
    params -- dictionary of params to pass to wikipedia api
    
    result:
    dict as json result of api
    """

    query = api.Request(site=pywikibot.Site(),**params )
    datas = query.submit()
    return datas
    
def deletelog(title):

    """
    query the delete log for the page
    
    arguments:
    title -- title of the page for which the log is required
    
    result:
    either 
        - the last entry of delete log for the page
        - None if there is no delete log
    """
    
    params = {
            'action': 'query',
            'list': "logevents",
            'letitle': title,
            'leprop':'title|timestamp',
            'leaction':"delete/delete",
            'lelimit':'1'
        }
    datas = api_query(params)
    dl = datas['query']['logevents']
    if dl:
        return dl[0]
        
def creation_log(start,end):
    """
    query the recent change for creation between the timestamp in parameter
    
    arguments:
    start -- time stamp of first creation (format YYYY-MM-DDTHH:MM:SSZ)"
    end -- time stamp of last creation (format YYYY-MM-DDTHH:MM:SSZ)"
    
    result:
    list of the creation events occuring between the timestamp
    """
    
    params = {
            'action': 'query',
            'list': "recentchanges",
            'rctype': "new",
            'rcnamespace': '0',
            'rcprop':'title|user|timestamp',
            'rcstart':end,
            'rcend':start,
            'rclimit':'10',
        }
    all_done = False

    while not all_done :
        
        if all_done:
            break
        datas = api_query(params)
        import pprint
        if datas == []:
            break
        data = datas['query']["recentchanges"]
        for d in data:
            yield d
        if 'query-continue' in datas:
            if 'recentchanges' in datas['query-continue']:
                params['rccontinue'] = datas['query-continue']['recentchanges']['rccontinue']
                
        else:
            all_done = True

def to_date(day):
    """
    convert a day from python time format to timestamp
     
    arguments:
    day -- python time format day
    
    result:
    timestamp (format YYYY-MM-DDTHH:MM:SSZ)
    """

    return day.strftime("%Y-%m-%dT00:00:00Z")

def from_date(timestamp):
    """
    convert a timestamp to python time format  
     
    arguments:
    timestamp -- string (format YYYY-MM-DDTHH:MM:SSZ)
    
    result:
    python time format
    """

    return datetime.strptime(timestamp,"%Y-%m-%dT%H:%M:%SZ")

def format_date(day,skip_day=False):
    """
    format day in french human readable format
     
    arguments:
    day -- python date format
    skip_day -- if True format "janvier 2013"
    
    result:
    the date formated of king
    either:
        - "1 janvier 2013"
        - "janvier 2013"
    depending on skip_day parameter
    """

    
    if skip_day:
        format_string = "{month} {year}"
    else:
        format_string = "{day} {month} {year}"
    return format_string.format(day=day.day,
                                month={1:"janvier",
                                       2:"février",
                                       3:"mars",
                                       4:"avril",
                                       5:"mai",
                                       6:"juin",
                                       7:"juillet",
                                       8:"août",
                                       9:"septembre",
                                       10:"octobre",
                                       11:"novembre",
                                       12:"décembre"}[day.month],
                                year = day.year)

def wiki_param(param):
    """
    format a parameter such as it is well behaved as a parameter in a template
    """
    if "=" in param:
        return "1="+param
    else:
        return param


ONE_DAY = timedelta(1)

def process(day):
    """
    one day bot processing
     
    arguments:
    day -- python date format
    
    """
    if params.verbose:
        print("processing Journal des recréations ({day})".format(day=format_date(day)))
    start = to_date(day)
    end = to_date(day+ONE_DAY)
    result = "\n\n== {} ==\n".format(format_date(day))
    comment = []
    for i,page in enumerate(creation_log(start,end),1):
        gras = ''
        date = ''
        if params.verbose:
            print (i,page["timestamp"])
    
        dl = deletelog(page["title"])
        if dl:
            page_pas = Page(Site(), "Discussion:" + page["title"] + "/Suppression")
            if page_pas.exists() and re.search(r'article supprimé', page_pas.get(), re.I):
                if re.search(r'\{\{ ?article supprimé[^\}]*\d{1,2} (\S* \d{4}) à', page_pas.get(), re.I):
                    date = u' de %s' % re.search(r'\{\{ ?article supprimé[^\}]*\d{1,2} (\S* \d{4}) à', page_pas.get(), re.I).group(1)
                comment.append(u'[[%s]] (malgré [[%s|PàS]]%s)' % (page["title"], page_pas.title(), date))
                gras = "'''"
            r = (u"* {g}{{{{a-court|{title}}}}} <small>([[{pas}|PàS]])</small> supprimé le {date} puis recréé par {{{{u|{user}}}}}{g} \n"
                            .format(title = wiki_param(page["title"]),
                            pas =  page_pas.title(),
                            user = wiki_param(page["user"]),
                            date = format_date(from_date(dl["timestamp"])),
                            g = gras))
            if params.verbose:
                print(r)
            result += r
    
    page = Page(Site(), params.prefix + u'/' + format_date(day, skip_day=True))
                                                                                               
    try:
        result = page.get() + result
    except NoPage:
        result = u'{{mise à jour bot|Zérobot}}' + result
    if comment: comment.insert(0, '')
    page.put(result,comment="Journal des recréations ({day}) ".format(day=format_date(day)) + ' - '.join(comment))

if __name__ == "__main__" : 

    parser = argparse.ArgumentParser(description='recreaction log bot for french wikipedia.')
    parser.add_argument('--verbose', help="enable verbose output", action='store_true')
    parser.add_argument('--prefix', 
                       help="prefix of the list page of recreation example: 'Utilisateur:ZéroBot/Journal_des_recréations'", 
                       action='store',
                       required = True)
    
    params = parser.parse_args()
    if sys.version_info < (3, 0):
        params.prefix = params.prefix.decode('utf-8')#params.prefix.decode(locale.getpreferredencoding())
    if "'" in params.prefix:
        input("Attention ! Le paramètre \"préfix\" contient des ' ce qui n'est pas nécéssaire. Continuer ?")
    Site().forceLogin()    
    end = datetime.today() - ONE_DAY
    with open("recreation.timestamp.txt") as ts:
        start = datetime.strptime(ts.read().strip(),"%Y-%m-%d")+ONE_DAY
    while start <= end:
        process(start)
        with open("recreation.timestamp.txt","w") as ts:
            print(start.strftime("%Y-%m-%d"),file=ts)
        start+=ONE_DAY
