import pandas as pd
import neo4j # just for testing
from neo4j import GraphDatabase # for data loader
import graphistry
print('neo4j', neo4j.__version__)
print('graphistry', graphistry.__version__)
# To specify Graphistry account & server, use:
# graphistry.register(api=3, username='...', password='...', protocol='https', server='hub.graphistry.com')
# graphistry.register(api=3, protocol="https", server="hub.graphistry.com", username="...", password="...")  
# For more options, see https://github.com/graphistry/pygraphistry#configure

# graphistry.register(api=3, username='jagadeesh_aarth', password='Prat2020')

# g = graphistry.bind(source="source", destination="target")
# g.edges(links).plot()
NEO4J={'uri':"bolt://localhost:7687", 'auth':basic_auth("neo4j", "Admin@123")}
graphistry.register(bolt=NEO4J)
def connection():
  driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "Admin@123"))
  return (driver)
driver_neo4j=connection()

session=driver_neo4j.session(database="Neo4j")
q1="MATCH (a) RETURN COUNT(a) AS num"
results=session.run(q1)
for record in results:
    print(record)