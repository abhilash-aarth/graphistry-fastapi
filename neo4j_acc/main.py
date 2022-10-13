from cgi import print_arguments
from lib2to3.pgen2 import driver
from multiprocessing.sharedctypes import Value
from typing import Union
from urllib import response
from webbrowser import get
from fastapi import FastAPI  
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json 
import logging
from neo4j.exceptions import ServiceUnavailable
import sys
from geopy.geocoders import Nominatim
from geopy import geocoders 
import geocoder 
import json 
from pydantic import BaseModel

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

# class nodemodel(BaseModel):
#   lng:float
#   lat:float

driver_neo4j=connection()

@app.get("/count")
def countnode(limit=None):
    limit_query = ""
    if limit:
      limit_query = f"LIMIT {limit}"
    session=driver_neo4j.session(database="Neo4j")
    array = []
    try:
      session=driver_neo4j.session(database="Neo4j")
      q1=f"MATCH (n:City) where  not exists (n.lat) RETURN n.ccode as ccode,COALESCE(n.cname,n.districtname) as cname {limit_query}"

      print(q1)
      # q1 = """MATCH (n)  RETURN 
      # count(n) as count"""
      # x={"a":label}
      handler = logging.StreamHandler(sys.stdout)
      handler.setLevel(logging.DEBUG)
      logging.getLogger("neo4j").addHandler(handler)
      logging.getLogger("neo4j").setLevel(logging.DEBUG)
      results=session.run(q1)
      array = [{"ccode":row["ccode"], "cname":row["cname"]}for row in results]
  

      # response = {"respose":[{"ccode":row["ccode"],"coordinates": get_coordinates(row["cname"]), "cname":row["cname"]}for row in results]} 

    
    except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=q1, exception=exception))
            raise
    finally:
      session.close()
    try:
      vcount=0
      for row in array:
        vcount=+1
        coordinates = get_coordinates(row['cname'])
        print (coordinates)
        if coordinates['lat'] is not None :
          update_city(coordinates,row['ccode'])
        
        row["coordinates"] = coordinates
    except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                 exception=exception))
            raise
    return "success count " +str(vcount)

@app.get("/map")
def get_coordinates(location):
    # return {"lat": location}
    gn = geocoder.bing(location, key='Aixqs7U_a7rhJavAccjoCNDWV96fzDgULkUSvM4b9VJ-cGrj0dgyhZlYj_GstGc-', maxRows=1) 
    results = gn.json
    if gn.status != "OK":
      return {
        "lat": "",
        "lng": ""
      }
    else:
      return {
        "lat": results['lat'],
        "lng": results['lng']
        }

def update_city(node, cccode):
      driver_neo4j=connection()
      session=driver_neo4j.session(database="Neo4j")
      update_query="""
      MATCH (n:City {ccode: $cccode}) SET n.long = $lng , n.lat= $lat return n.ccode 
      """
      print (update_query)
      print( node)
      x={"cccode":cccode,"lat":node["lat"],"lng":node["lng"]}
      results=session.run(update_query,x)
      session.close()