
# This is just the LogWatcher class; scroll to the bottom for the actual
# script code, which is pretty short.

"""
Real-time log files watcher supporting log rotation.
Works with Python >= 2.6 and >= 3.2, on both POSIX and Windows.

Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
License: MIT

"""
#TODO
#console instead of irc
#remove names in log_learn->Done
#randomly choose from array of responses->Done
#is_similar function for questions and responses
#markov chains for questions/responses
import os, time, errno, stat, sys, re, socket, string, random

SERVER = 'chat.freenode.net'
PORT = 6667
NICKNAME = 'patchi'
CHANNEL = sys.argv[1]
response = ''
#open a socket to handle the connection
IRC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#open a connection with the server
def irc_conn():
    IRC.connect((SERVER, PORT))

#simple function to send data through the socket
def send_data(command):
    IRC.send(command + '\n')
def send_channel(msg):
	IRC.send("PRIVMSG %s :%s\n" %(CHANNEL, msg))
#join the channel
def join(channel):
    send_data("JOIN %s" % channel)

#send login data (customizable)
def login(nickname, username='DarkElement', password = None, realname='DarkElement', hostname='rajaniemi', servername='Server'):
    send_data("USER %s %s %s %s" % (username, hostname, servername, realname))
    send_data("NICK " + nickname)
def full_join_channel():
	irc_conn()
	login(NICKNAME)
	join(CHANNEL)
	print 'Joining %s' % CHANNEL
	while True:
		buffer = IRC.recv(1024)
		msg = string.split(buffer)
		if msg[0] == "PING": #check if server have sent ping command
			send_data("PONG %s" % msg[1]) #answer with pong as per RFC 1459
			print 'channel %s joined' % CHANNEL
			send_channel("Hello everyone")
			return
full_join_channel()

	
class LogWatcher(object):
    """Looks for changes in all files of a directory.
    This is useful for watching log file changes in real-time.
    It also supports files rotation.

    Example:

    >>> def callback(filename, lines):
    ...     print(filename, lines)
    ...
    >>> lw = LogWatcher("/var/log/", callback)
    >>> lw.loop()
    """

    def __init__(self, folder, callback, extensions=["log"], tail_lines=0,
                       sizehint=1048576):
        """Arguments:

        (str) @folder:
            the folder to watch

        (callable) @callback:
            a function which is called every time one of the file being
            watched is updated;
            this is called with "filename" and "lines" arguments.

        (list) @extensions:
            only watch files with these extensions

        (int) @tail_lines:
            read last N lines from files being watched before starting

        (int) @sizehint: passed to file.readlines(), represents an
            approximation of the maximum number of bytes to read from
            a file on every ieration (as opposed to load the entire
            file in memory until EOF is reached). Defaults to 1MB.
        """
        self.folder = os.path.realpath(folder)
        self.extensions = extensions
        self._files_map = {}
        self._callback = callback
        self._sizehint = sizehint
        assert os.path.isdir(self.folder), self.folder
        assert callable(callback), repr(callback)
        self.update_files()
        for id, file in self._files_map.items():
            file.seek(os.path.getsize(file.name))  # EOF
            if tail_lines:
                try:
                    lines = self.tail(file.name, tail_lines)
                except IOError as err:
                    if err.errno != errno.ENOENT:
                        raise
                else:
                    if lines:
                        self._callback(file.name, lines)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def loop(self, interval=0.1, blocking=True):
        """Start a busy loop checking for file changes every *interval*
        seconds. If *blocking* is False make one loop then return.
        """
        # May be overridden in order to use pyinotify lib and block
        # until the directory being watched is updated.
        # Note that directly calling readlines() as we do is faster
        # than first checking file's last modification times.
        while True:
            self.update_files()
            for fid, file in list(self._files_map.items()):
                self.readlines(file)
            if not blocking:
                return
            time.sleep(interval)

    def log(self, line):
        """Log when a file is un/watched"""
        print(line)

    def listdir(self):
        """List directory and filter files by extension.
        You may want to override this to add extra logic or globbing
        support.
        """
        ls = os.listdir(self.folder)
        if self.extensions:
            return [x for x in ls if os.path.splitext(x)[1][1:] \
                                           in self.extensions]
        else:
            return ls

    @classmethod
    def open(cls, file):
        """Wrapper around open().
        By default files are opened in binary mode and readlines()
        will return bytes on both Python 2 and 3.
        This means callback() will deal with a list of bytes.
        Can be overridden in order to deal with unicode strings
        instead, like this:

          import codecs, locale
          return codecs.open(file, 'r', encoding=locale.getpreferredencoding(),
                             errors='ignore')
        """
        return open(file, 'rb')

    @classmethod
    def tail(cls, fname, window):
        """Read last N lines from file fname."""
        if window <= 0:
            raise ValueError('invalid window value %r' % window)
        with cls.open(fname) as f:
            BUFSIZ = 1024
            # True if open() was overridden and file was opened in text
            # mode. In that case readlines() will return unicode strings
            # instead of bytes.
            encoded = getattr(f, 'encoding', False)
            CR = '\n' if encoded else b'\n'
            data = '' if encoded else b''
            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            block = -1
            exit = False
            while not exit:
                step = (block * BUFSIZ)
                if abs(step) >= fsize:
                    f.seek(0)
                    newdata = f.read(BUFSIZ - (abs(step) - fsize))
                    exit = True
                else:
                    f.seek(step, os.SEEK_END)
                    newdata = f.read(BUFSIZ)
                data = newdata + data
                if data.count(CR) >= window:
                    break
                else:
                    block -= 1
            return data.splitlines()[-window:]

    def update_files(self):
        ls = []
        for name in self.listdir():
            absname = os.path.realpath(os.path.join(self.folder, name))
            try:
                st = os.stat(absname)
            except EnvironmentError as err:
                if err.errno != errno.ENOENT:
                    raise
            else:
                if not stat.S_ISREG(st.st_mode):
                    continue
                fid = self.get_file_id(st)
                ls.append((fid, absname))

        # check existent files
        for fid, file in list(self._files_map.items()):
            try:
                st = os.stat(file.name)
            except EnvironmentError as err:
                if err.errno == errno.ENOENT:
                    self.unwatch(file, fid)
                else:
                    raise
            else:
                if fid != self.get_file_id(st):
                    # same name but different file (rotation); reload it.
                    self.unwatch(file, fid)
                    self.watch(file.name)

        # add new ones
        for fid, fname in ls:
            if fid not in self._files_map:
                self.watch(fname)

    def readlines(self, file):
        """Read file lines since last access until EOF is reached and
        invoke callback.
        """
        while True:
            lines = file.readlines(self._sizehint)
            if not lines:
                break
            self._callback(file.name, lines)

    def watch(self, fname):
        try:
            file = self.open(fname)
            fid = self.get_file_id(os.stat(fname))
        except EnvironmentError as err:
            if err.errno != errno.ENOENT:
                raise
        else:
            self.log("watching logfile %s" % fname)
            self._files_map[fid] = file

    def unwatch(self, file, fid):
        # File no longer exists. If it has been renamed try to read it
        # for the last time in case we're dealing with a rotating log
        # file.
        self.log("un-watching logfile %s" % file.name)
        del self._files_map[fid]
        with file:
            lines = self.readlines(file)
            if lines:
                self._callback(file.name, lines)

    @staticmethod
    def get_file_id(st):
        if os.name == 'posix':
            return "%xg%x" % (st.st_dev, st.st_ino)
        else:
            return "%f" % st.st_ctime

    def close(self):
        for id, file in self._files_map.items():
            file.close()
        self._files_map.clear()


# Actual script code

class MyLogWatcher(LogWatcher):
	# Overriding log so it doesn't spew log messages whenever a file
	# becomes watched/unwatched
	def log(self, line):
		pass

if __name__ == '__main__':
	dir_to_watch =  "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\"#+sys.argv[1] # the chosen channel, currently monitoring all channels for testing

	def callback(filename, lines):
		response = None
		relpath = os.path.relpath(filename, dir_to_watch)
		if '<' not in lines:
			msg = re.split(r'\t+',lines[0])
			if '*' not in msg[0]:
				#TODO: fix problem with not splitting sometimes?
				print msg
				if len(msg) == 1:
					msg = msg[0].rstrip()
				else:
					msg = msg[1].rstrip()
				msg = msg.lower()
				response = check_logs(msg)
				if response != '' and response != None:
					print 'sending response'
					send_channel(response)
					response = ''
					return
					#send a message
		#msg is 2 element array , ['sender', 'message text']
		#if user is speaking to someone'<sender> Recipient:
		#check if one word before ':'
			#need to check for users in channel and if go through each username to see if sender is speaking to someone
			
	def check_logs(msg):
		qr_log_dir = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\qr\\"
		#temp_log_path = "C:\\Users\\Steve\\Desktop\\Programming\\Challenges\\patchi\\logs\\temp.log"
		qr_logs = []
		#I CANT THINK OF ANY MORE LOG VARIABLE NAMES Q_Q
		for logs in os.walk(qr_log_dir):
			for log in range(2, len(logs)):
				for log in logs[log]:
					qr_log_path = "%s%s" % (qr_log_dir, log)
					qr_log = open(qr_log_path, 'r')
					#temp = open(temp_log_path, 'a')
					qr_dict = {}
					
					#write better so parsing is easier with multiple responses to same question, but for now using one 
					if ('?' in msg): #and ('can i' in msg or 'who' in msg or 'what' in msg or 'when' in msg or 'where' in msg or 'why' in msg or 'how' in msg):
						
						for line in qr_log:
							line = re.split(r'\t+',line)
							question = line[0]
							response_arr = line[1].rstrip()
							response_arr = re.sub(r'\[\]', '', response_arr)
							#need to figure out how to parse the array of the responses
							qr_dict[question] = []
							qr_dict[question].append(response_arr)
						#qr_dict is now the questions and responses of the log
						response_arr = []
						for question in qr_dict:
							if msg in question:
								for response in qr_dict[question]:
									response_arr.append(response)
						if response_arr:
							print len(response_arr)
							#will choose random response if more than one.
							rand_response = random.randint(0, len(response_arr) - 1)
							
							response = response_arr[rand_response] 
							print 'QUESTION: ', msg
							print 'RESPONSE: ', response
							
							return response
		
		
		
		
		"""#msg_fmt = 'The following %d line(s) were added to the file %s'
		#print
		#print msg_fmt % (len(lines), relpath)
		raw = lines[0]
		msg = ['', '', '']
		raw = raw.split(" <")
		#print raw
		msg[2] = raw[1]
		temp = raw[0].split(" <")
		msg[0] = raw[0]
		msg[1] = temp[0]
		msg[2] = temp[1]
		msg = re.sub('\s+',' ',msg)"""

		
		
	
	lw = MyLogWatcher(dir_to_watch, callback)

	lw.loop()
	