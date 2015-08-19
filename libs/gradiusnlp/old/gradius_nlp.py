import praw
import elasticsearch
import string
import random
from nltk import word_tokenize, pos_tag


class GradiusNlp:

    def __init__(self):
        self.elastic = elasticsearch.Elasticsearch()

    def get_reddit_data(self, subreddit, post_count):
        r = praw.Reddit(user_agent="https://github.com/gradiuscypher/internetmademe")
        sub = r.get_subreddit(subreddit)
        top = sub.get_top_from_day(limit=post_count)

        #process post_count top posts
        for post in top:
            comments = post.comments

            #process top comment
            for c in comments:
                if type(c) is praw.objects.Comment:
                    tokens = word_tokenize(c.body)
                    tagged_tokens = pos_tag(tokens)

                    for tag in tagged_tokens:
                        print(tag)
                        if not tag[1] in string.punctuation:
                            es_index = tag[1].lower()
                            q_txt = 'word: ' + '"' + tag[0].lower() + '"'
                            if self.elastic.indices.exists(es_index):
                                if not (self.elastic.search(index=es_index, q=q_txt)['hits']['total'] > 0):
                                    self.elastic.index(index=es_index, doc_type='word', body={'word': tag[0].lower()})
                            else:
                                self.elastic.index(index=es_index, doc_type='word', body={'word': tag[0].lower()})

                    #process comment replies one tree down
                    for r in c.replies:
                        if type(r) is praw.objects.Comment:
                            tokens = word_tokenize(r.body)
                            tagged_tokens = pos_tag(tokens)

                            for tag in tagged_tokens:
                                print(tag)
                                if not tag[1] in string.punctuation:
                                    es_index = tag[1].lower()
                                    q_txt = 'word: ' + '"' + tag[0].lower() + '"'

                                    if self.elastic.indices.exists(es_index):
                                        if not (self.elastic.search(index=es_index, q=q_txt)['hits']['total'] > 0):
                                            self.elastic.index(index=es_index, doc_type='word', body={'word': tag[0].lower()})
                                    else:
                                        self.elastic.index(index=es_index, doc_type='word', body={'word': tag[0].lower()})

    def reform_sentence(self, sentence, force_replace_count=1):
        sentence_tokens = word_tokenize(sentence)

        replace_count = random.randint(force_replace_count, len(sentence_tokens))
        print(replace_count)

        #Ensure at least force_replace_count words are being replaced
        for x in range(0, replace_count):
            tagged_tokens = pos_tag(sentence_tokens)
            choice = random.choice(tagged_tokens)

            while choice[0] in string.punctuation:
                choice = random.choice(tagged_tokens)

            new_word = self.replace_pos(choice)
            sentence_tokens[sentence_tokens.index(choice[0])] = new_word

        return ' '.join(sentence_tokens)

    def replace_pos(self, pos_tuple):
        es_index = pos_tuple[1].lower()
        results = self.elastic.search(index=es_index, body={"query": {
            "function_score": {
                "query": {"wildcard": {"word": "*"}},
                "random_score": {}
            }}})

        return random.choice(results['hits']['hits'])['_source']['word']
