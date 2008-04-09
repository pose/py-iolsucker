# -*- coding: utf-8 -*-
import urllib2, urllib, cookielib
import re
import datetime
from BeautifulSoup import BeautifulSoup
import PyRSS2Gen
import cPickle

SILVESTRE_PATH = 'http://silvestre.itba.edu.ar'
BASE_PATH = SILVESTRE_PATH + '/itbaV/'
IOL_LOGIN_PATH = BASE_PATH + 'mynav.asp'
IOL_NAVBAR_PATH = BASE_PATH + 'mynav.asp'
MATERIAL_DIDACTICO_PATH = BASE_PATH + 'newmaterialdid.asp'
IOL_DESKTOP_PATH = BASE_PATH + 'mydesktop.asp'

class AbstractIOLPathNode(object):
    """ Nodo perteneciente al arbol de una materia """

    def __init__(self, url, parent=None, name=None):
        self.url = url
        self.parent = parent
	self.name = name
        self.buildNode()

    def buildNode(self):
        pass


class IOLFile(AbstractIOLPathNode):
    """ Archivo de una materia """
    def buildNode(self):
	r = PyIOLSucker().IOLUrlOpen(self.url)
	soup = BeautifulSoup(r.read())

	r = PyIOLSucker().IOLUrlOpen(BASE_PATH + soup('frame')[0]['src'])
	soup = BeautifulSoup(r.read())
	
	self.file = SILVESTRE_PATH + soup('a')[0]['href']

    def __repr__(self):
	return  self.name
        
class IOLAbstractFolder(AbstractIOLPathNode):
    """ Directorio de una materia """
    def __init__(self, url, parent=None, name=None):
        self._children = []
        AbstractIOLPathNode.__init__(self, url, parent, name)

    def buildNode(self):
        r = PyIOLSucker().IOLUrlOpen(self.url)
        soup = BeautifulSoup(r.read())
        table = soup('tbody')[0]
        files = table('tr', 'hand')
        folders = filter ( lambda x: x.findAll('img', alt='Ir a carpeta') != [], table('tr'))

        for folder in folders:
	    folder_name = ((folder('td',colspan=2)[0])('font')[0].string).strip()
            self._children.append(IOLFolder( BASE_PATH + folder('a')[0]['href'], self, name=folder_name))
        
        for f in files:
	    file_name = (f('td')[1])('font')[0].contents[0].string.strip()
            number = re.findall("[0-9]+", f['onclick'])[0]
            self._children.append(IOLFile( BASE_PATH + 'showfile.asp?fiid=' + str(number), self, name=file_name))

    def __repr__(self):
	return  self.name + self._children.__repr__()


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

class PyIOLSucker:
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
            r = urllib2.urlopen(req)
            self.cookies = cookielib.CookieJar()
            self.cookies.extract_cookies(r,req)

        def isLogged(self):
            if self.cookies is None:
                return False

            try:
                r = self.IOLUrlOpen( IOL_DESKTOP_PATH )
                soup = BeautifulSoup(r.read())
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

    __instance = None

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

class Subject:
    def __init__(self, url):
        r = PyIOLSucker().IOLUrlOpen(BASE_PATH + url)
        self.folder = IOLFolder(MATERIAL_DIDACTICO_PATH, name='root')

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
    r = PyIOLSucker().IOLUrlOpen(IOL_NAVBAR_PATH) 
    html = r.read()
    
    soup = BeautifulSoup(html)
    #Omito el primer td que es de Ingeniera Informatica
    #consigo las materias que curso
    materias = soup('td', colspan='2')[1:]
    
    subject_links = map( lambda x: x('a')[0]['href'],  materias)
    if subject_links:
        for subject_link in subject_links:
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


def getFeed(dni, passwd):
    files = []
    
    sucker = PyIOLSucker()
    if not sucker.isLogged():
        sucker.doLogin(dni,passwd)
    subs = getSubjects()

    for subject in subs:
        files = files + acidRain(subject.folder)
    
    items = []

    for i in files:
	items.append(PyRSS2Gen.RSSItem(
		title = i.name,
		link = i.file,
		description = i.name,
		pubDate =  datetime.datetime.now()
		))
	

    rss = PyRSS2Gen.RSS2(
    	title = "ITBA feed",
	link = SILVESTRE_PATH,
    	description = "ITBA Feed",
    	lastBuildDate = datetime.datetime.now(),
    	items = items)
    
    rss.write_xml(open("itba.xml", "w"))

