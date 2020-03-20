from flask import Flask, render_template, url_for, request, redirect
from datetime import datetime
from py2neo import Graph, authenticate
from time import time

app = Flask(__name__)
uri = "http://localhost:7474/db/data/"
authenticate("localhost:7474", "neo4j", "neo4j")

g = Graph(uri)


@app.route('/', methods=['POST', 'GET'])
# def index():
# 	if request.method == 'POST':
# 		cypher_query = request.form['content']
		
# 		try:
# 			result = g.cypher.execute(cypher_query)
# 			print(result)
# 			return redirect('/results')
# 		except:
# 			return "Error in adding new task"

# 	else:
# 		cypher_query = "MATCH (n) RETURN COUNT(*);"
# 		try:
# 			nodes = g.cypher.execute(cypher_query)
# 			# print(help(count))
# 		except:
# 			return "Error in getting total nodes"
# 		cypher_query = "MATCH (n)-[r]->() RETURN COUNT(r)"
# 		try:
# 			rel = g.cypher.execute(cypher_query)
# 		except:
# 			return "Error in getting total relationships"
# 		return render_template("index.html", nodes=nodes.one, rel=rel.one)


def index():	
	results = None
	t=0
	if request.method == 'POST':
		cypher_query = request.form['content']
		try:
			t1 = time()
			results = g.cypher.execute(cypher_query)
			t2 = time()
			t = t2 - t1
			print(results)
			# return redirect('/results')
			# return render_template("index.html", nodes=nodes.one, rel=rel.one, results=result)
		except:
			return "Error in executing Cypher query"

	cypher_query = "MATCH (n) RETURN COUNT(*);"
	try:
		nodes = g.cypher.execute(cypher_query)
		# print(help(count))
	except:
		return "Error in getting total nodes"
	cypher_query = "MATCH (n)-[r]->() RETURN COUNT(r)"
	try:
		rel = g.cypher.execute(cypher_query)
	except:
		return "Error in getting total relationships"

	print("RESULT is")
	print(results)
	return render_template("index.html", nodes=nodes.one, rel=rel.one, results=results, time=t)


@app.route('/results/<string:s>')
def results(s):
	return render_template('results.html', result=s)


if __name__ == "__main__":
	app.run(debug=True)