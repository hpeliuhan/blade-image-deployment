FROM python:latest
WORKDIR /usr/app/src


RUN apt-get update
RUN apt-get install -y apache2
RUN apt-get install -y apache2-utils
RUN apt-get clean
RUN mkdir /var/www/html/iso
RUN chmod 755 /var/www/html/iso
RUN mkdir ./config


RUN apt-get update && apt-get install python3-pip -y
COPY requirements.txt .
RUN pip3 install -r requirements.txt

EXPOSE 80 
CMD ["apache2ctl","-D","FOREGROUND"]
ADD Redfish ./Redfish
COPY agent.py ./

CMD ["python3","agent.py"]
