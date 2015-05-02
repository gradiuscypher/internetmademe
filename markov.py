import elasticsearch
import praw


class Markov:

    def __init__(self):
        self.elastic = elasticsearch.Elasticsearch()
        print()

    def seed_from_reddit(self, subreddit):
        """
        potential index approach -
        es.index(index='test', doc_type='2chain', body= {'key': 'this is', 'value': ['dog', 'cat', 'patrick']})

        potential choice approach -
        c = res['hits']['hits'][0]['_source']['value']
        random.choice(c)

        potential comment grabber
        r = praw.Reddit(user_agent = "Test project")
        sub = r.get_subreddit('leagueoflegends')
        top = sub.get_top_from_day()
        post = next(top)
        comms = post.comments
        comms[0].ups
        comms[0].replies
        """
        print()