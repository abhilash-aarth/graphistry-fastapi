import json
import logging
import queries
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
from sqlalchemy import create_engine, text, null, and_
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
            rs = con.execute("SELECT * FROM ld_node_selection_lov order by id")
            results = [dict(row) for row in rs]
    return {"data": results}

driver = GraphDatabase.driver(uri, auth=(user,pwd))

async def execute_query_builder(node1: str, node2: Optional[str] = None, node3: Optional[str] = None) -> dict:
    with engine.connect() as con:
        query = f"SELECT ld_match_query, ld_match_node1, ld_match_node2, ld_match_node3, ld_return_node1, ld_return_node2, ld_return_node3, ld_return_edge1, ld_return_edge2, ld_limit, ld_edge_point_icon FROM ld_query_builder WHERE ld_node1 = '{node1}'"
        if node2 is not None and node2 != "null":
            query += f" AND ld_node2 = '{node2}'"
        else:
            query += " AND ld_node2 =''"
        if node3 is not None and node3 != "null":
            query += f" AND ld_node3 = '{node3}'"
        else:
            query += " AND ld_node3 =''"
        query = text(query)
        print(query)
        rs = con.execute(query, {"node1": node1, "node2": node2, "node3": node3})
        query_builder_data = [dict(row) for row in rs]
        print(query_builder_data)
    if not query_builder_data:
        print(f"No records found for nodes: node1={node1}, node2={node2}, node3={node3}")
        return {}
    return query_builder_data


@app.get("/buildQuery")
async def queryGraphistry(node1: str, keyword1: Optional[str] = "null", node2: Optional[str] = "null", keyword2: Optional[str] = "null", node3: Optional[str] = "null", keyword3: Optional[str] = "null", userId: Optional[str] = "null"):
    try:
        keyword1 = keyword1.lower() if keyword1 != "null" else keyword1
        keyword2 = keyword2.lower() if keyword2 != "null" else keyword2
        keyword3 = keyword3.lower() if keyword3 != "null" else keyword3
        if node2!="null" and node3!="null":
            print("Found 3 nodes")
            
            # get the query builder data for node1
            query_builder_data_node = await execute_query_builder(node1,node2,node3)
            if not query_builder_data_node:
                print(f"No query builder data found for nodes: node1={node1}, node2={node2}, node3={node3}")
                return {}
            cypher_query = f"{query_builder_data_node[0]['ld_match_query']} "
            if keyword1 !="null":
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node1']}  '{keyword1}'  "
            if keyword2 !="null":
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node2']}  '{keyword2}'  "
            if keyword3 !="null":
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node3']}  '{keyword3}'  "
            cypher_query_node1 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node1']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_node2 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node2']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_node3 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node3']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges1 = cypher_query + f"RETURN {query_builder_data_node[0]['ld_return_edge1']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges2 = cypher_query + f"RETURN {query_builder_data_node[0]['ld_return_edge2']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges = cypher_query_edges1 + f" union " + cypher_query_edges2
            print(cypher_query_edges)
            with driver.session() as session:
		node_queries = [cypher_query_node1, cypher_query_node2, cypher_query_node3]
		nodes = pd.concat([pd.DataFrame([r.data() for r in session.run(q)]) for q in node_queries])					
                
		result = session.run(cypher_query_edges)
                edges_r = pd.DataFrame([r.data() for r in result])

            if nodes.empty:
                msg= "No records found"
                await insert_query_history(user_id=userId, node1=node1, keyword1=keyword1, node2=node2, keyword2=keyword2,node3=node3,keyword3=keyword3, error_message=msg)  
                return (msg)
            var_bind=f"{query_builder_data_node[0]['ld_edge_point_icon']}"

            shareable_and_embeddable_url=graphistry.bind(source="n1", destination="n2",node="id").nodes(nodes).edges(edges_r).encode_point_icon('ConstructRole', shape="circle",as_text=True,categorical_mapping={'Moderator': 'MV', 'IndependentVariable': 'IV', 'Mediator': 'M','DependentVariable': 'DV'},default_mapping="?").addStyle(bg={'color': '#FFFFFF'}).plot(render=False)
            query = urlsplit(shareable_and_embeddable_url).query
            params = parse_qs(query)
            await insert_query_history(user_id=userId, node1=node1, keyword1=keyword1, node2=node2, keyword2=keyword2,node3=node3,keyword3=keyword3,dataset=params['dataset'] )   

        elif node2 !="null" and node3 =="null":
            print("Found 2 nodes")
            
            # get the query builder data for 2 node
            query_builder_data_node = await execute_query_builder(node1,node2)

            if not query_builder_data_node:
                print(f"No query builder data found for nodes: node1={node1}, node2={node2}")
                return {}

            cypher_query = f"{query_builder_data_node[0]['ld_match_query']} "
            if keyword1 !="null":
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node1']}  '{keyword1}'  "
            if keyword2 !="null":
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node2']}  '{keyword2}'  "

            cypher_query_node1 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node1']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_node2 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node2']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges = cypher_query + f"RETURN {query_builder_data_node[0]['ld_return_edge1']} limit  {query_builder_data_node[0]['ld_limit']}"
            print(cypher_query_node1)
            print(cypher_query_node2)
            print(cypher_query_edges)
            
            with driver.session() as session:
                node_queries = [cypher_query_node1, cypher_query_node2]
                nodes = pd.concat([pd.DataFrame([r.data() for r in session.run(q)]) for q in node_queries])
		
                result = session.run(cypher_query_edges)
                edges_r = pd.DataFrame([r.data() for r in result])
		
            if nodes.empty:
                msg="No records found"
                await insert_query_history(user_id=userId, node1=node1, keyword1=keyword1, node2=node2, keyword2=keyword2, error_message=msg)  
                return (msg)
            var_bind=f"{query_builder_data_node[0]['ld_edge_point_icon']}"
            shareable_and_embeddable_url=graphistry.bind(source="n1", destination="n2",node="id").nodes(nodes).edges(edges_r).addStyle(bg={'color': '#FFFFFF'}).plot(render=False)
            query = urlsplit(shareable_and_embeddable_url).query
            params = parse_qs(query)
            await insert_query_history(user_id=userId, node1=node1, keyword1=keyword1, node2=node2, keyword2=keyword2, dataset=params['dataset'])  

        elif node2 =="null" and node3 =="null":
            print("Found 1 node")
            
            # get the query builder data for 2 node
            query_builder_data_node = await execute_query_builder(node1)
            if not query_builder_data_node:
                msg=f"No query builder data found for node: node1={node1}"
                print(msg)
                await insert_query_history(user_id=userId, node1=node1, keyword1=keyword1,error_message=msg) 
                return msg

            cypher_query = f"{query_builder_data_node[0]['ld_match_query']} "
            if keyword1 !="null":
                cypher_query += f"AND {query_builder_data_node[0]['ld_match_node1']}  '{keyword1}'  "

            cypher_query_node1 = cypher_query+f"RETURN {query_builder_data_node[0]['ld_return_node1']} limit  {query_builder_data_node[0]['ld_limit']}"
            cypher_query_edges = cypher_query + f"RETURN {query_builder_data_node[0]['ld_return_edge1']} limit  {query_builder_data_node[0]['ld_limit']}"
            print(cypher_query_node1)
            print(cypher_query_edges)

            with driver.session() as session:
                result = session.run(cypher_query_node1)
                df = pd.DataFrame([r.data() for r in result], columns=result.keys())
                edges_r = pd.DataFrame(columns=['n1', 'n2'])
            nodes = graphistry.bind(source="n1", destination="n2",node="id").nodes(df).edges(edges_r)
            if nodes is not None:
                viz = nodes.addStyle(bg={'color': '#FFFFFF'})
                shareable_and_embeddable_url = viz.plot(render=False)
                query = urlsplit(shareable_and_embeddable_url).query
                params = parse_qs(query)
                await insert_query_history(user_id=userId, node1=node1, keyword1=keyword1,dataset=params['dataset']) 
            else:
                msg="No records found"
                print(msg)
                await insert_query_history(user_id=userId, node1=node1, keyword1=keyword1,error_message=msg) 
                return(msg)

    except ServiceUnavailable as exception:
        logging.error("Error: {exception}".format(exception=exception))
        raise
    return params['dataset']

response = dict()

@app.get("/dashboardQuery/{queryNo}")
async def get_query(queryNo):

	if queryNo == "1":
		query = queries.query1
	elif queryNo == "2":
		query = queries.query2
	elif queryNo == "3":
		query = queries.query3
	with driver.session() as session:
		info = session.run(query)
		res = info.data()

	json_results = json.dumps(res)
	return json_results

response = dict()

@app.get("/dashboardQuery")
async def get_allQueries():
    with driver.session() as session:
        info = session.run(queries.query1)
        res1 = info.data()
        response["query1"] = res1

        info = session.run(queries.query2)
        res2 = info.data()
        response["query2"] = res2

        info = session.run(queries.query3)
        res3 = info.data()
        response["query3"] = res3
    json_results = json.dumps(response)
    return json_results

async def insert_query_history(user_id: str, node1: str, keyword1: Optional[str] = None, node2: Optional[str] = None, keyword2: Optional[str] = None, node3: Optional[str] = None, keyword3: Optional[str] = None,dataset:Optional[str] = None ,status:Optional[str] = None ,error_message:Optional[str] = None) -> None:
    with engine.connect() as con:
        query = """
            INSERT INTO ld_user_build_query_log (user_id, node1, keyword1, node2, keyword2, node3, keyword3, dataset, status, error_message)   
            VALUES (:user_id, :node1, :keyword1, :node2, :keyword2, :node3, :keyword3, :dataset, :status, :error_message)
        """
        con.execute(
            text(query),
            user_id=user_id,
            node1=node1,
            keyword1=keyword1,
            node2=node2,
            keyword2=keyword2,
            node3=node3,
            keyword3=keyword3,
            dataset=dataset,
            status=status,
            error_message=error_message
        )
