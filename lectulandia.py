from json import load as json_load
from lxml.html import fromstring, tostring
from cloudscraper import create_scraper
from urllib.parse import quote
from langLoader import langLoad
from sqlite3 import connect, IntegrityError
from sqlite3 import OperationalError as sqlite3OperationalError
from os import mkdir

from jscustom import Variable, getJsVariables

with open("config.json", "r") as configjson:
	CONFIG = json_load(configjson)

WEB_HEADERS = CONFIG["WEB_HEADERS"]
WEB_BROWSER = CONFIG["WEB_BROWSER"]
LECTULANDIA_URL = CONFIG["LECTULANDIA_URL"]
ANTUPLOAD_URL = CONFIG["ANTUPLOAD_URL"]

scraper = create_scraper(browser=WEB_BROWSER)

class FileDescription:
	def __init__(self, name, size, uploaded):
		self.name = name
		self.size = size
		self.uploaded = uploaded

class bookPage:
	def __init__(self, url):
		self.url = url

	def init(self):
		self.lectulandiaUrl = "/".join(self.url.split("/")[:3])
		self.authorList = []
		self.genreList = []
		self.downloadList = []
		pageTree = fromstring(html=scraper.get(self.url).content)
		self.imageUrl = pageTree.get_element_by_id("cover").xpath('./img')[0].attrib["src"]
		self.imageUrl = self.imageUrl.removesuffix("big.jpg") + "small.jpg"
		self.name = pageTree.get_element_by_id("title")[0].text
		try:
			serie = pageTree.get_element_by_id("serie")
			self.serie = Variable(serie.xpath('./a')[0].text, serie.xpath('./a')[0].attrib["href"])
			self.bookNumber = serie.xpath('./span')[0].strip()[1]
		except:
			self.serie = None
			self.bookNumber = None

		for element in pageTree.get_element_by_id("autor"):
			if element.tag == "a":
				aurl = element.attrib["href"].removeprefix("/")
				if not aurl.__contains__(LECTULANDIA_URL): aurl = f"{LECTULANDIA_URL}/{aurl}"
				self.authorList.append({"name": element.text, "url": aurl})
		if len(self.authorList) > 5: self.authorList = self.authorList[:4]

		for element in pageTree.get_element_by_id("genero"):
			if element.tag == "a":
				self.genreList.append({"genre": element.text, "url": f"{self.lectulandiaUrl}{element.attrib['href']}"})
		if len(self.genreList) > 5: self.genreList = self.genreList[:4]

		self.shortDescription = pageTree.xpath('//*[@property="og:description"]')[0].attrib["content"]
		self.longDescription = pageTree.get_element_by_id("sinopsis").text_content()
		self.longDescription = self.longDescription.strip("\n").replace(". ", ".\n\n")
		for element in pageTree.get_element_by_id("downloadContainer"):
			self.downloadList.append(Variable(element.xpath('./input')[0].attrib["value"], "{}{}".format(self.lectulandiaUrl, element.attrib["href"])))

	def print(self):
		print(self.name)
		print(self.url)
		print(self.imageUrl)
		print(self.serie)
		print(self.bookNumber)
		print(self.authorList)
		print(self.genreList)
		for download in self.downloadList:
			print(download.name, download.value)

		print(self.shortDescription)

class bookDownload:
	def __init__(self, url, antuploadUrl):
		self.url = url
		self.antuploadUrl = antuploadUrl

	def init(self):
		try: mkdir("books")
		except: pass

		self.lectulandiaUrl = "/".join(self.url.split("/")[:3])
		self.antuploadUrl = "/".join(self.antuploadUrl.split("/")[:3])
		self.linkCode = None
		self.name = None
		self.size = None
		self.uploaded = None
		pageTree = fromstring(html=scraper.get(self.url).content)
		for script in pageTree.xpath('//*/script'):
			if script.text is not None and "linkCode" in script.text:
				for variable in getJsVariables(script.text):
					if variable.name == "linkCode":
						self.linkCode = variable.value
		pageTree = fromstring(html=scraper.get("{}/file/{}".format(self.antuploadUrl, self.linkCode)).content)
		self.directUrl = "{}{}".format(self.antuploadUrl, pageTree.get_element_by_id("downloadB").attrib["href"])
		FDescription = {"name": "", "size": "", "uploaded": ""}
		for info in pageTree.get_element_by_id("fileDescription").xpath('./p'):
			if len(info.getchildren()) == 1:
				if "Name" in info.xpath('./span')[0].text:
					self.name = info.xpath('./span')[0].tail.strip("\n").strip()
				elif "Size" in info.xpath('./span')[0].text:
					self.size = info.xpath('./span')[0].tail.strip("\n").strip()
				elif "Uploaded" in info.xpath('./span')[0].text:
					self.uploaded = info.xpath('./span')[0].tail.strip("\n").strip()
		self.fileDescription = FileDescription(FDescription["name"], FDescription["size"], FDescription["uploaded"])

	def download(self):
		with open(file="./books/{}".format(self.name), mode="wb") as binaryFile, scraper.get(url=self.directUrl, stream=True) as requiredFile:
			for buff in requiredFile.iter_content(chunk_size=1024):
				if buff: binaryFile.write(buff)


class cardBook:
	def __init__(self, name: Variable, serie: Variable | None, authorList: list):
		self.name = name
		self.serie = serie
		self.authorList = authorList


class Lectulandia_scraper():
	def __init__(self):
		# self.base_url = scraper.get(LECTULANDIA_URL).url.removesuffix("/")
		self.lectulandiaUrl = LECTULANDIA_URL.removesuffix("/")
		self.antuploadUrl = ANTUPLOAD_URL.removesuffix("/")
		self.weekly_url = f"{self.lectulandiaUrl}/compartidos-semana/"
		self.monthly_url = f"{self.lectulandiaUrl}/compartidos-mes/"
		self.lasts_url = f"{self.lectulandiaUrl}/book/"
		conn = connect("lec.db")
		cur = conn.cursor()
		try:
			cur.execute("CREATE TABLE lec_url (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE)")
			conn.commit()
		except sqlite3OperationalError: print("TABLE already exist")
		cur.close()
		conn.close()

	def get_lib_info(self, lang):
		data_lang = langLoad(lang)
		page = fromstring(html=scraper.get(self.lectulandiaUrl).content)
		rtext = ""
		for el in page.get_element_by_id("counterSection"):

			if el.getchildren()[1].text == "libros disponibles":
				rtext = data_lang["books"].format(el.getchildren()[0].text)
				rtext += "\n"

			elif el.getchildren()[1].text == "autores":
				rtext += data_lang["authors"].format(el.getchildren()[0].text)
				rtext += "\n"

			elif el.getchildren()[1].text == "comentarios":
				rtext += data_lang["comments"].format(el.getchildren()[0].text)
				rtext += "\n"

		return rtext

	def get_search_info(self, text, lang):
		burl = f"{self.lectulandiaUrl}/search/{text}"
		page = fromstring(html=scraper.get(burl).content)
		rdata = {"text": "", "nav_next": ""}
		get_books = True
		get_nav = True
		for el in page.get_element_by_id("main"):
			if el.tag == "div" and "content-wrap" in el.classes:
				icon = ""
				if "Autores" in el.getchildren()[0][0].text: icon += "👩🏼‍💻"
				elif "Series" in el.getchildren()[0][0].text: icon += "📚"
				for li in el.getchildren()[0]:
					if li.tag == "div":
						for ue in li.getchildren()[0]:
							if ue.tag == "li":
								name = ue.getchildren()[0].text
								url = ue.getchildren()[0].attrib["href"]
								iid = self.db_get_id(f"{self.lectulandiaUrl}{url}")
								rdata["text"] += f"{icon} {name} /i_{iid}"
								rdata["text"] += "\n"
				rdata["text"] += "\n"

			elif el.tag == "article" and "card" in el.classes and get_books:
				iid = self.db_get_id(burl)
				rdata["text"] += self.get_ot_info(iid, lang, page=page)["text"]
				get_books = False

			elif el.tag == "div" and "page-nav" in el.classes and get_nav:
				iid = self.db_get_id(burl)
				rdata["nav_next"] += self.get_ot_nav(iid, lang, 1, page=page)
				print(rdata["nav_next"])
				get_nav = False

		return rdata.copy()

	def get_b_info(self, iid):
		rtext = ""
		biid = iid
		url = self.db_get_url(iid)
		tbook = bookPage(url)
		tbook.init()
		tbook.print()
		rtext += "📖 <b>{}</b>\n\n".format(tbook.name)
		for author in tbook.authorList:
			aname = author["name"]
			aurl = author["url"]
			aiid = self.db_get_id(aurl)
			rtext += f"✍ {aname} /i_{aiid}\n"

		rtext +="\n"

		for genre in tbook.genreList:
			gname = genre["genre"]
			gurl = genre["url"]
			giid = self.db_get_id(gurl)
			rtext += f"🏷 {gname} /i_{giid}\n"

		rtext +="\n"
		rtext += f"💬 {tbook.shortDescription} /s_{biid}"

		downloadIidList = []
		for download in tbook.downloadList:
			downloadIidList.append(Variable(download.name, self.db_get_id(download.value)))
		return (tbook.imageUrl, rtext, downloadIidList)


	def get_b_description(self, iid):
		url = self.db_get_url(iid)
		page = fromstring(html=scraper.get(url).content)
		rtext = ""
		description = ""
		description += page.get_element_by_id("sinopsis").text_content().strip("\n").replace(". ", ".\n\n")
		rtext = f"💬 {description}"
		# print(rtext)
		return rtext

	def get_ot_info(self, iid, lang, page=None, burl=None):
		if burl is None:
			burl = self.db_get_url(iid)
		else:
			biid = self.db_get_id(burl)

		# data_lang = lang_load(lang)
		if page is None:
			page = fromstring(html=scraper.get(burl).content)

		rdata = {"text": "", "nav_next": ""}
		get_nav = True

		for el in page.get_element_by_id("main"):
			if el.tag == "article" and "card" in el.classes:

				for it in el.getchildren():
					if it.tag == "div":
						title = it.getchildren()[0][0].attrib["title"]
						url = it.getchildren()[0][0].attrib["href"]
						iid = self.db_get_id(f"{self.lectulandiaUrl}{url}")
						rdata["text"] += f"📖 {title} /i_{iid}"
						rdata["text"] += "\n"

						if "subdetail" in it.getchildren()[2].classes:
							serie = it.getchildren()[2][0].attrib["title"]
							url = it.getchildren()[2][0].attrib["href"]
							iid = self.db_get_id(f"{self.lectulandiaUrl}{url}")
							rdata["text"] += f"└╴📚<i>{serie}</i> /i_{iid}"
							rdata["text"] += "\n"
						else: pass # rtext += "\n"

			elif el.tag == "div" and "page-nav" in el.classes and get_nav:
				iid = self.db_get_id(burl)
				rdata["nav_next"] += self.get_ot_nav(iid, lang, 1, page=page)
				print(rdata["nav_next"])
				get_nav = False

		return rdata

	def get_ot_nav(self, iid, lang, ind, page=None, url=None):
		ind = int(ind)
		if url is None:
			url = self.db_get_url(iid)
		else:
			iid = self.db_get_id(f"{self.lectulandiaUrl}{url}")

		# data_lang = lang_load(lang)

		if page is None:
			page = fromstring(html=scraper.get(url).content)

		rtext = ""

		for el in page.get_element_by_id("main"):
			if el.tag == "div" and "page-nav" in el.classes:
				for bu in el.getchildren():
					if bu.tag == "a" and "next" in bu.classes:
						rtext += f"iqh_morebooks_{iid}_{ind + 1}_{lang}"
						return rtext
		return rtext




	def db_get_id(self, url):
		conn = connect("lec.db")
		cur = conn.cursor()
		rvar = []
		try:
			cur.execute("INSERT INTO lec_url VALUES (NULL, ?)", (url,))
			conn.commit()
			cur.execute("SELECT * FROM lec_url WHERE url = ?", (url,))
			rvar = cur.fetchone()
		except IntegrityError:
			cur.execute("SELECT * FROM lec_url WHERE url = ?", (url,))
			rvar = cur.fetchone()
		finally:
			cur.close()
			conn.close()
			return rvar[0]

	def db_get_url(self, iid):
		conn = connect("lec.db")
		cur = conn.cursor()
		rvar = []
		try:
			cur.execute("SELECT * FROM lec_url WHERE id = ?", (iid,))
			rvar = cur.fetchone()
			cur.close()
			conn.close()
			return rvar[1]
		except Exception as exc:
			print(exc)
			return ""

	def get_inf(self):
		return [self.lectulandiaUrl, self.weekly_url, self.monthly_url, self.lasts_url]
