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
