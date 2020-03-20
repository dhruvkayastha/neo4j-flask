Install neo4j as a service on Linux:
	wget -O - https://debian.neo4j.org/neotechnology.gpg.key | sudo apt-key add -
	echo 'deb http://debian.neo4j.org/repo stable/' >/tmp/neo4j.list
	sudo mv /tmp/neo4j.list /etc/apt/sources.list.d
	sudo apt-get update
	sudo apt-get install neo4j=3.1.4

Start neo4j server:
	sudo service neo4j restart
	Once this is done, neo4j can be accessed at http://localhost:7474
	You will have to login using username "neo4j", password "neo4j" and a new password will be needed

Set up Flask app:
	pip3 install -r requirements.txt
	In app.py, update the password in the authenticate(username, password) function call

Run Flask app:
	python3 app.py


Details of Flask app:
	Displays total # of nodes, # of relationships in graph.
	User can enter cypher query to execute
	For information retrieval queries, the result will be shown as plain text and the query execution time will be displayed
	For CREATE statements, only the query execution time will be displayed 
