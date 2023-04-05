import json
import urllib.request
from opensearchpy import OpenSearch
# Create the client with SSL/TLS and hostname verification disabled.
# TODO add your own user and password
opensearch = OpenSearch(
    hosts = [{'host': 'localhost', 'port': 9200}],
    http_compress = True, # enables gzip compression for request bodies
    use_ssl = True,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
    http_auth = (OPENSEARCH_USER,OPENSEARCH_PASSWORD)
)

index_name = 'co2-index'

index_body = {
  'settings': {
    'index': {
      'number_of_shards': 4
    }
  }
}

# Create index if missing
if not opensearch.indices.exists(index_name):
    print(opensearch.indices.create(index_name, body=index_body))

# Get date of most recent dataset from Opensearch
query = {"size": 1, "sort": [
  {
    "time": {
      "order": "desc"
    }
  }
]}
result = opensearch.search(
    body = query,
    index = index_name)
if len(result['hits']['hits']) > 0:
    max_time = result['hits']['hits'][0]['_source']['time']
else:
    max_time = '*'
time_filter = 'time:[{} TO *]'.format(max_time)
# Get all recent documents from Solr and add to Opensearch, i.e. documents with
# a more recent time than the most recent one in Opensearch
solr_url = 'http://10.0.3.214:8983/solr/co2/select'
auth_handler = urllib.request.HTTPBasicAuthHandler()
# TODO add your own user and password
auth_handler.add_password(realm='solr',
                          uri=solr_url,
                          user=SOLR_USER,
                          passwd=SOLR_PASSWORD)
opener = urllib.request.build_opener(auth_handler)
# ...and install it globally so it can be used with urlopen.
urllib.request.install_opener(opener)
# Create request for querying Solr
req = urllib.request.Request(solr_url)
req.add_header('Content-Type', 'application/json; charset=utf-8')
jsondata = json.dumps({"query":"*:*", "filter": time_filter, "sort": "time ASC", "fields":["id","co2","temperature","time"]})
jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
req.add_header('Content-Length', len(jsondataasbytes))
response = urllib.request.urlopen(req, jsondataasbytes)
if response.status == 200:
    # Get the documents and send them to Opensearch
    docs = json.loads(response.read())['response']['docs']
    for doc in docs:
        print(doc)
        try:
            id = doc.pop('id')
            print(opensearch.create(index_name,id,doc))
        except:
            print("Document already exists")
else:
    print("Error querying solr " + response.message)
