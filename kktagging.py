# -*- coding: utf-8 -*-
"""
KK MP3 Tagging Tool

使用前提為必需讓 KKBOX 下載的音樂無加密
YHLi
"""

import sqlite3, getopt, sys, os.path
import plistlib, subprocess
import hashlib

try:
	from tagger import *
except:
	print "you need to install 'pytagger' library from 'http://pypi.python.org/pypi/pytagger'"
	sys.exit(2)

def usage():
	print """
		-v verbose
		-o output directory
		-d sqlite database
		-p plist file
		-s system serial
	"""
	
def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "vo:d:p:")
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
	
	downloaded_music_path = os.path.expanduser('~/Library/Application Support/KKBOX/Downloaded Music/')
	sqlitedb = os.path.expanduser("~/Library/Application Support/KKBOX/Playlists.db")
	plist_file = os.path.expanduser("~/Library/Application Support/KKBOX/Downloaded Music/cache.plist")
	system_serial = "Your System Serial"
	
	verbose = False
	output = "."
	
	for o, a in opts:
		if o == "-v":
			verbose = True
		elif o == "-s":
			system_serial = a
		elif o == "-p":
			plist_file = a
		elif o == "-o":
			output = a
		elif o == "-d":
			sqlitedb = a
		else:
			assert False, "unhandled option"
	
	"""
	checking requirement
	"""		
	if system_serial is None:
		print "you have to provide your 'System Serial'"
		sys.exit(2)
		
	if not (os.path.exists(sqlitedb) and os.path.isfile(sqlitedb)):
		print "sqlitedb not exists: ", sqlitedb
		sys.exit(2)
	
	if output is None or not (os.path.exists(output) and os.path.isdir(output)):
		print "output directory not exists: ", output
		sys.exit(2)
	
	con = sqlite3.connect(sqlitedb)
	cur = con.cursor()
	cur.execute("select song_id,song_name, artist_name, album_name, genre_name, in_album_order_index from song_tracks")
	
	plist = plistlib.readPlist(plist_file)
	cacheversion = plist['CacheVersion']	
	
	for songid, name, artist, album, genre, indx in cur.fetchall():	
	
		"""
		md5(system serial + cacheversion + songid) = hash_filename
		"""
		
		hash = hashlib.md5()
		hash.update("%s%s%s" % (system_serial, cacheversion, songid))
		digest = hash.hexdigest()
		
		song_src = downloaded_music_path + digest[0:2] + '/' + digest[2:4] + '/' + digest[4:]
		
		if os.path.exists(song_src):
			try:
				song_dst = output + '/' + name + '.mp3'
				
				mp3_tag = ID3v2(song_src)
				
				tags = ['TIT2', 'TALB', 'TPE1', 'TCON', 'TRCK']
				values = [name, album, artist, genre, indx]
				
				for tag, text in zip(tags, values):
					frame = mp3_tag.new_frame(tag)
					frame.set_text(text)
					mp3_tag.frames.append(frame)

				mp3_tag.commit_to_file(song_dst)
				
				print "music: %s -> %s" % (digest, song_dst)
				
			except Exception, message:
				print "music: %s maybe still encryted" % song_src
				print "message: %s" % message 
			
	con.close()
	
if __name__ == "__main__":
	main()

