import elasticsearch
import praw
import random


#TODO: Tons of debug printing that needs to be cleaned up
#TODO: not sure if case sensitivity is something I should address

class Markov:

    def __init__(self):
        self.elastic = elasticsearch.Elasticsearch()

        #Max number of times ending validation will be attempted.
        self.max_validation_attempt = 10

        random.seed()

    def build_chain(self, message, chain_length, doc_type):
        pointer = 0
        split_message = message.split()

        while pointer+chain_length < len(split_message):
            self.elastic.index(index=chain_length, doc_type=doc_type,
                               body={'key': ' '.join(split_message[pointer:pointer+chain_length]),
                                     'value': split_message[pointer+chain_length]})
            pointer += 1

    def clean_punctuation(self, sentence):
        #TODO: Implement this more "smartly"
        #TODO: Need something to remove URLs
        sentence = sentence.replace('"', '')
        sentence = sentence.replace('.', '')
        sentence = sentence.replace(')', '')
        sentence = sentence.replace('(', '')
        sentence = sentence.replace(',', '')
        return sentence

    def generate_bad_ending_index(self, ending_file):
        endings = open(ending_file, 'r')

        for line in endings:
            clean_line = line.strip('\n')
            self.elastic.index(index='stopwords', doc_type='stopword', body={'word': clean_line})

        endings.close()

    def generate_sentence(self, chain_type, seed, min_length, max_length):
        #TODO: Add functionality to select specific doc_types
        sentence = ""
        start = self.elastic.search(index=chain_type, body={"query": {
            "function_score": {
                "query": {"wildcard": {"key": seed}},
                "random_score": {}
            }}})
        start_key = random.choice(start['hits']['hits'])['_source']['key']
        sentence += start_key
        sentence = self.clean_punctuation(sentence)

        for x in range(0, random.randint(min_length, max_length)):
            target = ' '.join(sentence.split()[-chain_type:])
            # print("Search target: ", target)
            search = self.elastic.search(index=chain_type, q='key:"' + target + '"')
            result_list = search['hits']['hits']

            if len(result_list) > 0:
                results = random.choice(result_list)['_source']['value']
                sentence += " " + results
                sentence = self.clean_punctuation(sentence)

        validated = self.validate_ending(sentence)
        attempt_count = 0

        while not validated and attempt_count <= self.max_validation_attempt:
            target = ' '.join(sentence.split()[-chain_type:])
            # print("Search target: ", target)
            search = self.elastic.search(index=chain_type, q='key:"' + target + '"')
            result_list = search['hits']['hits']

            if len(result_list) > 0:
                results = random.choice(result_list)['_source']['value']
                sentence += " " + results
                sentence = self.clean_punctuation(sentence)

            validated = self.validate_ending(sentence)
            attempt_count += 1

        if validated:
            #normalize case
            sentence = sentence.lower()

            return sentence

        else:
            #TODO: NOT SURE IF THIS IS A GOOD IDEA, MIGHT LEAD TO INF RECURSION IN RARE CASES.
            #TODO: WILL LEAD TO RECURSION IF MALICIOUS SEED IS PROVIDED.
            return self.generate_sentence(chain_type, seed, min_length, max_length)

    def seed_from_reddit(self, subreddit, post_count, chain_length):
        #TODO: The indexing doesn't differentiate between different chain sizes, fix this.
        r = praw.Reddit(user_agent="https://github.com/gradiuscypher/internetmademe")
        sub = r.get_subreddit(subreddit)
        top = sub.get_top_from_day(limit=post_count)

        #process post_count top posts
        for post in top:

            #Check if the post has already been indexed
            if self.elastic.exists(index='indexed_posts', id=post.id):
                print("This post already has been indexed.")

            else:
                #Add post id to indexed posts
                self.elastic.index(index='indexed_posts', doc_type='post', id=post.id, body={"title": post.title})

                print("Post processing started...")
                comments = post.comments
                #process top comment
                for c in comments:
                    print("    Comment processing started...")
                    if type(c) is praw.objects.Comment:
                        self.build_chain(c.body, chain_length, subreddit)
                        #process comment replies one tree down
                        for r in c.replies:
                            print("        Reply processing started...")
                            if type(r) is praw.objects.Comment:
                                self.build_chain(r.body, chain_length, subreddit)
                            print("        Reply processing completed.")
                    print("    Comment processing completed.")

                print("Post processing completed.")

    def validate_ending(self, sentence):
        # Meant to ensure that the result doesn't end in things like the, is, etc.
        split_sentence = sentence.split()
        last_word = split_sentence[-1]

        count = self.elastic.search(index='stopwords', q='word:"' + last_word + '"')['hits']['total']

        if count is not 0:
            # print("Bad ending!")
            return False

        else:
            return True
