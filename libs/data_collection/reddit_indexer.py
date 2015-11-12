import praw
import elasticsearch
# TODO: This class should be used for indexing and exposing Reddit data to avoid duplicating requests


class RedditIndexer:

    def __init__(self):
        print("Building the RedditIndexer...")
        self.elastic = elasticsearch.Elasticsearch()

    def index_subreddit(self, subreddit, post_count):
        r = praw.Reddit(user_agent="https://github.com/gradiuscypher/internetmademe")
        sub = r.get_subreddit(subreddit)
        top = sub.get_top_from_day(limit=post_count)

        # process post_count top posts
        for post in top:
            # Check if the post has already been indexed
            index_name = 'indexed_posts'
            if self.elastic.exists(index=index_name, id=post.id):
                print("This post already has been indexed.")

            else:
                # Add post id to indexed posts
                self.elastic.index(index=index_name, doc_type='post', id=post.id, body={"title": post.title})

                comments = post.comments

                for c in comments:

                    # TODO: Climb farther down the comment tree
                    if type(c) is praw.objects.Comment:
                        try:
                            self.elastic.index(index=subreddit, doc_type='comment',
                                               body={'source': 'reddit', 'body': c.body, 'ups': c.ups})

                        except:
                            # TODO: Make this exception a lot less broad and more useful
                            print("There was a problem while indexing a comment.")
