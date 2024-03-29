import urllib, urllib2, cookielib
import re
import string
import datetime
from BeautifulSoup import BeautifulSoup
import cPickle

SILVESTRE_PATH = 'http://silvestre.itba.edu.ar'
BASE_PATH = SILVESTRE_PATH + '/itbaV/'
IOL_LOGIN_PATH = BASE_PATH + 'mynav.asp'
IOL_NAVBAR_PATH = BASE_PATH + 'mynav.asp'
MATERIAL_DIDACTICO_PATH = BASE_PATH + 'newmaterialdid.asp'
IOL_DESKTOP_PATH = BASE_PATH + 'mydesktop.asp'
NEWS_PATH = BASE_PATH + 'novlistall.asp'

class AbstractIOLPathNode(object):
    """ Node belonging to a subjet's tree. """

    def __init__(self, url, parent=None, name=None):
        self.url = url
        self.parent = parent
        self.name = name
        self.buildNode()

    #Hook.
    def buildNode(self):
        pass


class IOLFile(AbstractIOLPathNode):
    """ Subjet's file """
    def buildNode(self):
        webPage = PyIOLSucker().IOLUrlOpen(self.url)
        soup = BeautifulSoup(webPage.read())

        webPage = PyIOLSucker().IOLUrlOpen(BASE_PATH + soup('frame')[0]['src'])
        soup = BeautifulSoup(webPage.read())

        self.file = SILVESTRE_PATH + soup('a')[0]['href']

    def __repr__(self):
        return  self.name

class IOLAbstractFolder(AbstractIOLPathNode):
    """ Subjet's directory """
    def __init__(self, url, parent=None, name=None):
        self._children = []
        AbstractIOLPathNode.__init__(self, url, parent, name)

    def buildNode(self):
        webPage = PyIOLSucker().IOLUrlOpen(self.url)
        soup = BeautifulSoup(webPage.read())
        table = soup('tbody')[0]
        files = table('tr', 'hand')
        folders = filter ( lambda x: x.findAll('img', alt='Ir a carpeta') != [], table('tr'))

        for folder in folders:
            folder_name = ((folder('td',colspan=2)[0])('font')[0].string).strip()
            self._children.append(IOLFolder( BASE_PATH + folder('a')[0]['href'], self, name=folder_name))

        for f in files:
            file_name = (f('td')[1])('font')[0].contents[0].string.strip()
            number = re.findall("[0-9]+", f['onclick'])[0]
            self._children.append(IOLFile( BASE_PATH + 'showfile.asp?fiid=' + str(number),\
                                 self, name=file_name))

    def __repr__(self):
        return  self.name + self._children.__repr__()

#Inherits from IOLAbstractFolder
class IOLFolder(IOLAbstractFolder):
     pass

#class IOLLazyFolder(IOLAbstractFolder):
#    _nodeBuilt = False
#    def __getReal(self):
#        self = IOLFolder(self.obj, self.url, self.parent)
#       TODO: Me tiene que pisar el padre!!! No tengo el puntero!!
#        self.parent.makeMeReal(self)
#        if not self._nodeBuilt:
#            self._children = property(None, None, None)
#            self._children = []
#            self.__buildNode()
#            self._nodeBuilt = True
#        return self._children 
#    def __init__(self, obj, url, parent=None):
#        self.url = url
#        self.parent = parent
#        self.obj = obj

#    _children = property(__getReal, None, None)


#Albert: shouldn't be class PyIOLSucker(object): ?
class PyIOLSucker:

    __instance = None

    class __impl:
        """Implementation of the singleton instance"""
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = { 'User-Agent' : user_agent }

        def __init__(self):
            self.cookies = None

        def doLogin(self, dni, passwd):
            params = urllib.urlencode({'txtdni': dni,
                                        'txtpwd': passwd,
                                        'cmd': 'login'})

            req = urllib2.Request(IOL_LOGIN_PATH, params, self.headers)
            webPage = urllib2.urlopen(req)
            self.cookies = cookielib.CookieJar()
            self.cookies.extract_cookies(webPage,req)

        def isLogged(self):
            if self.cookies is None:
                return False

            try:
                webPage = self.IOLUrlOpen( IOL_DESKTOP_PATH )
                soup = BeautifulSoup(webPage.read())
            except urllib2.HTTPError, e:
                return False

            if soup('title')[0] == 'The page cannot be displayed':
                return False
            return True

        def IOLUrlOpen(self, url):
            req = urllib2.Request(url, headers=self.headers)
            self.cookies.add_cookie_header(req)
            try:
                return urllib2.urlopen(req)
            except urllib2.URLError, e:
                raise urllib2.URLError

    def __init__(self):
        """ Create singleton instance """
        if PyIOLSucker.__instance is None:
            PyIOLSucker.__instance = PyIOLSucker.__impl()

        self.__dict__['_PyIOLSucker__instance'] = PyIOLSucker.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

class Subject(object):
    def __init__(self, url):
        #To get different "Material Didactico's path, we must
        #first connect to the main page of the subject and then
        #open the one and only "Material Didactico's path"
        self.webPage = PyIOLSucker().IOLUrlOpen(BASE_PATH + url)
        self.folder = IOLFolder(MATERIAL_DIDACTICO_PATH, name='root')

class News(object):

    def __init__(self):
        #Gets HTML needed to parse news. 
        self.webPage = PyIOLSucker().IOLUrlOpen(NEWS_PATH)
        self.html = self.webPage.read()
        self.soup = BeautifulSoup(self.html)

        #List of singleNews
        self.newsList = []

        #Vars used to parse news
        bgcolor = None
        father = None
        section = None
        link = None
        delLink = None
        title = None
        clase = None

        #Every table @ HTML is parse depending on bgcolor attribute.
        self.tables = self.soup.findAll('tr')
        for table in self.tables:
            for at in table.attrs:
                if at[0] == 'bgcolor':
                    bgcolor = at[1]
            
            if bgcolor == 'LIGHTSTEELBLUE':
                father = table.td.string.strip()
            elif bgcolor == 'SILVER':
                section = table.td.string.strip()
            elif bgcolor == 'WHITE' and table.a:
                link = table.attrs[2][1].split('\'')[1]
                delLink = table.a.attrs[0][1]
                title = table.td.contents[2].strip()
                self.newsList.append( singleNews(father, section, link, delLink, title) )

    def deleteAll(self):
        if self.newsList:
            for news in self.newsList:
                PyIOLSucker().IOLUrlOpen(BASE_PATH + news.delLink)
                self.newsList.remove(news)
        else:
            print 'No news to remove'

    def printNews(self):
        if self.newsList:
            for news in self.newsList:
                print   'Father: %s\nSection: %s\nLink: %s\nDelLink: %s\nTitle: %s \n '\
                        % ( news.father, news.section, news.link, news.delLink, news.title)
        else:
            print 'No news to print'


class singleNews(object):
    #singleNews variables.
    link = None
    delLink = None
    father = None
    section = None
    title = None

    def __init__(self, father, section, link, delLink, title ):
        self.father = father
        self.section = section
        self.link = link
        self.delLink = delLink
        self.title = title



def getSubjects():

    try:
        pkl_file = open('subjects_iol.pkl','rb')
        subjects = cPickle.load(pkl_file)
        #TODO: Update!
        return subjects
    except IOError, e:
        subjects = []
    except EOFError, e:
        subjects = []

    #Nav bar
    webPage = PyIOLSucker().IOLUrlOpen(IOL_NAVBAR_PATH)
    html = webPage.read()

    soup = BeautifulSoup(html)

    #Checking if I can fix bug. Old code below
    #materias = soup('td', colspan='2')[1:]
    #subject_links = map( lambda x: x('a')[0]['href'],  materias)
    
    #new code.
    #Gets subjets I am doing.
    #from soup I don't get first one, because it should be the name of my career.
    materias = soup.findAll('td', colspan="2")[1:]
    subject_links = [materia('a')[0]['href'] for materia in materias if materia.a]

    if subject_links:
        for subject_link in subject_links:
            #Stupid bug:
            #@ utf8 links looks like: 
            #mynav.asp?cmd=ChangeContext&amp;nivel=4&amp;snivel=22.09
            #where they should be
            #mynav.asp?cmd=ChangeContext&nivel=4&snivel=22.09
            #Fixed with a string.replace
            subject_link = string.replace(subject_link,"&amp;","&")
            subjects.append(Subject(subject_link))

    output = open('subjects_iol.pkl','wb')
    cPickle.dump(subjects, output)
    output.close()

    return subjects

def acidRain(t):
    #TODO: REFACTOR
    if str(t.__class__) == '<class \'iol.IOLFile\'>':
        return [t]
    else:
        files_ = []
        for i in t._children:
         new_files = acidRain(i)
         files_ = files_ + new_files
 
    return files_

