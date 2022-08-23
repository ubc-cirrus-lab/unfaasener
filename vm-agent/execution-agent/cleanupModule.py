import docker
import sys
import time
from datetime import datetime, timedelta


def main():
#    run_container(sys.argv[1])

    client_api = docker.APIClient(base_url='unix://var/run/docker.sock')
    info = client_api.df()
    for container in info['Containers']:
      if (('Created' in container) and (container['State'] == 'running')):
        print(container['Created'])
        created_at = datetime.fromtimestamp((container['Created']))
        print (created_at)
        if (created_at + timedelta(seconds=int(sys.argv[1])) < datetime.now()):
            print ("Container too old... Stopping It")
            client_api.stop(container)





if __name__ == '__main__':
    while True:
      time.sleep(5)
      main()



