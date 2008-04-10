import PyRSS2Gen
from iolsucker import *

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
	

if __name__ == '__main__':
	#TODO Verify if dni is correct.
	dni = raw_input('Enter your DNI: ')
	pwd = getpass.getpass("Enter password for DNI %s: " %dni)
	getFeed(dni, pwd)