# Поиск жанра по названию
#  curl -XGET http://127.0.0.1:9200/genres/_search -H 'Content-Type: application/json' -d'
# {
#     "query": {
#         "bool": {
#             "must": [
#                 {"match": {"name": "Action"}}
#             ]
#         }
#     }
# }'

# Поиск жанра по идентификатору
# curl -XGET http://127.0.0.1:9200/genres/_search -H 'Content-Type: application/json' -d'
# {
#     "query": {
#         "bool": {
#             "must": [
#                 {"match": {"id": "5373d043-3f41-4ea8-9947-4b746c601bbd"}}
#             ]
#         }
#     }
# }'

# Поиск по полю writers_names
#  curl -XGET http://127.0.0.1:9200/movies/_search -H 'Content-Type: application/json' -d'
# {
#     "query": {
#         "bool": {
#             "must": [
#                 {"match": {"writers_names": "George Lucas"}}
#             ]
#         }
#     }
# }'

# Вложенный поиск
# curl -XGET http://127.0.0.1:9200/movies/_search -H 'Content-Type: application/json' -d'
# {
#   "query": {
#     "nested": {
#       "path": "writers",
#       "query": {
#         "bool": {
#           "must": [
#             { "match": { "writers.id": "a5a8f573-3cee-4ccc-8a2b-91cb9f55250a" } }
#           ]
#         }
#       }
#     }
#   }
# }'