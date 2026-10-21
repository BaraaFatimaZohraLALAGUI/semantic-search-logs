# semantic-search-logs


attempting to build semantic search for some synthetic logs: 
generating logs -> embedding -> storing in elastic

- cisco logs 
- sophos logs
- external websites access logs
- postfix mailing logs 
- embedded and queried 

- next to work on is translate the resukt to human readable report 


### to run the app :
`docker compose up --build`

### access through: 

- for the streamlit app to query: http://localhost:8501/
- for kibana to see the logs and database : http://localhost:5601/
- to check elastic running: http://localhost:9200/