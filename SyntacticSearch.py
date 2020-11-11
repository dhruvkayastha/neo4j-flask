import re
from py2neo import Graph, authenticate # version 2.0.8
from time import time
import numpy as np

# Enter Neo4j database server details here
username = "neo4j"
password = "neo4j"
uri = ""
# example: http://localhost:7474 or https://<ip>:<port>
db_uri = ""


class SyntacticSearch:

	# load graph (not required for current work flow) into framework
		# graph will be needed to be loaded if framework fetches and returns the results instead of returning the query 
	def __init__(self, graph):
		self.g = graph

		# load regular expression query templates
		self.templates = []
		self.templates.append('How many (.*) calls are there?'.lower())
		self.templates.append('how many references are there for symbol (.*)?'.lower())
		self.templates.append('Where is (the )?variable ([a-zA-Z0-9_]*) defined'.lower())
		self.templates.append('Where is (the )?variable ([a-zA-Z0-9_]*) used'.lower())
		self.templates.append('What is (the )?read write sequence of (the )?variable ([a-zA-Z0-9_]*)'.lower())
		self.templates.append('which threads update (the )?variable ([a-zA-Z0-9_]*)'.lower())
		self.templates.append('function call graph for (function )?([a-zA-Z0-9_]*)'.lower())
		self.templates.append('how are class (.*) and class (.*) related'.lower())
		self.templates.append('name, type definition of (the )?variables associated with (the )?concept (.*)'.lower())
		self.templates.append('read write sequence of (the )?variable (.*)'.lower())
		self.templates.append('List (the )?threads accessing (the )?variable (.*)'.lower())
		self.templates.append('read write sequence of (the )?variable ([a-zA-Z0-9_]*) in (the )?file (.*)'.lower())
		self.templates.append('which variables of file (.*) maps to concept (.*)'.lower())
		self.templates.append('list (all )?(the )?([a-zA-Z]*) variables and (the )?file(s)? where (they are |it is )?defined'.lower())
		self.templates.append('Where in (the )?file is (the )?variable ([a-zA-Z0-9_]*) used'.lower())
		self.templates.append('What are (the )?comments associated (to |with )? variable ([a-zA-Z0-9_]*)'.lower())
		self.templates.append('member variable (.*) of class (.*) is accessed using which mutex'.lower())
		self.templates.append('How many unsynchronised accesses are there in (the )?file ([a-zA-Z0-9_]*)'.lower())
		# self.templates.append('Which variables are (read|written) before and after the (read|write) of variable (.*)'.lower())
		self.templates.append('List all ([a-zA-Z.]*) (files)?'.lower())
		self.templates.append('List all ([a-zA-Z.]*) and ([a-zA-Z.]*) (files)?'.lower())
		self.templates.append('variables accessed (by |using )?(.*) thread(s)?'.lower())
		self.templates.append('(total number of |How many )threads in execution ([0-9]*) of (.*)'.lower())
		self.templates.append('(what|which) functions have return type ([a-zA-Z0-9_]*)'.lower())
		self.templates.append('Does function (.*) invoke any function which has return type (.*)'.lower())
		self.templates.append('Concept (.*) involves which (.*) variables'.lower())
		self.templates.append('which member variables of class (.*) are involved in sorting algo'.lower())
		self.templates.append('Where in (the )?project is variable ([a-zA-Z0-9_]*) used'.lower())
		self.templates.append('Which functions are called after the invocation of function (.*)'.lower())
		self.templates.append('list (all )?(the )?variables accessed using (the )?mutex ([a-zA-Z0-9_]*)'.lower())
		self.templates.append('Does (the )?function (.*) (invoke|call) any function(s)? (which has|having) parameter of type (.*)'.lower())
		self.templates.append('What are the (.*) members of class (.*)'.lower())
		self.templates.append('Concept (.*) involves which classes'.lower())
		self.templates.append('what (all )?is referred (to in|by) (the )?comment (.*)'.lower())


	# input: natural language query
	# output: generated cypher query or NA
	def get_cypher(self, query):
		cypher = "NA"
		query = query.lower()
		templates = self.templates
		for temp in templates:
			m = re.match(temp, query)
			if m:
				if temp == 'How many (.*) calls are there?'.lower():
					cypher = "match p = (a:function)<-[:CALLS]-(b:function) WHERE a.name=~'.*{}.*' or a.linkage_name=~'.*{}.*' RETURN COUNT(p)".format(m.group(1), m.group(1))
				
				elif temp == 'how many references are there for symbol (.*)?'.lower():
					cypher = "match p = (a {{name: '{}'}})-[:referenceTo]-() return count(p)".format(m.group(1))
				
				elif temp == 'Where is (the )?variable ([a-zA-Z0-9_]*) defined'.lower():
					cypher = "match (a {{name: '{}', isDef: 'True'}}) WHERE exists(a.line) return distinct a.file, a.line".format(m.group(2))
				
				elif temp == 'Where is (the )?variable ([a-zA-Z0-9_]*) used'.lower() or temp == 'Where in (the )?project is variable ([a-zA-Z0-9_]*) used'.lower():
					cypher = "match (a {{name: '{}'}}) WHERE exists(a.line) return distinct a.file, a.line".format(m.group(2))
				
				elif temp == 'What is (the )?read write sequence of (the )?variable ([a-zA-Z0-9_]*)'.lower():
					cypher = "MATCH p = (a)-[r:NONLOCALWRITE|POINTERWRITE|NONLOCALREAD|LOCALACCESS]-() WHERE a.name=~'(?i){}' and exists(r.TS) RETURN r ORDER BY toInt(split(r.TS, '_')[2])".format(m.group(3))
				
				elif temp == 'which threads update (the )?variable ([a-zA-Z0-9_]*)'.lower():
					cypher = "MATCH p = (a)-[r:NONLOCALWRITE|POINTERWRITE]-() WHERE a.name='{}' RETURN distinct(r.THREADID)".format(m.group(2))
				
				elif temp == 'function call graph for (the file )?([a-zA-Z0-9_]*)'.lower(): #file
					cypher = "match (a:function)-[r:CALLS]-(b:function), (a)-[:trace]-(c) WHERE c.EXE=~'(?i).*{}.*' RETURN a, r, b".format(m.group(2))
				
				elif temp == 'how are class (.*) and class (.*) related'.lower():
					cypher = "MATCH p=(o:class {{name:'{}'}})-[r*1..3]-(x:class {{name:'{}'}}) RETURN p".format(m.group(1), m.group(2))
				
				elif temp == 'name, type definition of (the )?variables associated with (the )?concept (.*)'.lower():
					cypher = "match (com:comment)-[:symbol]-(sym), (com)-[:domain]-(concept) WHERE concept.type=~'(?i).*{}.*' return sym".format(m.group(3))
				
				elif temp == 'read write sequence of (the )?variable (.*)'.lower():
					cypher = "MATCH p = (a)-[r:NONLOCALWRITE|POINTERWRITE|NONLOCALREAD|LOCALACCESS]-() WHERE a.name='{}' and exists(r.TS) RETURN distinct type(r), r.FUNCNAME, r.THREADID, r.TS ORDER BY toInt(split(r.TS, '_')[2])".format(m.group(1))
				
				elif temp == 'List (the )?threads accessing (the )?variable (.*)'.lower():
					cypher = "MATCH p = (a)-[r:NONLOCALWRITE|POINTERWRITE|NONLOCALREAD|LOCALACCESS]-() WHERE a.name='{}' RETURN distinct(r.THREADID)".format(m.group(3))
				
				elif temp == 'read write sequence of (the )?variable ([a-zA-Z0-9_]*) in (the )?file (.*)'.lower():
					cypher = "MATCH p = (a)-[r:NONLOCALWRITE|POINTERWRITE|NONLOCALREAD|LOCALACCESS]-() WHERE a.name='{}' and a.file=~'.*{}.*' exists(r.TS) RETURN r ORDER BY toInt(split(r.TS, '_')[2])".format(m.group(3), m.group(2))
				
				elif temp == 'which variables of file (.*) maps to concept (.*)'.lower():
					cypher = "match (com:comment)-[:symbol]-(sym), (com)-[:domain]-(concept) WHERE concept.type=~'(?i).*{}.*' and sym.file=~'.*{}.*' return sym".format(m.group(2), m.group(1))
				
				elif temp == 'list (all )?(the )?([a-zA-Z]*) variables and (the )?file(s)? where (they are |it is )?defined'.lower():
					cypher = "match (a) where a.storage_class=~'.*{}.*' return a.name, a.file, a.line".format(m.group(3))
				
				elif temp == 'Where in (the )?file is (the )?variable ([a-zA-Z0-9_]*) used'.lower():
					cypher = "match (a {{name: '{}'}}) WHERE exists(a.line) return a.file, a.line".format(m.group(3))
				
				elif temp == 'member variable (.*) of class (.*) is accessed using which mutex'.lower():
					# cypher = "match (a)-[:LEX_PARENT|SEM_PARENT]-(b), (a)-[r:NONLOCALWRITE|POINTERWRITE|NONLOCALREAD|LOCALACCESS]-(c:function) where a.name='{}' and b.name='{}' and  c.name=~'.*mutex.*' return a".format(m.group(1), m.group(2))
					cypher = "match p = (a)<-[:LOCKS]-(b), (a)-[:SEM_PARENT|LEX_PARENT]-(c) where a.name='{}' and c.name='{}' return b".format(m.group(1), m.group(2))
				
				elif temp == 'How many unsynchronised accesses are there in (the )?file ([a-zA-Z0-9_]*)'.lower():
					cypher = "match p = (b)-[r:NONLOCALWRITE|POINTERWRITE|NONLOCALREAD|LOCALACCESS]->(a) where a.file=~'.*{}.*' and r.SYNCS='ASYNC' return count(p)".format(m.group(2))
				
				elif temp == 'List all ([a-zA-Z.]*) and ([a-zA-Z.]*) (files)?'.lower():
					if 'header' in m.group(1):
						file_type1 = 'h'
					else:
						file_type1 = m.group(1)
					if 'header' in m.group(2):
						file_type2 = 'h'
					else:
						file_type2 = m.group(2)
					if 'cpp' in file_type2 or 'cpp' in file_type1:
						cypher = "match (a) where a.file=~'.*{}' or a.file=~'.*{}' or a.file=~'.*cc' return distinct(a.file)".format(file_type2, file_type1)
					elif 'cc' in file_type2 or 'cc' in file_type1:
						cypher = "match (a) where a.file=~'.*{}' or a.file=~'.*{}' or a.file=~'.*cpp' return distinct(a.file)".format(file_type2, file_type1)
					else:
						cypher = "match (a) where a.file=~'.*{}' or a.file=~'.*{}' return distinct(a.file)".format(file_type2, file_type1)
				
				elif temp == 'List all ([a-zA-Z.]*) (files)?'.lower():
					if 'header' in m.group(1):
						file_type = 'h'
					else:
						file_type = m.group(1)
					cypher = "match (a) where a.file=~'.*{}' return distinct(a.file)".format(file_type)
				
				elif temp == 'variables accessed (by |using )(.*) thread(s)?'.lower():
					cypher = "MATCH p = (a)-[r:NONLOCALWRITE|POINTERWRITE|NONLOCALREAD|LOCALACCESS]-() WHERE r.THREADID{}'0' RETURN distinct(a)".format('=' if m.group(2) == 'main' else '!=')
				
				elif temp == '(total number of |How many )threads in execution ([0-9]*) of (.*)'.lower():
					cypher = "profile match (d:dynamictrace)<-[:trace]-(c), (c)-[r]-() where d.RUNID=~'{}' and d.EXE=~'.*{}' and exists(r.THREADID) return count(distinct(r.THREADID))".format(m.group(2), m.group(3))
				
				elif temp == '(what|which) functions have return type ([a-zA-Z0-9_]*)'.lower():
					cypher = "match (a:function) where a.return_type='{}' and a.isDef='True' return distinct a.name, a".format(m.group(2))
				
				elif temp == 'Does (the )?function (.*) (invoke|call) any function(s)? (which has|having) parameter of type (.*)'.lower():
					cypher = "match (a:function)-[:CALLS]-(b:function) where a.name='{}' or a.linkage_name=~'.*{}.*' and b.return_type='{}' return b.linkage_name, b".format(m.group(2), m.group(2), m.group(6))
				
				elif temp == 'Concept (.*) involves which (.*) variables'.lower():	# extern
					cypher = "match (com:comment)-[:symbol]-(sym), (com)-[:domain]-(concept) WHERE concept.type=~'(?i).*{}.*' and sym.storage_class='{}' return sym".format(m.group(1), m.group(2))
				
				elif temp == "which member variables of class (.*) is involved in (.*)".lower(): # concept
					cypher = "match (com:comment)-[:symbol]-(sym), (com)-[:domain]-(concept), (sym)-[:LEX_PARENT|SEM_PARENT]-(a:class)"
					cypher +=" WHERE a.name='{}' concept.type=~'(?i).*{}}.*' return sym".format(m.group(1), m.group(2))
				
				elif temp == 'Which functions are called after the invocation of function (.*)'.lower():
					cypher = "match (caller:function)-[r:CALLS]->(myfunc:function) where myfunc.name='{}' with min(toInt(split(r.TS, '_')[2])) AS temp match (a:function)-[rr:CALLS]->(b:function) where toInt(split(rr.TS, '_')[2]) > temp return distinct(b.name)".format(m.group(1))
				
				elif temp == 'list (all )?(the )?variables accessed using (the )?mutex ([a-zA-Z0-9_]*)'.lower():
					cypher = "match p = (a)<-[:LOCKS]-(b) where b.name='{}' return distinct a.name, a.file".format(m.group(4))
				
				elif temp == 'Does function (.*) invoke any function which has parameter of type (.*)?'.lower():
					cypher = "match (a:function)-[:CALLS]->(b:function), (p:parm)-[:LEX_PARENT|SEM_PARENT]-(b) where a.name='{}' and p.type='{}' return distinct b.linkage_name".format(m.group(1), m.group(2))
				
				elif temp == 'What are the (.*) members of class (.*)'.lower():
					cypher = "match (a:class)-[:LEX_PARENT|SEM_PARENT]-(b) where b.access_specifier=~'(?i){}' and a.name='(?i){}' return b".format(m.group(1), m.group(2))
				
				elif temp == 'Concept (.*) involves which classes'.lower():
					cypher = "match (com:comment)-[:symbol]-(sym), (com)-[:domain]-(concept), (sym)-[:LEX_PARENT|SEM_PARENT]-(a:class) WHERE concept.type=~'(?i).*{}.*' or labels(sym)='class' return a".format(m.group(1))
				
				elif temp == 'what (all )?is referred (to in|by) (the )?comment (.*)'.lower():
					cypher = "match (com:comment)-[:symbol]-(sym) where com.comment_text=~'(?i).*{}.*' return sym.name, labels(sym), com.comment_text".format(m.group(4))

		return cypher


