from flask import Flask, render_template, url_for, request, redirect
from datetime import datetime
from py2neo import Graph, authenticate # version 2.0.8
from time import time
from SyntacticSearch import SyntacticSearch


app = Flask(__name__)


# Enter neo4j database & server details here
username = "neo4j"
server_address = "<ip:port>"
# port is 7474 for http connections, 7687 for bolt connections
password = "neo4j"
db_uri = "http://<ip:port>/db/data/"

authenticate(server_address, username, password)
g = Graph(db_uri)

# load the Syntactic Search framework which generates required cypher queries
framework = SyntacticSearch(g)


# Start page of Flask app
@app.route('/', methods=['POST', 'GET'])
def index():	
	results = None
	t=0 
	cypher_query = None

	# if user has entered query
	if request.method == 'POST':
		query = request.form['content']
		print("Input query:", query)

		# generate cypher query with error checking and record time
		try:
			cypher_query = framework.get_cypher(query) 
			t1 = time()
			results = g.cypher.execute(cypher_query)
			t2 = time()
			t = t2 - t1
		except AssertionError as e:
			print("ERROR in -", cypher_query)
			return "Doesn't match template"
		except Exception as e:
			print("ERROR in -", cypher_query)
			return "Error in executing Cypher query"

	# display total nodes and relationships to user
	count_query = "MATCH (n) RETURN COUNT(*);"
	
	try:
		nodes = g.cypher.execute(count_query)
	except:
		return "Error in getting total nodes"
	count_query = "MATCH (n)-[r]->() RETURN COUNT(r)"
	try:
		rel = g.cypher.execute(count_query)
	except:
		return "Error in getting total relationships"

	# render the results page displaying required data
	return render_template("index.html", nodes=nodes.one, rel=rel.one, results=results, time="{:.6f}".format(t), cypher=cypher_query)



@app.route('/results/<string:s>')
def results(s):
	return render_template('results.html', result=s)


if __name__ == "__main__":
	app.run(debug=True)