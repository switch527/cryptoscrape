import links, source, db
import praw
import time
from textblob import TextBlob

INCLUDED_PATH_REDDIT = "sources/reddit/include.txt"
LAST_RUN_PATH_REDDIT = "sources/reddit/.lastrun"
CRYPTOS_PATH_REDDIT = "sources/reddit/cryptos.txt"

class Reddit(source.Source):
    subreddits = set()
    instance = praw.Reddit("crypto-scrape")
    srMentions = dict()

    def __init__(self):
        source.Source.__init__(self, INCLUDED_PATH_REDDIT, LAST_RUN_PATH_REDDIT, CRYPTOS_PATH_REDDIT)
        for sr in self.included:
            self.subreddits.add(self.instance.subreddit(sr))
            self.srMentions[sr] = {}
            for crypto in self.cryptos:
                self.srMentions[sr][crypto] = 0

    def collectMentions(self, lim=0):
        for sub in self.subreddits:
            for post in sub.new(limit = lim):
                postTime = int(post.created)

                if (postTime > self.lastRun):
                    # include all comments
                    post.comments.replace_more(limit = None)

                    for crypto in self.cryptos:
                        self.srMentions[sub.display_name][crypto] += post.url.lower().count(crypto)

                        if (post.selftext.lower().count(crypto) > 0):
                            self.srMentions[sub.display_name][crypto] += post.selftext.lower().count(crypto)
                            selfTextBlob = TextBlob(post.selftext.lower())
                            sentimentScore = selfTextBlob.sentiment.polarity
                            print(sentimentScore)
                            
                        for comment in post.comments.list():

                            if (comment.body.lower().count(crypto) > 0):
                                self.srMentions[sub.display_name][crypto] += comment.body.lower().count(crypto)
                                commentBlob = TextBlob(comment.body.lower())
                                commentScore = commentBlob.sentiment.polarity
                                print(commentScore)
        self.updateRun(time.time())

    def writeMentions(self):
	 for source, mentions in self.srMentions.iteritems():
            if isinstance(mentions, dict):
                for currency, number in mentions.iteritems():
                    db.execute_sql("cryptos.db", "lib/sql/insert_all_mentions.sql",
                    ["reddit", source, currency, number])
