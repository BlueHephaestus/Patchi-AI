import re, sys, os
#TODO:
#remove the names when checking for matching questions
#set cap of responses after original question to search, save time
#improve method of getting questions and responses
#need to keep names of askers in questions, but not responses
#global constant file paths:


def make_base():
	log = open(log_path, 'r')
	name_log_raw = open(name_log_raw_path, 'w')
	msg_log_raw = open(msg_log_raw_path, 'w')
	for line in log:
		#check to make sure it's a message, if it can't find a sender then do nothing with it
		if '<' in line and '>' in line and'NICK' not in line and "===" not in line:
			if "[" in line[:8] and "]" in line[:8]:
				line = line.replace(line[:8], '')
			msg = line.strip()
			msg += '\n'
			msg_log_raw.write(msg.lower())
			#print msg
			if '\t' in line:
				msg = re.split(r'\t+',line)
			else:
				msg = re.split('>', line)
			#msg[0] = msg[0] 
			if len(msg) <= 1:	
				print msg
				break
				#sys.exit()
			
			#msg[1] = msg[1] 
			
			names_arr.add(msg[0].lower())
			msgs_arr.append(msg[1].lower())
	log.close()
	
	name_log_raw = open(name_log_raw_path, 'r')
	msg_log_raw = open(msg_log_raw_path, 'r')
	
	u_names = set()
	msg_arr = set()
	name_arr = set()
	ref_names_raw = set()
	ref_names = set()
	
	#gets the unique names
	for name in names_arr:
		if name.find('*') >= 0:
			pass
		elif name not in u_names:
			name = re.sub('[<>}]', '', name)
			u_names.add(name.strip())
	"""u_names is an array of users that have sent a message in logs, no dupes
	msgs_arr is an array of the messages sent by these users
	the msg log has all the messages sent by users
	the ref_names array has all the referenced names, usually in responses"""
	#u_names.remove('')
	#gets the names referenced by users
	for msg in msg_log_raw:
		for word in msg.split():
			if word.endswith(':') or word.endswith(','):
				#word += '\n'
				ref_names_raw.add(word.strip())	
	
	name_log_raw.close()
	msg_log_raw.close()
	for msg in ref_names_raw:
		for name in u_names:
			msg = re.sub('[:,]', '', msg)
			if name in msg:
				ref_names.add(name)
	return ref_names

def log_question(ref_names):
	q_dict = {}
	#messages is messages with usernames of senders,
	#msgs arr is messages without them
	messages = open(msg_log_raw_path).readlines()
	for msg in range(len(messages)):
		if ('?' in messages[msg]): 
			question = messages[msg].strip()
			q_index = msg
			q_dict = log_response(q_index, question, messages, ref_names)
			
	write_dict(q_dict)
def log_response(q_index, question, messages, ref_names):
	#searches through msgs array so as not to confuse usernames with referencing names
	for msg in range(q_index + 1, len(msgs_arr)):
		for ref_name in ref_names:
			if ref_name in msgs_arr[msg] and ref_name in question:
				if '\t' in question:
					question = re.split(r'\t+',question)
				else:
					question = re.split('>', question)
				question = question[1]
				question = remove_ref_names(question, ref_names)
				question = question.replace("  ", " ")
				response = msgs_arr[msg]
				response = re.sub(ref_name, '', response)
				response = re.sub('[:,]', '', response)
				response = response.rstrip()
				response = response.lstrip(' ')
				response = remove_ref_names(response, ref_names)
				#now that response is successfully stripped, add to dict
				#where checking if question/response is similar will be done
				
				#check if question is a duplicate, if so, then log new response
				#need to work with is_similar function when made.
				for dict_question in q_dict:
					if question == dict_question:
						q_dict[dict_question].append(response)
				else:
					q_dict[question] = []
					q_dict[question].append(response)
					
				print "Q-R #: ", len(q_dict)
				return q_dict
	return q_dict
def dictprint(dict):
	for key in dict:
		print key, dict[key]
		
#need to use this?
def remove_ref_names(msg, ref_names):
	while True:
		check = msg
		for name in ref_names:
			if name in msg:
				msg = msg.replace(name, '')
		if msg == check:
			return msg

"""def parse_msg(msg):
	pass
def parse_qr():
	qr_log_path = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\##programming_qr.log"

	qr_log = open(qr_log_path, 'r')
	#write better so parsing is easier
	for line in qr_log.readlines():
		line = line.split('\t')
		question = line[0]
		response_arr = line[1]"""
		
def write_dict(q_dict):
	#write the dictionary to the log
	qr_log = open(qr_log_path, 'w')
	for key, val in q_dict.items():
		line = '%s\t%s\n' %(key, val[0])
		qr_log.write(line)
	#sys.exit()
	
"""def watch_chat():
	qr_dict = parse_qr()
	while True:
		user_msg = raw_input("")"""
		

q_dict = {}
def full_exec():
	ref_names = make_base()
	log_question(ref_names)

qr_log_dir = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\"
qr_logs = []
for logs in os.walk(qr_log_dir):
	for log in range(2, len(logs)):
		for log in logs[log]:
			if "_" not in log and "#" in log:
				#Currently set to read through the irclogs.ubuntu.com logs, which are saved in text form
				#TODO: if text file then do all the stuffs accordingly, and if log file do that too, so that they can all be in same file system.
				print "Extracting from %s..." % log
				if '.txt' in log:
					log_file = re.sub('.txt', '', log)
					log_type = ".txt"
				elif '.log' in log:
					log_file = re.sub('.log', '', log)
					log_type = ".log"
				log_path = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\%s%s" % (log_file, log_type)
				name_log_raw_path = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\%s_names%s" % (log_file, log_type)
				name_log_path = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\%s_u_names%s" % (log_file, log_type)
				msg_log_raw_path = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\%s_msgs%s" % (log_file, log_type)
				msg_log_path = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\%s_ref_names%s" % (log_file, log_type)
				qr_log_path = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\qr\\%s_qr2%s" % (log_file, log_type)
				#qr_log_path = "%s%s" % (qr_log_dir, log)
				#qr_log = open(qr_log_path, 'r')
				#log_file = sys.argv[1]
				

				qr_log = open(qr_log_path, 'a')
				names = set()
				names_arr = set()
				msgs_arr = []
				name_log_raw = open(name_log_raw_path, 'w')
				msg_log_raw = open(msg_log_raw_path, 'w')
				full_exec()














