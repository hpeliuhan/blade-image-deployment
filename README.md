# blade-image-deployment

## Introduction
This is an auto deployment tool for waggle blade image on HPE hardware
The tool will compose a container thats runs http server which hosts the iso images and deploy this iso image to Edge blades using HPE ilo restful API.
## Deployment steps
The images are build from：https://github.com/waggle-sensor/blade-image. User will need to copy the built images to the iso folder.To depoly the waggle-sensor blade image to multiple nodes, user need to specify the HPE ILO info of each nodes following by this format seperated by space:

| IP | Username | Password | ImagetoDeploy |

Users will run: 'docker-compose up --build' to start the deployment.
 
## Future works:
 1. PXE support for universal x86_64 systems
 2. Auto registration to sagecontinuum beekeeper.
 
 
