from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyMarkup, replykeyboardmarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, callbackcontext
from threading import Thread
import telegram.error
from urllib.parse import quote
from os import getenv, unlink
from lectulandia import Lectulandia_scraper, bookDownload
from langLoader import langLoad


TELEGRAM_BOT_TOKEN = getenv("_TELEGRAM_BOT_TOKEN", "")
print(f"----------------------------- {TELEGRAM_BOT_TOKEN}------------------")

lectulandia = Lectulandia_scraper()

def runner(func, update, context):
	Thread(None, func, args=(update, context)).run()

def proc_send_to_tel(chat_iid, text, photo=None, parseMode="html", are_book=False, inlineK=None):
	if photo is None:
		rtext = ""
		if len(text) > 4096:

			text_aux = text.split("\n")
			while text_aux:
				roux = text_aux.pop(0)
				roux += "\n"
				if are_book and "📚" in text_aux[0]:
					roux += text_aux.pop(0)
					roux += "\n"

				if len(rtext) + len(roux) > 4096:
					bot.send_message(chat_id=chat_iid, text=rtext, parse_mode=parseMode)
					rtext = ""
				else: rtext += roux
		else: rtext = text

		if inlineK:
			bot.send_message(chat_id=chat_iid, reply_markup=inlineK, text=rtext, parse_mode=parseMode)
		else:
			bot.send_message(chat_id=chat_iid, text=rtext, parse_mode=parseMode)

def cmd_start(update, context):
	print("command start from", update.message.from_user.first_name)

def cmd_help(update, context):
	# user_lang = update.message.from_user.language_code
	# data_lang = langLoad(user_lang)
	print("command help from", update.message.from_user.first_name)

def cmd_lib_info(update, context):
	user_id = update.message.from_user.id
	user_lang = update.message.from_user.language_code
	data_lang = langLoad(user_lang)
	lib_info = lectulandia.get_lib_info(user_lang)
	if lib_info is not None:
		rtext = data_lang["library_info"]
		rtext += f":\n{lib_info}"
	else:
		rtext = data_lang["error_lib_info"]
	rtext = rtext.capitalize()
	bot.send_message(chat_id=user_id, text=rtext, are_book=True)

def cmd_weekly(update, context):
	user_id = update.message.from_user.id
	user_lang = update.message.from_user.language_code
	data_lang = langLoad(user_lang)
	url = lectulandia.weekly_url
	rtext = ""
	rdata = {}
	rinline = []
	rtext += f"<b>{data_lang['weekly']}</b>:"
	rtext += "\n\n"
	rdata = lectulandia.get_ot_info("", user_lang, burl=url)
	rtext += rdata["text"]

	rnav_next = rdata["nav_next"]
	if rnav_next:
		print(f"inlineK -> {rnav_next}")
		butt_text = data_lang["load_more"]
		rinline = InlineKeyboardMarkup([[InlineKeyboardButton(text=butt_text, callback_data=rnav_next)]])

	proc_send_to_tel(user_id, rtext, are_book=True, inlineK=rinline)

def cmd_monthly(update, context):
	user_id = update.message.from_user.id
	user_lang = update.message.from_user.language_code
	data_lang = langLoad(user_lang)
	url = lectulandia.monthly_url
	rtext = ""
	rdata = {}
	rinline = []
	rtext += f"<b>{data_lang['monthly']}</b>:"
	rtext += "\n\n"
	rdata = lectulandia.get_ot_info("", user_lang, burl=url)

	rtext += rdata["text"]
	rnav_next = rdata["nav_next"]
	print(rdata)
	if rnav_next:
		print(f"inlineK -> {rnav_next}")
		butt_text = data_lang["load_more"]
		rinline = InlineKeyboardMarkup([[InlineKeyboardButton(text=butt_text, callback_data=rnav_next)]])
	print(rinline)
	proc_send_to_tel(user_id, rtext, are_book=True, inlineK=rinline)

def cmd_lasts(update, context):
	user_id = update.message.from_user.id
	user_lang = update.message.from_user.language_code
	data_lang = langLoad(user_lang)
	url = lectulandia.lasts_url
	rtext = ""
	rdata = {}
	rinline = []
	rtext += f"<b>{data_lang['lasts']}</b>:"
	rtext += "\n\n"
	rdata = lectulandia.get_ot_info("", user_lang, burl=url)
	rtext += rdata["text"]
	rnav_next = rdata["nav_next"]

	if rnav_next:
		print(f"inlineK -> {rnav_next}")
		butt_text = data_lang["load_more"]
		rinline = InlineKeyboardMarkup([[InlineKeyboardButton(text=butt_text, callback_data=rnav_next)]])

	proc_send_to_tel(user_id, rtext, are_book=True, inlineK=rinline)

def proc_find(update, context):
	user_id = update.message.from_user.id
	user_lang = update.message.from_user.language_code
	chat_text = update.message.text.strip()
	data_lang = langLoad(user_lang)
	rtext = ""
	rdata = {}
	if len(chat_text) > 3:
		chat_text_quote = quote(chat_text)
		rdata = lectulandia.get_search_info(f"{chat_text_quote}/", user_lang)
		rtext += rdata["text"]
		# print(rtext)
	else:
		rtext += data_lang["error_find_length"]

	if not rtext:
		rtext += data_lang["warning_not_found"].format(chat_text)


	rnav_next = rdata["nav_next"]
	rinline = []
	if rnav_next:
		print(f"inlineK -> {rnav_next}")
		butt_text = data_lang["load_more"]
		rinline = InlineKeyboardMarkup([[InlineKeyboardButton(text=butt_text, callback_data=rnav_next)]])

	proc_send_to_tel(user_id, rtext, inlineK=rinline)

def inlinePrint(update, context):
	update.callback_query.answer()
	user_id = update.callback_query.message.chat.id
	toDelete = bot.send_message(chat_id=user_id, text="downloading")
	mess_iid = update.callback_query.message.message_id
	# chat_text = update.callback_query.message.text
	callback_data = update.callback_query.data
	print(callback_data)
	iid = callback_data.split("_")[1]
	url = lectulandia.db_get_url(iid)
	tbook = bookDownload(url, lectulandia.antuploadUrl)
	tbook.init()
	chat_text = "{}\n{}\n{}".format(tbook.name, tbook.size, tbook.uploaded)
	proc_send_to_tel(user_id, chat_text)
	tbook.download()
	bot.edit_message_text(chat_id=user_id, message_id=toDelete.message_id, text="sending")
	bot.send_document(chat_id=user_id, document=open(file="./books/{}".format(tbook.name), mode="rb"), caption=chat_text, parse_mode="html")
	bot.delete_message(chat_id=user_id, message_id=toDelete.message_id)
	unlink("./books/{}".format(tbook.name))

def proc_inline_query(update, context):
	update.callback_query.answer()
	user_id = update.callback_query.message.chat.id
	mess_iid = update.callback_query.message.message_id
	chat_text = update.callback_query.message.text
	callback_data = update.callback_query.data
	# print("person ->", dir(update.callback_query.message), "\n", update.callback_query.message.sender_chat, update.callback_query.message.chat)
	# print("data ->", user_id)
	# print(chat_text)
	schat_text = callback_data.split("_")
	opt = schat_text[1]
	iid = schat_text[2]
	ind = schat_text[3]
	user_lang = schat_text[4]
	data_lang = langLoad(user_lang)
	rtext = ""
	rdata = {}
	rinline = []
	if opt == "morebooks":
		rnav_next = lectulandia.get_ot_nav(iid, user_lang, ind)
		url = f"{lectulandia.db_get_url(iid)}page/{ind}"
		print("url -> ", url)
		rdata = lectulandia.get_ot_info(None, user_lang, burl=url)
		rtext += rdata["text"]
		print("rtext ->", rtext)
		# proc_send_to_tel(user_id, chat_text, are_book=True)
		bot.edit_message_reply_markup(user_id, mess_iid)
		if rnav_next:
			print(f"inlineK -> {rnav_next}")
			butt_text = data_lang["load_more"]
			rinline = InlineKeyboardMarkup([[InlineKeyboardButton(text=butt_text, callback_data=rnav_next)]])

	proc_send_to_tel(user_id, rtext, inlineK=rinline)

def proc_r_info(update, context):
	user_id = update.message.from_user.id
	user_lang = update.message.from_user.language_code
	chat_text = update.message.text
	data_lang = langLoad(user_lang)
	cover_url =""
	rtext = ""
	rdata = {}
	rinline = []
	try:
		comm = chat_text.split("_")
		opt = str(comm[0])[1:]
		iid = int(comm[1])
		# print(opt, iid)
	except:
		rtext += data_lang["error_dont_fuck"]
	else:
		this_url = lectulandia.db_get_url(iid)
		if opt == "i":

			if this_url.startswith(f"{lectulandia.lectulandiaUrl}/book/")\
			and this_url is not f"{lectulandia.lectulandiaUrl}/book/":
				ret_info = lectulandia.get_b_info(iid)
				cover_url += ret_info[0]
				rtext += ret_info[1]
				keis = []
				for dow in ret_info[2]:
					keis.append(InlineKeyboardButton(text=dow.name, callback_data="dd_{}".format(dow.value)))
				bot.send_photo(chat_id=user_id, photo=cover_url, reply_markup=InlineKeyboardMarkup([keis]), caption=rtext, parse_mode="html")

				return

			elif this_url.startswith(f"{lectulandia.lectulandiaUrl}/serie/")\
			and this_url is not f"{lectulandia.lectulandiaUrl}/serie/"\
			or this_url.startswith(f"{lectulandia.lectulandiaUrl}/autor/")\
			and this_url is not f"{lectulandia.lectulandiaUrl}/autor/"\
			or this_url.startswith(f"{lectulandia.lectulandiaUrl}/genero/")\
			and this_url is not f"{lectulandia.lectulandiaUrl}/genero/":
				rdata = lectulandia.get_ot_info(iid, user_lang)
				rtext += rdata["text"]
				rnav_next = rdata["nav_next"]
				if rnav_next:
					print(f"inlineK -> {rnav_next}")
					butt_text = data_lang["load_more"]
					rinline = InlineKeyboardMarkup([[InlineKeyboardButton(text=butt_text, callback_data=rnav_next)]])

		elif opt == "s":
			if this_url.startswith(f"{lectulandia.lectulandiaUrl}/book/")\
			and this_url is not f"{lectulandia.lectulandiaUrl}/book/":
				rtext += lectulandia.get_b_description(iid)
		else:
			rtext += "..."

	proc_send_to_tel(user_id, rtext, inlineK=rinline)
	# bot.send_message(chat_id=user_id, text=rtext, parse_mode="html")


def cmd_process(update, context):
	chat_text = update.message.text
	command = chat_text.split(" ")[0][1:]
	# args = chat_text.split(" ")[1:]
	if command == "start":
		runner(cmd_start, update, context)
	elif command == "help":
		runner(cmd_help, update, context)
	elif command == "lib_info":
		runner(cmd_lib_info, update, context)
	elif command == "weekly":
		runner(cmd_weekly, update, context)
	elif command == "monthly":
		runner(cmd_monthly, update, context)
	elif command == "lasts":
		runner(cmd_lasts, update, context)
	elif command.startswith("i_")\
	or command.startswith("s_"):
		runner(proc_r_info, update, context)
	else:
		print(f"Error: Command {command} don't found")

def inline_query(update, context):
	runner(proc_inline_query, update, context)

def find_process(update, context):
	runner(proc_find, update, context)

if __name__ == "__main__":
	updater = Updater(token=TELEGRAM_BOT_TOKEN)
	bot = updater.bot
	dispatcher = updater.dispatcher
	dispatcher.add_handler(MessageHandler(Filters.command, callback=cmd_process))
	dispatcher.add_handler(MessageHandler(Filters.text, callback=find_process))
	dispatcher.add_handler(CallbackQueryHandler(callback=inline_query, pattern="iqh_"))
	dispatcher.add_handler(CallbackQueryHandler(callback=inlinePrint, pattern="dd_"))
	updater.start_polling(drop_pending_updates=True)
	print("Polling!!!")
	updater.idle()
