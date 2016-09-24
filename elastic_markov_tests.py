import elasticsearch
import markovify
from pprint import pprint
import traceback

body = {
    "fields": "content",
    "size": 10000,
    "query": {
        "function_score": {
            "query": {
                "bool": {
                    "must": {
                        "term": {
                            "channel": "general"
                        }
                    }
                }
            },
            "random_score": {}
        }
    },

    "filter": {
        "script": {
            "script": "_source.content?.size() > 25"
        }
    }
}

twitch_body = {
    "fields": "body",
    "size": 10000,
    "query": {
        "function_score": {
            "random_score": {}
        }
    },

    "filter": {
        "script": {
            "script": "_source.content?.size() > 25"
        }
    }
}

es = elasticsearch.Elasticsearch()

result = es.search(index="discord_chat", body=body)
twitch_result = es.search(index="twitch_chat", body=twitch_body)
pprint("Query took: " + str(result['took']))

hits = result['hits']['hits']
twitch_hits = twitch_result['hits']['hits']

text_blob = ""
never_ended = 0

for h in hits:
    try:
        message = h['fields']['content'][0]
        message = message.strip()
        if not message.endswith((".", "?", "!")):
            never_ended += 1
            message += "."
        text_blob += message + "\n"
    except:
        print(traceback.format_exc())

for h in twitch_hits:
    try:
        message = h['fields']['body'][0]
        text_blob += message + "\n"
    except:
        print(traceback.format_exc())

print("Building Markov Start.")
text_model = markovify.NewlineText(text_blob)
print("Building Markov Complete.")
print("Never ended: ", never_ended)

print()

for x in range(0,10):
    # print(target, text_model.make_sentence(("is", "a")))
    print(text_model.make_sentence())
