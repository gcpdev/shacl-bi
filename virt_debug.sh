#!/bin/bash
set -euo pipefail

CONTAINER_NAME=virtuoso     # change if different
SPARQL_URL="http://127.0.0.1:8890/sparql"
APPUSER="appuser"
APPPWD="secret"

echo "=== Running diagnostics for container: $CONTAINER_NAME ==="
echo

echo "1) Container status:"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

echo "2) Which volumes are mounted to the container (inspect):"
docker inspect --format='{{json .Mounts}}' ${CONTAINER_NAME} | python -m json.tool || true
echo

echo "3) List SQL users (via isql):"
docker exec -i ${CONTAINER_NAME} /opt/virtuoso-opensource/bin/isql 1111 dba dba <<'SQL'
set result_transform off;
SELECT U_NAME, U_ID FROM DB.DBA.SYS_USERS ORDER BY U_ID;
SQL
echo

echo "4) Check specific users and privileges:"
docker exec -i ${CONTAINER_NAME} /opt/virtuoso-opensource/bin/isql 1111 dba dba <<SQL
set result_transform off;
SELECT U_NAME, U_ID FROM DB.DBA.SYS_USERS WHERE U_NAME IN ('appuser','SPARQL','nobody');
SELECT * FROM DB.DBA.SYS_USER_PRIVILEGES WHERE U_NAME IN ('appuser','SPARQL','nobody') ORDER BY U_NAME;
SQL
echo

echo "5) Show relevant virtuoso.ini sections (inside container):"
docker exec -i ${CONTAINER_NAME} bash -lc "grep -n -E '^\[SPARQL\]|\[HTTPServer\]|\[Parameters\]|\[HTTP\]' /etc/virtuoso/virtuoso.ini || true"
echo "---- virtuoso.ini excerpt (SPARQL + HTTPServer sections) ----"
docker exec -i ${CONTAINER_NAME} bash -lc "awk '/^\[SPARQL\]/,/^\[/{if(NR>1)print}' /etc/virtuoso/virtuoso.ini || true"
echo
docker exec -i ${CONTAINER_NAME} bash -lc "awk '/^\[HTTPServer\]/,/^\[/{if(NR>1)print}' /etc/virtuoso/virtuoso.ini || true"
echo

echo "6) Show initdb dir mounted into container (if present):"
docker exec -i ${CONTAINER_NAME} bash -lc "ls -la /docker-entrypoint-initdb.d || true"
docker exec -i ${CONTAINER_NAME} bash -lc "echo '---- init.sql contents if present ----'; for f in /docker-entrypoint-initdb.d/*; do echo '-----' \\\$f; sed -n '1,200p' \\\$f; done || true"
echo

echo "7) Tail Virtuoso logs (last 400 lines):"
# location may vary by image; check common locations
docker exec -i ${CONTAINER_NAME} bash -lc "if [ -f /var/lib/virtuoso/db/virtuoso.log ]; then tail -n 400 /var/lib/virtuoso/db/virtuoso.log; elif [ -f /database/virtuoso.log ]; then tail -n 400 /database/virtuoso.log; else echo 'virtuoso.log not found at known paths'; fi"
echo

echo "8) Try authenticated SPARQL update (curl POST with Basic Auth) — expected: success or a 200/204"
echo "---- Running curl authenticated update (INSERT DATA) ----"
docker run --rm --network host curlimages/curl:7.90.0 -s -S -u ${APPUSER}:${APPPWD} \
  -X POST \
  --data-urlencode "update=INSERT DATA { GRAPH <http://example.org/test> { <http://example.org/s> <http://example.org/p> \"t\" } }" \
  "${SPARQL_URL}" -w "\nHTTP_STATUS:%{http_code}\n" || echo "curl failed"
echo

echo "9) Try unauthenticated SPARQL update (should fail if auth required):"
docker run --rm --network host curlimages/curl:7.90.0 -s -S \
  -X POST \
  --data-urlencode "update=INSERT DATA { GRAPH <http://example.org/test> { <http://example.org/s> <http://example.org/p> \"u\" } }" \
  "${SPARQL_URL}" -w "\nHTTP_STATUS:%{http_code}\n" || echo "curl failed"
echo

echo "10) Make a SPARQL query (authenticated) to verify graph content (SELECT):"
docker run --rm --network host curlimages/curl:7.90.0 -s -S -u ${APPUSER}:${APPPWD} \
  --data-urlencode "query=SELECT * WHERE { GRAPH <http://example.org/test> { ?s ?p ?o } }" \
  "${SPARQL_URL}" -H "Accept: application/sparql-results+json" -w "\nHTTP_STATUS:%{http_code}\n" || echo "curl failed"
echo

echo "=== Diagnostics complete ==="
