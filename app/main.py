import json
import logging
import os
from urllib.parse import parse_qs, urlsplit

import graphistry
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase  # for data loader
from neo4j.exceptions import ServiceUnavailable
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
uri=os.getenv("uri")
user=os.getenv("user")
pwd=os.getenv("pwd")
personal_key_id=os.getenv("personal_key_id")
personal_key_secret=os.getenv("personal_key_secret")
postgres_db=os.getenv("DATABASE_URI")

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
            rs = con.execute("SELECT * FROM ltd_node_selection_lov")
            results = [dict(row) for row in rs]
    return {"data": results}

driver = GraphDatabase.driver(uri, auth=(user,pwd))
@app.get("/runQuery")
#TODO add input parameters 
def queryGraphistry(cypherQuery="null"):
    try:
        query = 'MATCH (n1:Construct) return n1.name as name, n1.ConstructRole as ConstructRole'
        with driver.session() as session:
            result = session.run(query)

            # Convert the result to a DataFrame
            constructs = pd.DataFrame([r.data() for r in result])
        query = 'MATCH (i:`Independent Variable`)<-[:AS]-(n1:Construct)<-[*]-(j:JournalReference)-[:STUDIED]->(n2:Construct) RETURN n1.name as n1,j,n2.name as n2 LIMIT 25'
        with driver.session() as session:
            result = session.run(query)
            edges_r=pd.DataFrame([r.data() for r in result])
        shareable_and_embeddable_url=graphistry.bind(source="n1", destination="n2",node="name").nodes(constructs).edges(edges_r).encode_point_icon('ConstructRole',
                  shape="circle",as_text=True,
                 categorical_mapping={
      'Moderator': 'MV', 
      'IndependentVariable': 'IV', 
      'Mediator': 'M',
      'DependentVariable': 'DV'},
                default_mapping="?"
            ).addStyle(bg={'color': '#FFFFFF'}).plot(render=False)
        query = urlsplit(shareable_and_embeddable_url).query
        params = parse_qs(query) 
    except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=query, exception=exception))
            raise
    return params['dataset']

#TODO add functional blocks to give generate graphs for each scenario
# scenarios:
# 1 node
# 2 nodes
# 3 nodes