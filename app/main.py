
from pandas import DataFrame
import datetime, pandas as pd
import neo4j # just for testing
from neo4j import GraphDatabase # for data loader
import graphistry
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
import json
from fastapi import FastAPI  
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import numpy as np
import matplotlib.pyplot as plt
from urllib.parse import urlsplit, parse_qs
from fastapi.middleware.cors import CORSMiddleware

# print('neo4j', neo4j.__version__)
# print(dir(graphistry))
# print('graphistry', graphistry.__version__)
DELETE_EXISTING_DATABASE=False
POPULATE_DATABASE=False
load_dotenv()
uri=os.getenv("uri")
user=os.getenv("user")
pwd=os.getenv("pwd")
personal_key_id=os.getenv("personal_key_id")
personal_key_secret=os.getenv("personal_key_secret")
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]



graphistry.register(api=3,personal_key_id=personal_key_id, personal_key_secret=personal_key_secret, protocol='https', server='hub.graphistry.com')
NEO4J={'uri':uri, 'auth':(user, pwd)}
graphistry.register(bolt=NEO4J)


def connection():
  driver=GraphDatabase.driver(uri=uri,auth=(user,pwd))
  return (driver)
driver_neo4j=connection()
app = FastAPI()  
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/") 
async def main_route():     
  return {"message": "Hey, Graphistry!!"}

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
            ).plot(render=False)
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