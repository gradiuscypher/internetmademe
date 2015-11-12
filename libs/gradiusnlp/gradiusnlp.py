import nltk
import praw
import elasticsearch
import random
import string


class GradiusNlp:

    def __init__(self):
        print("Building GradiusNlp...")
        self.elastic = elasticsearch.Elasticsearch()

    def learn_from_reddit(self, subreddit, post_count):
        r = praw.Reddit(user_agent="https://github.com/gradiuscypher/internetmademe")
        sub = r.get_subreddit(subreddit)
        top = sub.get_top_from_day(limit=post_count)

        #process post_count top posts
        for post in top:

            #Check if the post has already been indexed
            index_name = 'index'
            if self.elastic.exists(index=index_name, id=post.id):
                print("This post already has been indexed.")

            else:
                #Add post id to indexed posts
                self.elastic.index(index=index_name, doc_type='post', id=post.id, body={"title": post.title})

                comments = post.comments

                #process top comments
                for c in comments:
                    if type(c) is praw.objects.Comment:
                        tokens = nltk.word_tokenize(c.body)
                        tagged_tokens = nltk.pos_tag(tokens)

                        sentence_structure = []
                        for tag in tagged_tokens:
                            sentence_structure.append(tag[1])
                            if not tag[1] in string.punctuation:
                                es_index = tag[1].lower()
                                q_txt = 'word: ' + '"' + tag[0].lower() + '"'

                                try:
                                    if self.elastic.indices.exists(es_index):
                                        if not (self.elastic.search(index=es_index, q=q_txt)['hits']['total'] > 0):
                                            self.elastic.index(index=es_index, doc_type='word', body={'word': tag[0].lower()})
                                    else:
                                        self.elastic.index(index=es_index, doc_type='word', body={'word': tag[0].lower()})

                                except:
                                    #TODO: Limit the exception scope and have a better action.
                                    print("The query failed to execute: " + q_txt)

                                es_index = "sentence_structure"
                                q_txt = 'word: ' + '"' + tag[0].lower() + '"'
                                try:
                                        self.elastic.index(index=es_index, doc_type='structure', body={'structure': sentence_structure})

                                except:
                                    #TODO: Limit the exception scope and have a better action.
                                    print("The query failed to execute: " + q_txt)


                        #process comment replies one tree down
                        for r in c.replies:
                            if type(r) is praw.objects.Comment:
                                tokens = nltk.word_tokenize(r.body)
                                tagged_tokens = nltk.pos_tag(tokens)

                                for tag in tagged_tokens:
                                    if not tag[1] in string.punctuation:
                                        es_index = tag[1].lower()
                                        q_txt = 'word: ' + '"' + tag[0].lower() + '"'

                                        try:
                                            if self.elastic.indices.exists(es_index):
                                                if not (self.elastic.search(index=es_index, q=q_txt)['hits']['total'] > 0):
                                                    self.elastic.index(index=es_index, doc_type='word', body={'word': tag[0].lower()})
                                            else:
                                                self.elastic.index(index=es_index, doc_type='word', body={'word': tag[0].lower()})

                                        except:
                                            #TODO: Limit the exception scope and have a better action.
                                            print("The query failed to execute: " + q_txt)

                                        es_index = "sentence_structure"
                                        q_txt = 'word: ' + '"' + tag[0].lower() + '"'
                                        try:
                                            self.elastic.index(index=es_index, doc_type='structure', body={'structure': sentence_structure})

                                        except:
                                            #TODO: Limit the exception scope and have a better action.
                                            print("The query failed to execute: " + q_txt)

    def fill_pos(self, pos_string):
        es_index = pos_string.lower()
        results = self.elastic.search(index=es_index, body={"query": {
            "function_score": {
                "query": {"wildcard": {"word": "*"}},
                "random_score": {}
            }}})

        return random.choice(results['hits']['hits'])['_source']['word']

    def build_sentence(self):
        result = ""
        es_index = "sentence_structure"
        results = self.elastic.search(index=es_index, body={"query": {
            "function_score": {
                "query": {"wildcard": {"structure": "*"}},
                "random_score": {}
            }}})

        random_struct = random.choice(results['hits']['hits'])['_source']['structure']

        for pos in random_struct:
            if pos in string.punctuation:
                result += pos + ' '
            else:
                result += self.fill_pos(pos) + ' '

        return result
