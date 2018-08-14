#!/bin/sh

sudo docker run  mistral-all cat /opt/stack/mistral/mistral/actions/openstack/mapping.json > mapping.json.org
sudo docker run  mistral-all cat /opt/stack/mistral/mistral/db/v2/api.py > api.py.org
sudo docker run  mistral-all cat /opt/stack/mistral/mistral/cmd/launch.py > launch.py.org
sudo docker run  mistral-all cat /opt/stack/mistral/tools/sync_db.py > sync_db.py.org

sudo docker run  mistral-all cat /opt/stack/mistral/mistral/engine/tasks.py > tasks.py.org
sudo docker run  mistral-all cat /opt/stack/mistral/mistral/engine/workflows.py > workflows.py.org

sudo docker run  mistral-all cat /opt/stack/mistral/mistral/api/controllers/v2/root.py  > root.py.org

# /home/auv/eoe/dx/mistral-dev/mistral/utils/kfk_client.py 
# /home/auv/eoe/dx/mistral-dev/mistral/utils/kfk_etypes.py 
# /home/auv/eoe/dx/mistral-dev/mistral/utils/kfk_trace.py  


