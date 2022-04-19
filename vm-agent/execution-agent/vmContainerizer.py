from google.cloud import functions_v1
import requests
import wget
import string
from zipfile import ZipFile
import subprocess



def containerize(functionname):
    # Create a client
    client = functions_v1.CloudFunctionsServiceClient()

    # Initialize request arguments
    request = functions_v1.GenerateDownloadUrlRequest(name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"+functionname,
    )

    # Make the request
    response = client.generate_download_url(request=request)
    downloadlink = str(response).split(' ')[1].split('"')[1]
    # Download the function
    print ("\nDownloading the function")
    wget.download(downloadlink,functionname+'.zip')
    request = functions_v1.GetFunctionRequest(
       name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"+functionname,
    )

    # Make the request
    response = client.get_function(request=request)
    entrypoint = response.entry_point

    # Unzip the function
    print ("\nUnzipping the function")
    with ZipFile(functionname+'.zip', 'r') as zipObj:
       zipObj.extractall(functionname)
    with open("/tmp/output.log", "a") as output:
       print ("\nCreating the Docker container \n")
       # Copy the Docker file to the unzipped folder
       subprocess.call("cp Dockerfile "+functionname, shell=True, stdout=output, stderr=output)
       subprocess.call("cp init.sh "+functionname, shell=True, stdout=output, stderr=output)
       file_object = open(functionname+'/main.py', 'a')
       file_object.write('
       def main(event,context):
           if __name__ == '__main__':
               detect(event,context)
')
       file_object.close()
       subprocess.call("cp requirements/"+functionname + ".txt "+ functionname+"/requirements.txt" , shell=True, stdout=output, stderr=output)
       # Create the image from the Dockerfile also copy the function's code
       subprocess.call("cd "+functionname+"; docker build . < Dockerfile --tag name:"+functionname, shell=True, stdout=output, stderr=output)

def run_container(functionname):
    with open("/tmp/output.log", "a") as output:
       print ("\nRunning the Docker container \n")
       subprocess.call("docker run name:"+functionname, shell=True, stdout=output, stderr=output)


def main():
    containerize("Text2SpeechCensoringWorkflow_Profanity")
    run_container("Text2SpeechCensoringWorkflow_Profanity")

if __name__ == '__main__':
    main()
