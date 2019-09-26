Quick Python Script to plot historical evetns from Kentik Data
Best to run this using Docker Compose and HarperDB.
Edit docker-compose.yml and adjust the Kentik API Enviroment Vars as needed.
Use the command "docker-compose up -d" to run.  Note this can take several hours to complete.

The following environment vars are required:
KENTIK_API_USER=""
KENTIK_API_PASSWORD=""
HARPERDB_URL=""
HARPERDB_USER=""
HARPERDB_PASSWORD

Be sure to export them too
export KENTIK_API_USER
export KENTIK_API_PASSWORD
export HARPERDB_URL
export HARPERDB_USER
export HARPERDB_PASSWORD
