from binsearch import BinSearch
from nzbclub import NZBClub
from nzbindex import NZBIndex

from bs4 import BeautifulSoup
from couchpotato.core.helpers.variable import getTitle, splitString, tryInt
from couchpotato.core.helpers.encoding import simplifyString
from couchpotato.environment import Env
from couchpotato.core.logger import CPLog
from couchpotato.core.helpers import namer_check
from couchpotato.core.media._base.providers.nzb.base import NZBProvider

log = CPLog(__name__)
import re
import urllib
import urllib2
import traceback

class Base(NZBProvider):
    allowedGroups = {
        'abmulti': 'alt.binaries.multimedia',
        'ab.moovee': 'alt.binaries.moovee',
        'abtvseries': 'alt.binaries.tvseries',
        'abtv': 'alt.binaries.tv',
        'a.b.teevee': 'alt.binaries.teevee',
        'abstvdivxf': 'alt.binaries.series.tv.divx.french',
        'abhdtvx264fr': 'alt.binaries.hdtv.x264.french',
        'abmom': 'alt.binaries.mom',
        'abhdtv': 'alt.binaries.hdtv',
        'abboneless': 'alt.binaries.boneless',
        'abhdtvf': 'alt.binaries.hdtv.french',
        'abhdtvx264': 'alt.binaries.hdtv.x264',
        'absuperman': 'alt.binaries.superman',
        'abechangeweb': 'alt.binaries.echange-web',
        'abmdfvost': 'alt.binaries.movies.divx.french.vost',
        'abdvdr': 'alt.binaries.dvdr',
        'abmzeromov': 'alt.binaries.movies.zeromovies',
        'abcfaf': 'alt.binaries.cartoons.french.animes-fansub',
        'abcfrench': 'alt.binaries.cartoons.french',
        'abgougouland': 'alt.binaries.gougouland',
        'abroger': 'alt.binaries.roger',
        'abtatu': 'alt.binaries.tatu',
        'abstvf': 'alt.binaries.series.tv.french',
        'abmdfreposts': 'alt.binaries.movies.divx.french.reposts',
        'abmdf': 'alt.binaries.movies.french',
        'abhdtvfrepost': 'alt.binaries.hdtv.french.repost',
        'abmmkv': 'alt.binaries.movies.mkv',
        'abf-tv': 'alt.binaries.french-tv',
        'abmdfo': 'alt.binaries.movies.divx.french.old',
        'abmf': 'alt.binaries.movies.french',
        'ab.movies': 'alt.binaries.movies',
        'a.b.french': 'alt.binaries.french',
        'a.b.3d': 'alt.binaries.3d',
        'ab.dvdrip': 'alt.binaries.dvdrip',
        'ab.welovelori': 'alt.binaries.welovelori',
        'abblu-ray': 'alt.binaries.blu-ray',
        'ab.bloaf': 'alt.binaries.bloaf',
        'ab.hdtv.german': 'alt.binaries.hdtv.german',
        'abmd': 'alt.binaries.movies.divx',
        'ab.ath': 'alt.binaries.ath',
        'a.b.town': 'alt.binaries.town',
        'a.b.u-4all': 'alt.binaries.u-4all',
        'ab.amazing': 'alt.binaries.amazing',
        'ab.astronomy': 'alt.binaries.astronomy',
        'ab.nospam.cheer': 'alt.binaries.nospam.cheerleaders',
        'ab.worms': 'alt.binaries.worms',
        'abcores': 'alt.binaries.cores',
        'abdvdclassics': 'alt.binaries.dvd.classics',
        'abdvdf': 'alt.binaries.dvd.french',
        'abdvds': 'alt.binaries.dvds',
        'abmdfrance': 'alt.binaries.movies.divx.france',
        'abmisc': 'alt.binaries.misc',
        'abnl': 'alt.binaries.nl',
        'abx': 'alt.binaries.x',
        'abdivxf': 'alt.binaries.divx.french'
    }

    urls = {
        'download': 'http://www.binnews.in/',
        'detail': 'http://www.binnews.in/',
        'search': 'http://www.binnews.in/_bin/search2.php',
    }

    http_time_between_calls = 4 # Seconds
    cat_backup_id = None

    nzbDownloaders = [NZBClub(), BinSearch(), NZBIndex()]

    def _search(self, movie, quality, results):
        MovieTitles = movie['info']['titles']
        moviequality = simplifyString(quality['identifier'])
        movieyear = movie['info']['year']
        if quality['custom']['3d']==1:
            threeD= True
        else:
            threeD=False
        if moviequality in ("720p","1080p","bd50"):
            cat1='39'
            cat2='49'
            minSize = 2000
        elif moviequality in ("dvdr"):
            cat1='23'
            cat2='48'
            minSize = 3000
        else:
            cat1='6'
            cat2='27'
            minSize = 500

        for MovieTitle in MovieTitles:
            try:
                TitleStringReal = str(MovieTitle.encode("latin-1").replace('-',' '))
            except:
                continue
            if threeD:
                TitleStringReal = TitleStringReal + ' 3d'
            data = 'chkInit=1&edTitre='+TitleStringReal+'&chkTitre=on&chkFichier=on&chkCat=on&cats%5B%5D='+cat1+'&cats%5B%5D='+cat2+'&edAge=&edYear='
            try:
                soup = BeautifulSoup( urllib2.urlopen(self.urls['search'], data), "html5lib" )
            except Exception, e:
                log.error(u"Error trying to load BinNewz response: "+e)
                return []

            tables = soup.findAll("table", id="tabliste")
            for table in tables:

                rows = table.findAll("tr")
                for row in rows:

                    cells = row.select("> td")
                    if (len(cells) < 11):
                        continue

                    name = cells[2].text.strip()
                    #filename = cells[5].contents[0]
                    testname=namer_check.correctName(name,movie)
                    #testfilename=namer_check.correctName(filename,movie)
                    if testname==0:# and testfilename==0:
                        continue
                    language = cells[3].find("img").get("src")

                    if not "_fr" in language and not "_frq" in language:
                        continue

                    detectedlang=''

                    if "_fr" in language:
                        detectedlang=' truefrench '
                    else:
                        detectedlang=' french '


                    # blacklist_groups = [ "alt.binaries.multimedia" ]
                    blacklist_groups = []

                    newgroupLink = cells[4].find("a")
                    newsgroup = None
                    if newgroupLink.contents:
                        newsgroup = newgroupLink.contents[0]
                        if newsgroup in self.allowedGroups:
                            newsgroup = self.allowedGroups[newsgroup]
                        else:
                            log.error(u"Unknown binnewz newsgroup: " + newsgroup)
                            continue
                        if newsgroup in blacklist_groups:
                            log.error(u"Ignoring result, newsgroup is blacklisted: " + newsgroup)
                            continue

                    filename =  cells[5].contents[0]

                    m =  re.search("^(.+)\s+{(.*)}$", name)
                    qualityStr = ""
                    if m:
                        name = m.group(1)
                        qualityStr = m.group(2)

                    m =  re.search("^(.+)\s+\[(.*)\]$", name)
                    source = None
                    if m:
                        name = m.group(1)
                        source = m.group(2)

                    m =  re.search("(.+)\(([0-9]{4})\)", name)
                    year = ""
                    if m:
                        name = m.group(1)
                        year = m.group(2)
                        if int(year) > movieyear + 1 or int(year) < movieyear - 1:
                            continue

                    m =  re.search("(.+)\((\d{2}/\d{2}/\d{4})\)", name)
                    dateStr = ""
                    if m:
                        name = m.group(1)
                        dateStr = m.group(2)
                        year = dateStr[-5:].strip(")").strip("/")

                    m =  re.search("(.+)\s+S(\d{2})\s+E(\d{2})(.*)", name)
                    if m:
                        name = m.group(1) + " S" + m.group(2) + "E" + m.group(3) + m.group(4)

                    m =  re.search("(.+)\s+S(\d{2})\s+Ep(\d{2})(.*)", name)
                    if m:
                        name = m.group(1) + " S" + m.group(2) + "E" + m.group(3) + m.group(4)

                    filenameLower = filename.lower()
                    searchItems = []
                    if qualityStr=="":
                        if source in ("Blu Ray-Rip", "HD DVD-Rip"):
                            qualityStr="brrip"
                        elif source =="DVDRip":
                            qualityStr="dvdrip"
                        elif source == "TS":
                            qualityStr ="ts"
                        elif source == "DVDSCR":
                            qualityStr ="scr"
                        elif source == "CAM":
                            qualityStr ="cam"
                        elif moviequality == "dvdr":
                            qualityStr ="dvdr"
                    if year =='':
                        year = '1900'
                    if len(searchItems) == 0 and qualityStr == str(moviequality):
                        searchItems.append( filename )
                    for searchItem in searchItems:
                        resultno=1
                        for downloader in self.nzbDownloaders:

                            log.info("Searching for download : " + name + ", search string = "+ searchItem + " on " + downloader.__class__.__name__)
                            try:
                                binsearch_result =  downloader.search(searchItem, minSize, newsgroup )
                                if binsearch_result:
                                    new={}

                                    def extra_check(item):
                                        return True

                                    qualitytag=''
                                    if qualityStr.lower() in ['720p','1080p']:
                                        qualitytag=' hd x264 h264 '
                                    elif qualityStr.lower() in ['dvdrip']:
                                        qualitytag=' dvd xvid '
                                    elif qualityStr.lower() in ['brrip']:
                                        qualitytag=' hdrip '
                                    elif qualityStr.lower() in ['ts']:
                                        qualitytag=' webrip '
                                    elif qualityStr.lower() in ['scr']:
                                        qualitytag=''
                                    elif qualityStr.lower() in ['dvdr']:
                                        qualitytag=' pal video_ts '

                                    new['id'] =  binsearch_result.nzbid
                                    new['name'] = name + detectedlang +  qualityStr + qualitytag + downloader.__class__.__name__
                                    new['url'] = binsearch_result.nzburl
                                    new['detail_url'] = binsearch_result.refererURL
                                    new['size'] = binsearch_result.sizeInMegs
                                    new['age'] = binsearch_result.age
                                    new['extra_check'] = extra_check

                                    results.append(new)

                                    resultno=resultno+1
                                    log.info("Found : " + searchItem + " on " + downloader.__class__.__name__)
                                    if resultno==3:
                                        break
                            except Exception, e:
                                log.error("Searching from " + downloader.__class__.__name__ + " failed : " + str(e) + traceback.format_exc())

    def download(self, url = '', nzb_id = ''):
        if 'binsearch' in url:
            data = {
            'action': 'nzb',
            nzb_id: 'on'
            }
            try:
                return self.urlopen(url, data = data, show_error = False)
            except:
                log.error('Failed getting nzb from %s: %s', (self.getName(), traceback.format_exc()))
                return 'try_next'
        else:
            values = {
                    'url' : '/'
            }
            data_tmp = urllib.urlencode(values)
            req = urllib2.Request(url, data_tmp )

            try:
                #log.error('Failed downloading from %s', self.getName())
                return urllib2.urlopen(req).read()
            except:
                log.error('Failed downloading from %s: %s', (self.getName(), traceback.format_exc()))

                return 'try_next'

config = [{
    'name': 'binnewz',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'nzb_providers',
            'name': 'binnewz',
            'description': 'Free provider, lots of french nzbs. See <a href="http://www.binnews.in/">binnewz</a>',
            'wizard': True,
            'icon': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAgRJREFUOI1t009rVFcYx/HPuffOTGYmMcZoEmNUkiJRSZRAC1ropuimuy6KuHHhShe+EF+CL8AX4LpQCgoiohhMMKKMqHRTtaJJ5k8nudfFnBkjzoEf5zk8PN/zO3+egFGMYX+MS9hFG604d/A/ulG7yFFkqOGgcuUuSJK32q0NPMMaNrE9RC10UxzCedX6767cqDu2MGV8YlFz62ed9iWVkYvy/IyimEUSFaKD3QwV7ENwapmlHymVU5126tNHVh9MW3s8bfXhOW8b16TpliR5otW8jm6GHiSEYOYoF076Zjx6x29/8OHfssZzNp6Ou3XzF8zicxYtZWBislfUKL4CFgIvd5mcYuowed7PjKOSGTYWwiAsij6srChmJI058Q6qyIYD9jgIIQzWxXygPtZPpUj6gGJv/V4HGoViPsLWt77bK9P7FDtg8zPr21RrX48wT3g11OcA0MG2oii8aXB4jiInK5FmSAcOGBUawwFvtFuJO7dpbLBynuM/UK0Jn0YolXtqNfn4vl/bRZ7pfcsXdrqX3f/rhgd/L+m0J8zMdZ1eKTn7U7C4zNg+yhX+ed2/syZ2AkZQ12umSRyI8wpOqdaXdTszRmocOR5Mz2bu/ZnL81/xIsTnyFCOsKpeg9ViPBo1jxMq1UVpEjS3r+K/Pe81aJQ0qhShlQiuxPxOtL+J1heOZZ0e63LUQAAAAABJRU5ErkJggg==',
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False,
                },
                {
                    'name': 'extra_score',
                    'advanced': True,
                    'label': 'Extra Score',
                    'type': 'int',
                    'default': 0,
                    'description': 'Starting score for each release found via this provider.',
                }
            ],
        },
    ],
}]
