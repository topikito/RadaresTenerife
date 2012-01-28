# coding: utf-8

import datetime
import tweepy
import pprint
import ConfigParser
import smtplib
import sys
import shelve

#Print Status Array
def psa(status_array):
	for status in status_array:
		#pprint.pprint(dir(status))
		pprint.pprint(status.retweeted)
	print

#Configuration for the (ro)bot
config = ConfigParser.RawConfigParser()
config.read('/home/topi/twitter/settings.cfg')

#environment
args = sys.argv[1:]
if args:
	environment = sys.argv[1]
else:
	environment = 'dev';	
print 'Running in \'' + environment.upper() + ' MODE\''
	
#Last retweet	
db = shelve.open(config.get(environment, 'retweeted_history'))
last_retweet = db['last_retweet']

#Initialize API and RT flag	
rt = False
auth = tweepy.OAuthHandler(config.get(environment, 'consumer_key'), config.get(environment, 'consumer_secret'))
auth.set_access_token(config.get(environment, 'access_token'), config.get(environment, 'access_token_secret'))
api = tweepy.API(auth)
timeline = api.user_timeline(config.get(environment, 'feeder'))
timeline = reversed(timeline) #from older to newer

#Open log file and initialize timestamp
f = open(config.get(environment, 'log_file'), 'a')
now = datetime.datetime.now()

#Run over the timeline
for status in timeline:
	tweet_id = status.id
	tweet_text = status.text
	
	if config.get(environment, 'keyword').lower() in tweet_text.lower() and (tweet_id > last_retweet):
		rt = True
		if (environment == 'main'):
			#api.retweet(tweet_id)
			optional_via = ' (RT: ' + config.get(environment, 'optional_via') + ')'
			new_tweet = tweet_text + optional_via
			total_size = len(new_tweet)
			my_tweet = new_tweet
			if (total_size > int(config.get(environment, 'max_tweet_size'))):
				my_tweet = tweet_text
			db['last_retweet'] = tweet_id
			api.update_status(my_tweet)
			print 'Status Update: ' + my_tweet
		else:
			print config.get(environment, 'got_new_tweet') + ': ' + str(tweet_id)
		f.write('[' + str(now) +']['+ environment +'] ' + config.get(environment, 'retweeted_log') + ' ' + str(tweet_id) + '\n')
		print config.get(environment, 'retweeted_print') + ' ' + str(tweet_id)


if rt:
	print 'Retweets done'
else:
	f.write('[' + str(now) + ']['+ environment +'] ' + config.get(environment, 'nothing_done_log') + '\n')
	print config.get(environment, 'nothing_done_print')

f.close()
db.close()