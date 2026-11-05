import bom_queries, lcsc
done = 0
for k, (q, pk, must) in bom_queries.Q.items():
    try:
        lcsc.search(q)
        done += 1
    except RuntimeError as e:
        print('FAIL', q, e)
print('fetched', done, 'of', len(bom_queries.Q))
