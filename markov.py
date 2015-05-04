import elasticsearch
import praw
import random


#TODO: Tons of debug printing that needs to be cleaned up

class Markov:

    def __init__(self):
        self.elastic = elasticsearch.Elasticsearch()
        random.seed()

    def build_chain(self, message, chain_length):
        pointer = 0
        split_message = message.split()

        while pointer+chain_length < len(split_message):
            self.elastic.index(index=chain_length, doc_type='markov_chain',
                               body={'key': ' '.join(split_message[pointer:pointer+chain_length]),
                                     'value': split_message[pointer+chain_length]})
            pointer += 1

    def clean_punctuation(self, sentence):
        #TODO: Implement this more "smartly"
        sentence = sentence.replace('"', '')
        sentence = sentence.replace('.', '')
        return sentence

    def generate_sentence(self, chain_type, seed, min_length, max_length):
        #TODO: Current search / random methods are SUPER slow. There needs to be a better way.
        sentence = ""
        start = self.elastic.search(index=chain_type, q=seed)
        max_search = start['hits']['total']
        start = self.elastic.search(index=chain_type, q=seed, size=max_search)
        start_key = random.choice(start['hits']['hits'])['_source']['key']
        sentence += start_key
        sentence = self.clean_punctuation(sentence)

        for x in range(0, random.randint(min_length, max_length)):
            target = ' '.join(sentence.split()[-chain_type:])
            print("Search target: ", target)
            search = self.elastic.search(index=chain_type, q='key:"' + target + '"', size=max_search)
            result_list = search['hits']['hits']

            if len(result_list) > 0:
                results = random.choice(result_list)['_source']['value']
                sentence += " " + results
                sentence = self.clean_punctuation(sentence)

        while not self.validate_ending(sentence):
            target = ' '.join(sentence.split()[-chain_type:])
            print("Search target: ", target)
            search = self.elastic.search(index=chain_type, q='key:"' + target + '"', size=max_search)
            result_list = search['hits']['hits']

            if len(result_list) > 0:
                results = random.choice(result_list)['_source']['value']
                sentence += " " + results
                sentence = self.clean_punctuation(sentence)

        return sentence

    def seed_from_reddit(self, subreddit, post_count, chain_length):
        r = praw.Reddit(user_agent="https://github.com/gradiuscypher/internetmademe")
        sub = r.get_subreddit(subreddit)
        top = sub.get_top_from_day(limit=post_count)

        #process post_count top posts
        for post in top:
            print("Post processing started...")
            comments = post.comments
            #process top comment
            for c in comments:
                print("    Comment processing started...")
                if type(c) is praw.objects.Comment:
                    self.build_chain(c.body, chain_length)
                    #process comment replies one tree down
                    for r in c.replies:
                        print("        Reply processing started...")
                        if type(r) is praw.objects.Comment:
                            self.build_chain(r.body, chain_length)
                        print("        Reply processing completed.")
                print("    Comment processing completed.")

            print("Post processing completed.")

    def validate_ending(self, sentence):
        ## Meant to ensure that the result doesn't end in things like the, is, etc.
        invalid_endings = ['a', 'is', 'the', 'and']
        split_sentence = sentence.split()

        if split_sentence[-1] in invalid_endings:
            print("BAD ENDING.")
            return False
        else:
            return True
