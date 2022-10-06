from cgi import print_arguments
from lib2to3.pgen2 import driver
from typing import Union
from fastapi import FastAPI  
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json 
import logging
from neo4j.exceptions import ServiceUnavailable
import sys



load_dotenv()
uri=os.getenv("uri")
user=os.getenv("user")
pwd=os.getenv("pwd")

def connection():
  driver=GraphDatabase.driver(uri=uri,auth=(user,pwd))
  return (driver)

app = FastAPI()   
@app.get("/") 
async def main_route():     
  return {"message": "Hey, ACC Cements!!"}


driver_neo4j=connection()

@app.get("/count")
def countnode(label):
    session=driver_neo4j.session(database="Neo4j")
    q1="""MATCH (n) where labels(n) in [[$a]] RETURN n.title as name,count(n) as count"""

    print(q1)
    # q1 = """MATCH (n)  RETURN 
    # count(n) as count"""
    x={"a":label}
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    logging.getLogger("neo4j").addHandler(handler)
    logging.getLogger("neo4j").setLevel(logging.DEBUG)
    results=session.run(q1,x)
    response = {"respose":[{"Name":row["name"],"count":row["count"]}for row in results]} 
    session.close()
    try:
        return response
    except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=q1, exception=exception))
            raise
    # json_data = json.dumps(countnode(label).data())
    #return  JSON.dumps([row.data() for row in results])