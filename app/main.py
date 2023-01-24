
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

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]


# graphistry.register(api=3, username='jagadeesh_aarth', password='Prat2020')
# graphistry.register(api=3, token=initial_one_hour_token)
graphistry.register(api=3,personal_key_id='5EH9DONAY5', personal_key_secret='W7LJ3BUDUI6EZ91U', protocol='https', server='hub.graphistry.com')
# NEO4J={'uri':"neo4j+s://6bb63f78.databases.neo4j.io", 'auth':("neo4j", "mib9K3dAFRX_wBZ2BxfNY9LA2rzD7hsrRVkO4MpZc1U")}
# NEO4J={'uri':uri, 'auth':(user, pwd)}
# NEO4J={'uri':"bolt://127.0.0.1:7687", 'auth':("neo4j", "Admin@123")}
NEO4J={'uri':"bolt://neo4j_carlton:7687", 'auth':("neo4j", "Admin@123")}
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



# @app.get("/runQuery")
# def countnode(cypherQuery):
#     try:

#       e_df = pd.DataFrame({
#           's': ['a', 'b', 'c', 'a', 'd', 'e'],
#           'd': ['b', 'c', 'a', 'c', 'e', 'd'],
#           'time': [datetime.datetime(1987, 10, 1), datetime.datetime(1987, 10, 2), datetime.datetime(1987, 10, 3),
#                 datetime.datetime(1988, 10, 1), datetime.datetime(1988, 10, 2), datetime.datetime(1988, 10, 3)]
#       })
#       n_df = pd.DataFrame({
#           'n': ['a', 'b', 'c', 'd', 'e'],
#           'score': [ 0, 30, 50, 70, 90 ],
#           'palette_color_int32': pd.Series(
#               [0, 1, 2, 3, 4],
#               dtype='int32'),
#           'hex_color_int64': pd.Series(
#               [0xFF000000, 0xFFFF0000, 0xFFFFFF00, 0x00FF0000, 0x0000FF00],
#               dtype='int64'),
#           'type': ['mac', 'macbook', 'mac', 'macbook', 'sheep']
#       })
#       g = graphistry.edges(e_df, 's', 'd').nodes(n_df, 'n')
#       print(g._nodes['palette_color_int32'].dtype)

#       g.addStyle(bg={'color': 'grey'}, fg={}, page={'title': 'My Graph'}, logo={'url':'https://cdn.pixabay.com/photo/2021/01/24/19/05/crane-5946169_1280.jpg'}).plot(layout='layout_igraph')
#     except ServiceUnavailable as exception:
#             logging.error("{query} raised an error: \n {exception}".format(
#                 query=e_df, exception=exception))
#             raise
#     # return JSONResponse(content=json_compatible_item_data,headers=headers)
#     return "success"
    #   q1=cypherQuery

    #   g = graphistry.cypher(q1)
    #   shareable_and_embeddable_url=g.plot(render=False)
    #   query = urlsplit(shareable_and_embeddable_url).query
    #   print(query)
    #   params = parse_qs(query)   
    #   print(params)
    # except ServiceUnavailable as exception:
    #         logging.error("{query} raised an error: \n {exception}".format(
    #             query=q1, exception=exception))
    #         raise
    # return params['dataset']

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
    # return JSONResponse(content=json_compatible_item_data,headers=headers)
    return params['dataset']

#TODO add functional blocks to give generate graphs for each scenario
# scenarios:
# 1 node
# 2 nodes
# 3 nodes