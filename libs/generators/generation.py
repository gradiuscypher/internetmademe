from libs.gradiusnlp.gradiusnlp import GradiusNlp
from libs.markov.markov import Markov

# TODO: Pull all Reddit content locally so that we don't have to double pull.


class Generation:

    def __init__(self):
        print("Loading generation libraries...")
        self.nlp = GradiusNlp()
        self.markov = Markov()

    def collect_content(self, subreddit, post_count):
        self.markov.seed_from_reddit(subreddit=subreddit, post_count=post_count, chain_length=2)
        self.markov.seed_from_reddit(subreddit=subreddit, post_count=post_count, chain_length=3)
        self.nlp.learn_from_reddit(subreddit=subreddit, post_count=post_count)

