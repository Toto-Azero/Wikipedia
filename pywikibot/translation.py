#!/usr/bin/python
# -*- coding: utf-8  -*-

import _errorhandler
import pywikibot
from pywikibot import catlib, config, pagegenerators
import codecs, re, _mysql

def projectsort(item):
    return item[1]

def capitalizefirst(string):
    return string[0:1].capitalize()+string[1:]

def checkproject(project):
    #pywikibot.output(u'Getting correct project for %s' % project)
    if project==u'Droit/rattachement précis non vérifié':
        project=u'Droit'
    elif project==u'Droit/dt':
        project=u'Droit'
    elif project==u'Cours d\'eau':
        project=u'Géographie'
    elif project==u'Jeu':
        project=u'Jeux'
    elif project==u'Précolompédia':
        project=u'Amérique précolombienne'
    elif project==u'Musique Country':
        project=u'Musique country'
    elif project==u'Animation et bande dessinée asiatiques/Naruto':
        project='Naruto'
    elif project==u'Rhône-Alpes/Ain':
        project='Ain'
    elif project==u'Les plus consultés':
        project=u'Wikipédia 1.0'
    elif re.match(u'Wikipédia 1.0/', project):
        project=u'Wikipédia 1.0'

    projectpage=pywikibot.Page(pywikibot.getSite(), u'Projet:'+project)

    if not projectpage.exists():
        _errorhandler.message(u'Ignoring non-existent project : %s' % project)
        project=None
    elif projectpage.isRedirectPage():
        targetproject=projectpage.getRedirectTarget()
        if targetproject.namespace()==100 or targetproject.namespace()==102:
            project=targetproject.title(withNamespace=False)
        else:
            pywikibot.output(u'Ignoring non-project target : %s (%d)' % (targetproject.title(), targetproject.namespace()))
            project=None

    if project==u'Mode/Projet':
        project=u'Mode'

    return project

def createcategories(addedprojects, debug, commandLogFile):
    # For tests
    #addedprojects.append('test_bot')

    botName=config.usernames['wikipedia']['fr']

    pywikibot.output('Create categories')
    pywikibot.output(str(addedprojects))

    site = pywikibot.getSite()
    addedprojectscat=list()
    addedprojectscatpage=list()
    addedprojects.sort()
    addedprojectscat.append(addedprojects[0])
    addedprojectscatpage.append(pywikibot.Page(site, u'Catégorie:Traduction du Projet %s' % addedprojects[0]))
    for project in addedprojects:
        if project!=addedprojectscat[-1]:
            addedprojectscat.append(project)
            addedprojectscatpage.append(pywikibot.Page(site, u'Catégorie:Traduction du Projet %s' % project))

    pywikibot.output('------------------------------')
    pywikibot.output(str(addedprojectscatpage))

    catgenerator=iter(addedprojectscatpage)
    catpreloadingGen=pagegenerators.PreloadingGenerator(catgenerator, 60)

    index=0
    for addedprojectcatpage in catpreloadingGen:
        if not addedprojectcatpage.exists():
            pywikibot.output(u'%s does not exist' % addedprojectcatpage.title(asLink=True))
            title = addedprojectcatpage.title()
            project = re.search(u'Traduction du Projet (.+)', title).group(1)
            #project=addedprojectscat[index]

            main_cat_project = pywikibot.Page(site, u"Catégorie:Projet:%s" % project)
            main_cat_project_str = ''
            if main_cat_project.exists():
                main_cat_project_str = main_cat_project.title(asLink=True)

            text=u'{{Translation/Projet|%s}}\n[[Catégorie:Traduction par projet|%s]]\n%s' % (project, project, main_cat_project_str)
            if (debug==0) or (debug==3):
                commandLogFile.write(u'******************************** %s ********************************\n' % addedprojectcatpage.title())
                commandLogFile.write(text)
                commandLogFile.write(u'********************************\n')
                addedprojectcatpage.put(text, u'Catégorisation en projet des pages de traduction')
            elif debug==2:
                newpage=pywikibot.Page(site, u'Utilisateur:'+botName+'/Test')
                newpage.put(text, u'Création de [[:%s]] ([[%s]])' % (addedprojectcatpage.title(), project))
            commandLogFile.write(u'* Création de [[:%s]]\r\n' % addedprojectcatpage.title())

        index=index+1

def translationiterator(generator, num):

    site = pywikibot.getSite()
    preloadingGen=pagegenerators.PreloadingGenerator(generator, step=num)

    index=1
    origlist=list()
    neworiglist=list()
    linkedlist=list()
    talklinkedlist=list()
    for page in preloadingGen:
        origtext=page.get(False, True)
        if re.search(u'Traduction/Suivi', origtext):
            parts=re.split(u'Traduction/Suivi', origtext, 1)
            newtext=parts[0]+u'Traduction/Suivi'
            parts=re.split(u'\|', parts[1])
            linkedpage1=pywikibot.Page(site, parts[3])

            origlist.append(page)
            linkedlist.append(linkedpage1)


            if (index==num):
                lpGen=iter(linkedlist)

                lpGenerator=pagegenerators.PreloadingGenerator(lpGen, step=num)
                subindex=0
                for linkedpage in lpGenerator:
                    if linkedpage.exists():
                        while linkedpage.isRedirectPage():
                            #pywikibot.output(u'Redirect found: %s to %s' % (linkedpage.title(), linkedpage.getRedirectTarget().title()))
                            linkedpage=linkedpage.getRedirectTarget()
                        if not linkedpage.isTalkPage():
                            linkedpage=linkedpage.toggleTalkPage()
                        talklinkedlist.append(linkedpage)
                        neworiglist.append(origlist[subindex])
                    subindex=subindex+1

                tlpGen=iter(talklinkedlist)
                tlpGenerator=pagegenerators.PreloadingGenerator(tlpGen, step=num)
                subindex=0
                for talklinkedpage in tlpGenerator:
                    yield (neworiglist[subindex], talklinkedpage)
                    subindex=subindex+1

                index=1
                origlist=list()
                neworiglist=list()
                linkedlist=list()
                talklinkedlist=list()
            else:
                index=index+1

    lpGen=iter(linkedlist)

    lpGenerator=pagegenerators.PreloadingGenerator(lpGen, step=num)
    subindex=0
    for linkedpage in lpGenerator:
        if linkedpage.exists():
            while linkedpage.isRedirectPage():
                pywikibot.output(u'Redirect found')
                linkedpage=linkedpage.getRedirectTarget()
            if not linkedpage.isTalkPage():
                linkedpage=linkedpage.toggleTalkPage()
            talklinkedlist.append(linkedpage)
            neworiglist.append(origlist[subindex])
        subindex=subindex+1

    tlpGen=iter(talklinkedlist)
    tlpGenerator=pagegenerators.PreloadingGenerator(tlpGen, step=num)
    subindex=0
    for talklinkedpage in tlpGenerator:
        yield (neworiglist[subindex], talklinkedpage)
        subindex=subindex+1


def main():

    botName=config.usernames['wikipedia']['fr']

    categ=False
    debug=0
    debugwrite=False
    lang=''
    checkcat=False
    startindex=None
    finishindex=None
    db=False

    for arg in pywikibot.handleArgs():
        if arg.startswith('-categ'):
            categ = True
            if arg.startswith('-categ:'):
                parts=re.split(u':', arg)
                lang=parts[1]
                if (len(parts)>2):
                    parts=re.split(u'-', parts[2])
                    startindex=int(parts[0])
                    if (len(parts)>1):
                        finishindex=int(parts[1])
        elif arg.startswith('-debugwt'):
            debug = 2
        elif arg.startswith('-debugw'):
            debug = 3
        elif arg.startswith('-debug'):
            debug = 1
        elif arg.startswith('-db'):
            db = True
        elif arg.startswith('-checkcat'):
            checkcat = True
        else:
            pywikibot.output(u'Syntax: translation.py [-categ[:lang]] [-debug]')
            exit()

    # Get category
    site = pywikibot.getSite()

    # Open logfile
    commandLogFilename = config.datafilepath('logs', 'translation.log')
    try:
        commandLogFile = codecs.open(commandLogFilename, 'a', 'utf-8')
    except IOError:
        commandLogFile = codecs.open(commandLogFilename, 'w', 'utf-8')

    if not debug==0:
        # SPECIFIC PAGES
        artlist=list()
        artlist.append(pywikibot.Page(site, u'Discussion:Psychologie/Traduction'))
        #artlist.append(pywikibot.Page(site, u'Utilisateur:'+botName+'/Tests'))
        #artlist.append(pywikibot.Page(site, u'Utilisateur:Almabot/Junior/Projet:Traduction/Carlos María de Alvear'))
        #artlist.append(pywikibot.Page(site, u'Discussion:Surtsey/Traduction'))
        gen = iter(artlist)
        # -CATEG
        #catname = u'Catégorie:Traduction par langue'
        #categ=catlib.Category(site, catname)
        #commandLogFile.write(u'== Traitement de [[:%s]] ==\r\n' % catname)
        #artlist=list(subcat.articles(True))
        #newlist=list()
        #for page in artlist:
        #    if not re.match (u'Projet:Traduction/\*/', page.title()):
        #        newlist.append(page)
        #pywikibot.output(u'Traitement de %d articles' % len(newlist))
        #gen = iter(newlist)
    elif categ:
        if lang=='0':
            catname=u'Catégorie:Page de suivi de traduction'
            categ=catlib.Category(site, catname)
            subcats=categ.subcategoriesList()
            artlist=list()
            for subcat in subcats:
                title=subcat.title()
                if re.match(u'Catégorie:Page de suivi de traduction', title) and (not re.search(u'/en', title)) and (not re.search(u'/de', title)):
                    sublist=list(subcat.articles(True))
                    artlist=artlist+sublist
            commandLogFile.write(u'== Traitement des petites catégories ==\r\n')
        elif lang:
            catname = u'Catégorie:Page de suivi de traduction/'+lang
            categ=catlib.Category(site, catname)
            commandLogFile.write(u'== Traitement de [[:%s]] ==\r\n' % catname)
            artlist=list(categ.articles(True))
            #pywikibot.output(u'index %d %d'% (startindex, finishindex))
            if startindex>=0 and finishindex:
                artlist=artlist[startindex:finishindex]
        else:
            catname = u'Catégorie:Traduction par langue'
            categ=catlib.Category(site, catname)
            commandLogFile.write(u'== Traitement de [[:%s]] ==\r\n' % catname)
            artlist=list(categ.articles(True))
        newlist=list()
        for page in artlist:
            if not re.match (u'Projet:Traduction/\*/', page.title()):
                newlist.append(page)
        #pywikibot.output(u'Traitement de %d articles' % len(newlist))
        gen = iter(newlist)
    elif db:
        database=_mysql.connect(host='frwiki-p.db.toolserver.org', db='frwiki_p', read_default_file="/home/totoazero/.my.cnf")
        database.query('SELECT page_title FROM page WHERE page_title REGEXP "/Traduction" AND page_namespace=1')
        results=database.store_result()
        result=results.fetch_row(maxrows=0)
        #pywikibot.output(u'Traitement de %d articles' % len(result))
        artlist=list()
        for res in result:
            title=res[0].decode('utf-8')
            page=pywikibot.Page(site, u'Discussion:%s' % title)
            artlist.append(page)

        gen=iter(artlist)
    else:
        commandLogFile.write(u'== Traitement des sous-pages de Projet:Traduction/ ==\r\n')
        catname = u'Catégorie:Traduction par projet'
        categ=catlib.Category(site, catname)
        commandLogFile.write(u'== Traitement de [[:%s]] ==\r\n' % catname)
        gen=categ.articles(True)

    if checkcat:
        pagesToProcess=pagegenerators.PreloadingGenerator(gen, 60)
    else:
        pagesToProcess=translationiterator(gen, 60)


    allset=0
    processed=0
    total=0
    addedprojects=list()

    dictionary=dict()
    for tuple in pagesToProcess:
        total=total+1
        if checkcat:
            projectpage=tuple
        else:
            projectpage=tuple[0]
            #linkedpage=tuple[1]
            linkedpage=pywikibot.Page(site, re.sub(u'/Traduction', u'', projectpage.title()))

        #pywikibot.output(u'Processing %s and %s' % (projectpage.title(), linkedpage.title()))

        if checkcat:
            commandLogFile.write(u'Processing [[%s]]\n' % projectpage.title())

        if projectpage.title() == u"Discussion:Interprétations politiques de Harry Potter/Traduction":
            commandLogFile.write(u'Escaping this page…')
            continue

        pywikibot.output(u'Processing [[%s]]\n' % projectpage.title())
        #if not checkcat:
        #    pywikibot.output('**** Traitement de %s (et %s)' % (projectpage.title(), linkedpage.title()))
        projectlist=list()

        # Templates broken
        #templates=page.templates()
        #for template in templates:
        #    templatetitle=template.title()
        #    #pywikibot.output(templatetitle)
        origtext=projectpage.get(False, True)
        if re.search(u'Traduction/Suivi', origtext):
            parts=re.split(u'Traduction/Suivi', origtext, 1)
            newtext=parts[0]+u'Traduction/Suivi'
            parts=re.split(u'\|', parts[1])

            existingprojects=list()
            for part in parts:
                subparts=re.split(u'(.*)<!--', part)
                subpart=subparts[0]
                if subpart[0:6] == u'projet':
                    substrings=subpart.split(u'=', 1)
                    fstring=substrings[0].strip();
                    if len(fstring)==6:
                        index=1
                    else:
                        index=int(fstring[6])
                    string=substrings[1].strip();
                    if len(string)>1:
                        existingprojects.append( (capitalizefirst(string), index, False) )

            if checkcat:
                for existingproject in existingprojects:
                    addedprojects.append(existingproject[0])
                    commandLogFile.write(u'  Adding [[%s]]\n' % existingproject[0])
                    if (len(addedprojects)>=200):
                        createcategories(addedprojects, debug, commandLogFile)
                        addedprojects=list()
            else:
                for (templatepage, args) in linkedpage.templatesWithParams():
                    #pywikibot.output(templatetitle)
                    if templatepage.namespace()==10:
                        templatetitle=templatepage.title(withNamespace=False)
                        if re.match(u'Wikiprojet ', templatetitle) or (re.match(u'Projet', templatetitle) and not re.match(u'Projet:Traduction', templatetitle)):
                            #pywikibot.output(templatetitle)
                            if templatepage.isRedirectPage():
                                targettemplate=templatepage.getRedirectTarget()
                                templatetitle=targettemplate.title(withNamespace=False)
                                #pywikibot.output(u'Template redirect: replacing with %s' % templatetitle)
                            locallen=0
                            if re.match(u'Wikiprojet', templatetitle):
                                locallen=11
                            elif re.match(u'Projet', templatetitle):
                                locallen=7
                            #pywikibot.output(u'%d' % locallen)
                            if not re.match(u'méta ', templatetitle[locallen:]):
                                string=templatetitle[locallen:]
                                key = capitalizefirst(string)
                                if key in dictionary:
                                    projectname=dictionary[key]
                                    #pywikibot.output(u'Found %s for %s in dictionary' % (projectname, key))
                                else:
                                    projectname=checkproject(key)
                                    dictionary[key]=projectname
                                if projectname:
                                    projectlist.append(projectname)
                                else:
                                    pywikibot.output('... while processing %s' % projectpage.title())
                        elif re.match(u'Évaluation multiprojet', templatetitle) or re.match(u'Wikiprojet', templatetitle):
                            projectflag=True
                            for arg in args:
                                arg=re.sub(u'\r\n', u'', arg)
                                while len(arg)>0 and arg[0]==' ':
                                    arg=arg[1:]
                                if projectflag and re.match(u'[Aa]vancement=', arg):
                                    break
                                if projectflag and re.match(u'[Àà] faire=', arg):
                                    break
                                elif len(arg)==0:
                                    break
                                elif projectflag and not re.match(u'[Aa]vancement', arg) and not re.match(u'[Àà] faire', arg) and not re.match(u'[Rr]aison', arg) and not re.match(u'[Tt]odo', arg) and not re.match(u'WP1.0', arg) and not re.match(u'[Ll]umière', arg) and not re.match(u'[Ww]ikiconcours', arg):
                                    if re.search(u'=', arg):
                                        commandLogFile.write(u'::Potential issue %s in %s:\r\n' % (arg, projectpage.title()))
                                        _errorhandler.message(u'::Potential issue %s in %s:\n' % (arg, projectpage.title()))
                                    else:
                                        key = capitalizefirst(arg)
                                        if key in dictionary:
                                            projectname=dictionary[key]
                                            #pywikibot.output(u'Found %s for %s in dictionary' % (projectname, key))
                                        else:
                                            projectname=checkproject(key)
                                            dictionary[key]=projectname
                                        if projectname:
                                            projectlist.append(projectname)
                                        else:
                                            pywikibot.output('... while processing %s' % projectpage.title())
                                        projectflag=False
                                else:
                                    projectflag=True

                #pywikibot.output(u'LENS: %d %d' % (len(projectlist), len(existingprojects)))
                listLength=len(projectlist)
                projectlist.sort()
                if listLength==len(existingprojects):
                    if (listLength==0):
                        projectChanges=False
                    else:
                        existingprojects.sort()
                        projectChanges=False
                        index=0
                        while (index<listLength) and (not projectChanges):
                            #pywikibot.output(u'Compare: %s | %s' % (projectlist[index], existingprojects[index][0]))
                            if not (projectlist[index]==existingprojects[index][0]):
                                projectChanges=True
                            index=index+1
                else:
                    projectChanges=True

                #pywikibot.output(u'LENS: %d %d' % (len(projectlist), len(existingprojects)))
                if projectChanges:
                    #pywikibot.output(u'Mise à jour des projets')
                    index = 1
                    projecttext = ''
                    for project in projectlist:
                        addedprojects.append(project)
                        if index==1:
                            projecttext+= 'projet=%s\n|' % project
                        else:
                            projecttext= projecttext + 'projet%d=%s\n|' % (index, project)
                        index = index+1

                    inserted = False
                    comments=''
                    for part in parts:
                        if not inserted:
                            if (len(existingprojects)==0) and (re.search(u'=', part)):
                                newtext=newtext+projecttext+part+'|'
                                inserted=True
                            elif (len(existingprojects)>0) and (re.match(u'projet', part)):
                                newtext=newtext+projecttext
                                inserted=True
                                if (re.search(u'<!--', part)):
                                    subparts=re.split(u'<!--', part, 1)
                                    newtext=newtext[:-1]+u'<!--'+subparts[1]+u'|'
                            else:
                                newtext=newtext+part+'|'
                        else:
                            if not re.match(u'projet', part):
                                newtext=newtext+part+'|'
                            else:
                                if (re.search(u'<!--', part)):
                                    subparts=re.split(u'<!--', part, 1)
                                    newtext=newtext[:-1]+u'<!--'+subparts[1]+u'|'

                    finaltext=newtext[0:len(newtext)-1]
                    if not origtext==finaltext:
                        pywikibot.output('**** Traitement de %s (et %s)' % (projectpage.title(), linkedpage.title()))
                        commandLogFile.write(u'* Traitement de [[%s]]\r\n' % projectpage.title())
                        if (debug==0) or (debug==3):
                            projectpage.put(finaltext, u'Catégorisation en projet des pages de traduction')
                        elif debug==2:
                            newpage=pywikibot.Page(site, u'Utilisateur:'+botName+'/Test')
                            newpage.put(origtext, u'Texte original de [[%s]]' % projectpage.title())
                            newpage.put(finaltext, u'Nouveau texte de [[%s]]' % projectpage.title())

            if (len(addedprojects)>=60):
                createcategories(addedprojects, debug, commandLogFile)
                addedprojects=list()

    if (len(addedprojects)>0):
        createcategories(addedprojects, debug, commandLogFile)


    #pywikibot.output(u'Total %d' % total)


if __name__ == '__main__':
    try:
        main()
    except Exception, myexception:
        _errorhandler.handle(myexception)
        raise
    finally:
        pywikibot.stopme()
