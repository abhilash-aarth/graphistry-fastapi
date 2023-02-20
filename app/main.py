import json
import logging
import os
from urllib.parse import parse_qs, urlsplit
from typing import Optional
import graphistry
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase  # for data loader
from neo4j.exceptions import ServiceUnavailable
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()
uri=os.getenv("uri")
user=os.getenv("user")
pwd=os.getenv("pwd")
personal_key_id=os.getenv("personal_key_id")
personal_key_secret=os.getenv("personal_key_secret")
postgres_db=os.getenv("database_uri")

graphistry.register(api=3,personal_key_id=personal_key_id, personal_key_secret=personal_key_secret, protocol='https', server='hub.graphistry.com')
NEO4J={'uri':uri, 'auth':(user, pwd)}
graphistry.register(bolt=NEO4J)


def connection():
  driver=GraphDatabase.driver(uri=uri,auth=(user,pwd))
  return (driver)

app = FastAPI()  
driver_neo4j=connection()
engine = create_engine(postgres_db)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.middleware("http")
async def db_session_middleware(request, call_next):
    response = JSONResponse(content={"message": "Internal Server Error"}, status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response

@app.get("/") 
async def main_route():     
  return {"message": "Hey, Graphistry!!"}

@app.get("/getDropdownValues") 
async def get_table_data():
    with engine.connect() as con:
            rs = con.execute("SELECT * FROM ltd_node_selection_lov order by id")
            results = [dict(row) for row in rs]
    return {"data": results}

driver = GraphDatabase.driver(uri, auth=(user,pwd))

async def execute_query_builder(node1: str, node2: Optional[str] = None, node3: Optional[str] = None) -> dict:
    with engine.connect() as con:
        query = text("SELECT ld_match_query, ld_match_node1, ld_match_node2, ld_match_node3, ld_return_node1, ld_return_node2, ld_return_node3, ld_return_edge1, ld_return_edge2, ld_limit,ld_edge_point_icon FROM ld_query_builder WHERE ld_node1 = :node1  AND (ld_node2 = :node2 OR :node2 IS NULL) AND (ld_node3 = :node3 OR :node3 IS NULL)")
        rs = con.execute(query, {"node1": node1, "node2": node2, "node3": node3})
        query_builder_data = [dict(row) for row in rs]
    if not query_builder_data:
        print(f"No records found for nodes: node1={node1}, node2={node2}, node3={node3}")
        return {}
    return query_builder_data


@app.get("/buildQuery")
async def queryGraphistry(node1: str, keyword1: Optional[str] = None, node2: Optional[str] = None, keyword2: Optional[str] = None, node3: Optional[str] = None, keyword3: Optional[str] = None, userId: Optional[str] = None):
    try:
        if node2 and node3:
            print("Found 3 nodes")
            
            # get the query builder data for node1
            query_builder_data_node = await execute_query_builder(node1,node2,node3)
            if not query_builder_data_node:
                print(f"No query builder data found for nodes: node1={node1}, node2={node2}, node3={node3}")
                return {}
            cypher_query = f"{query_builder_data_node[0]['ld_match_query']} "
            if keyword1 is not None:
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node1']}  '{keyword1}'  "
            if keyword2 is not None:
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node2']}  '{keyword2}'  "
            if keyword3 is not None:
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node3']}  '{keyword3}'  "
            cypher_query_node1 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node1']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_node2 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node2']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_node3 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node3']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges1 = cypher_query + f"RETURN {query_builder_data_node[0]['ld_return_edge1']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges2 = cypher_query + f"RETURN {query_builder_data_node[0]['ld_return_edge2']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges = cypher_query_edges1 + f" union " + cypher_query_edges2
            # print(cypher_query_node1)
            # print(cypher_query_node2)
            # print(cypher_query_node3)
            print(cypher_query_edges)
            with driver.session() as session:
                result = session.run(cypher_query_node1)
                node1 = pd.DataFrame([r.data() for r in result])
            with driver.session() as session:
                result = session.run(cypher_query_node2)
                node2 = pd.DataFrame([r.data() for r in result])
            with driver.session() as session:
                result = session.run(cypher_query_node3)
                node3 = pd.DataFrame([r.data() for r in result])
            nodes=pd.concat([node1, node2, node3])
            with driver.session() as session:
                result = session.run(cypher_query_edges)
                edges_r = pd.DataFrame([r.data() for r in result])
 
            if nodes.empty:
                return ("No records found")
            var_bind=f"{query_builder_data_node[0]['ld_edge_point_icon']}"

            shareable_and_embeddable_url=graphistry.bind(source="n1", destination="n2",node="id").nodes(nodes).edges(edges_r).encode_point_icon('ConstructRole', shape="circle",as_text=True,categorical_mapping={'Moderator': 'MV', 'IndependentVariable': 'IV', 'Mediator': 'M','DependentVariable': 'DV'},default_mapping="?").addStyle(bg={'color': '#FFFFFF'}).plot(render=False)
            query = urlsplit(shareable_and_embeddable_url).query
            params = parse_qs(query) 

        elif node2 is not None and node3 is None:
            print("Found 2 nodes")
            
            # get the query builder data for 2 node
            query_builder_data_node = await execute_query_builder(node1,node2)

            if not query_builder_data_node:
                print(f"No query builder data found for nodes: node1={node1}, node2={node2}")
                return {}

            cypher_query = f"{query_builder_data_node[0]['ld_match_query']} "
            if keyword1 is not None:
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node1']}  '{keyword1}'  "
            if keyword2 is not None:
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node2']}  '{keyword2}'  "

            cypher_query_node1 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node1']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_node2 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node2']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges = cypher_query + f"RETURN {query_builder_data_node[0]['ld_return_edge1']} limit  {query_builder_data_node[0]['ld_limit']}"
            print(cypher_query_node1)
            print(cypher_query_node2)
            print(cypher_query_edges)
            with driver.session() as session:
                result = session.run(cypher_query_node1)
                node1 = pd.DataFrame([r.data() for r in result])
            with driver.session() as session:
                result = session.run(cypher_query_node2)
                node2 = pd.DataFrame([r.data() for r in result])
            nodes=pd.concat([node1, node2])
            with driver.session() as session:
                result = session.run(cypher_query_edges)
                edges_r = pd.DataFrame([r.data() for r in result])
            if nodes.empty:
                return ("No records found")
            var_bind=f"{query_builder_data_node[0]['ld_edge_point_icon']}"
            shareable_and_embeddable_url=graphistry.bind(source="n1", destination="n2",node="id").nodes(nodes).edges(edges_r).addStyle(bg={'color': '#FFFFFF'}).plot(render=False)
            query = urlsplit(shareable_and_embeddable_url).query
            params = parse_qs(query) 

        elif node2 is None and node3 is None:
            print("Found 1 node")
            
            # get the query builder data for 2 node
            query_builder_data_node = await execute_query_builder(node1)
            if not query_builder_data_node:
                print(f"No query builder data found for node: node1={node1}")
                return {}

            cypher_query = f"{query_builder_data_node[0]['ld_match_query']} "
            if keyword1 is not None:
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node1']}  '{keyword1}'  "

            cypher_query_node1 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node1']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges = cypher_query + f"RETURN {query_builder_data_node[0]['ld_return_edge1']} limit  {query_builder_data_node[0]['ld_limit']}"
            print(cypher_query_node1)
            print(cypher_query_edges)

            with driver.session() as session:
                result = session.run(cypher_query_node1)
                nodes = pd.DataFrame([r.data() for r in result])
            with driver.session() as session:
                result = session.run(cypher_query_edges)
                edges_r = pd.DataFrame([r.data() for r in result])
            if nodes.empty:
                return ("No records found")
            var_bind=f"{query_builder_data_node[0]['ld_edge_point_icon']}"
            shareable_and_embeddable_url=graphistry.bind(source="n1", destination="n1",node="id").nodes(nodes).edges(edges_r).addStyle(bg={'color': '#FFFFFF'}).plot(render=False)
            query = urlsplit(shareable_and_embeddable_url).query
            params = parse_qs(query) 

    except ServiceUnavailable as exception:
        logging.error("Error: {exception}".format(exception=exception))
        raise
    return params['dataset']

query1 = """CALL apoc.meta.stats() YIELD labels
RETURN labels.JournalPublication as Journals, labels.JournalReference as Papers, labels.Publisher as Publishers, labels.Affiliation as Affiliations, labels.Hypothesis as Hypotheses, labels.Author as Authors, labels.Construct as Constructs"""

query2 = """MATCH (ref:JournalReference)-[:APPEARED_IN]->(pub:JournalPublication)
WHERE '1981'> ref.year<= '1990'
    with pub.name as `Journal Name`, "1980-1990" as Years, count(ref) as `No.Of Papers`
RETURN `Journal Name`, Years, `No.Of Papers`
UNION ALL
MATCH (ref:JournalReference)-[:APPEARED_IN]->(pub:JournalPublication)
WHERE '1991'> ref.year<= '2000'
    with pub.name as `Journal Name`, "1991-2000" as Years, count(ref) as `No.Of Papers`
RETURN `Journal Name`, Years, `No.Of Papers`
UNION ALL
MATCH (ref:JournalReference)-[:APPEARED_IN]->(pub:JournalPublication)
WHERE '2001'> ref.year<= '2010'
    with pub.name as `Journal Name`, "2001-2010" as Years, count(ref) as `No.Of Papers`
RETURN `Journal Name`, Years, `No.Of Papers`
UNION ALL
MATCH (ref:JournalReference)-[:APPEARED_IN]->(pub:JournalPublication)
WHERE '2011'> ref.year<= '2020'
    with pub.name as `Journal Name`, "2011-2020" as Years, count(ref) as `No.Of Papers`
RETURN `Journal Name`, Years, `No.Of Papers`
UNION ALL
MATCH (ref:JournalReference)-[:APPEARED_IN]->(pub:JournalPublication)
WHERE '2020'> ref.year<= '2023'
    with pub.name as `Journal Name`, "2020-2023" as Years, count(ref) as `No.Of Papers`
RETURN `Journal Name`, Years, `No.Of Papers`
"""

query3 = """MATCH (c:Construct)-[r:AS]->(cr:`Construct Role`)
WITH c.ConstructRole as role, count(c) as count
MATCH (c2:Construct)
WITH count, role, count(c2) as total
RETURN role, count, toFloat(count) / toFloat(total) * 100 as percentage
"""

response = dict()

@app.get("/dashboardQuery/{queryNo}")
async def get_query(queryNo):

	if queryNo == "1":
		query = query1
	elif queryNo == "2":
		query = query2
	elif queryNo == "3":
		query = query3
	with driver.session() as session:
		info = session.run(query)
		res = info.data()

	json_results = json.dumps(res)
	return json_results

response = dict()

@app.get("/dashboardQuery")
async def get_allQueries():
    with driver.session() as session:
        info = session.run(query1)
        res1 = info.data()
        response["query1"] = res1

        info = session.run(query2)
        res2 = info.data()
        response["query2"] = res2

        info = session.run(query3)
        res3 = info.data()
        response["query2"] = res3
    json_results = json.dumps(response)
    return json_results
