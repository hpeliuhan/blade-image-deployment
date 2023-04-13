import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
import os
import time
global DISABLE_RESOURCE_DIR
import Redfish.get_resource_directory
import Redfish.ilorest_util 
from Redfish.ilorest_util import get_gen
from Redfish.ilorest_util import get_resource_directory


#reset server
def reset_server(_redfishobj):
    
    managers_members_response = None
    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Systems']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
            if "ComputerSystem." in instance['@odata.type']:
                managers_members_uri = instance['@odata.id']
                managers_members_response = _redfishobj.get(managers_members_uri)
                
    if managers_members_response:
        path = managers_members_response.obj["Actions"]["#ComputerSystem.Reset"]["target"]
        body = dict()
        resettype = ['ForceRestart','GracefulRestart']
        body["Action"] = "ComputerSystem.Reset"
        for reset in resettype:
            if reset.lower() == "forcerestart":
                body['ResetType'] = "ForceRestart"
                resp = _redfishobj.post(path, body)
            elif reset.lower() == "gracefulrestart":
                body['ResetType'] = "GracefulRestart"
                resp = _redfishobj.post(path, body)

    #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
    #error message to see what went wrong
    if resp.status == 400:
        try:
            print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, sort_keys=True))
        except Exception as excp:
            sys.stderr.write("A response error occurred, unable to access iLO Extended Message "\
                             "Info...")
    elif resp.status != 200:
        sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
    else:
        print("Success!\n")
        print(json.dumps(resp.dict, indent=4, sort_keys=True))


#mount iso

def mount_virtual_media_iso(_redfishobj, iso_url, media_type, boot_on_next_server_reset):

    virtual_media_uri = None
    virtual_media_response = []

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        virtual_media_uri = managers_members_response.obj['VirtualMedia']['@odata.id']
    else:
        for instance in resource_instances:
            #Use Resource directory to find the relevant URI
            if '#VirtualMediaCollection.' in instance['@odata.type']:
                virtual_media_uri = instance['@odata.id']

    if virtual_media_uri:
        virtual_media_response = _redfishobj.get(virtual_media_uri)
        for virtual_media_slot in virtual_media_response.obj['Members']:
            data = _redfishobj.get(virtual_media_slot['@odata.id'])
            if media_type in data.dict['MediaTypes']:
                virtual_media_mount_uri = data.obj['Actions']['#VirtualMedia.InsertMedia']['target']
                post_body = {"Image": iso_url}

                if iso_url:
                    resp = _redfishobj.post(virtual_media_mount_uri, post_body)
                    if boot_on_next_server_reset is not None:
                        patch_body = {}
                        patch_body["Oem"] = {"Hpe": {"BootOnNextServerReset": \
                                                 boot_on_next_server_reset}}
                        boot_resp = _redfishobj.patch(data.obj['@odata.id'], patch_body)
                        if not boot_resp.status == 200:
                            sys.stderr.write("Failure setting BootOnNextServerReset")
                    if resp.status == 400:
                        try:
                            print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                    sort_keys=True))
                        except Exception as excp:
                            sys.stderr.write("A response error occurred, unable to access iLO"
                                             "Extended Message Info...")
                    elif resp.status != 200:
                        sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
                    else:
                        print("Success!\n")
                        print(json.dumps(resp.dict, indent=4, sort_keys=True))
                break

#change boot order once
def change_temporary_boot_order(_redfishobj, boottarget):

    systems_members_uri = None
    systems_members_response = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        systems_uri = _redfishobj.root.obj['Systems']['@odata.id']
        systems_response = _redfishobj.get(systems_uri)
        systems_members_uri = next(iter(systems_response.obj['Members']))['@odata.id']
        systems_members_response = _redfishobj.get(systems_members_uri)
    else:
        for instance in resource_instances:
            if '#ComputerSystem.' in instance['@odata.type']:
                systems_members_uri = instance['@odata.id']
                systems_members_response = _redfishobj.get(systems_members_uri)

    if systems_members_response:
        print("\n\nShowing BIOS attributes before changes:\n\n")
        print(json.dumps(systems_members_response.dict.get('Boot'), indent=4, sort_keys=True))
    body = {'Boot': {'BootSourceOverrideTarget': boottarget}}
    resp = _redfishobj.patch(systems_members_uri, body)

    #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
    #error message to see what went wrong
    if resp.status == 400:
        try:
            print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, sort_keys=True))
        except Exception as excp:
            sys.stderr.write("A response error occurred, unable to access iLO Extended Message "\
                             "Info...")
    elif resp.status != 200:
        sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
    else:
        print("\nSuccess!\n")
        print(json.dumps(resp.dict, indent=4, sort_keys=True))
        if systems_members_response:
            print("\n\nShowing boot override target:\n\n")
            print(json.dumps(systems_members_response.dict.get('Boot'), indent=4, sort_keys=True))
#reboot server


def reboot_server(_redfishobj):

    systems_members_response = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        systems_uri = _redfishobj.root.obj['Systems']['@odata.id']
        systems_response = _redfishobj.get(systems_uri)
        systems_uri = next(iter(systems_response.obj['Members']))['@odata.id']
        systems_response = _redfishobj.get(systems_uri)
    else:
        for instance in resource_instances:
            #Use Resource directory to find the relevant URI
            if '#ComputerSystem.' in instance['@odata.type']:
                systems_uri = instance['@odata.id']
                systems_response = _redfishobj.get(systems_uri)

    if systems_response:
        system_reboot_uri = systems_response.obj['Actions']['#ComputerSystem.Reset']['target']
        body = dict()
        resettype = ['ForceRestart','GracefulRestart']
        body['Action'] = 'ComputerSystem.Reset'
        for reset in resettype:
            if reset.lower() == "forcerestart":
                body['ResetType'] = "ForceRestart"
                resp = _redfishobj.post(system_reboot_uri, body)
            elif reset.lower() == "gracefulrestart":
                body['ResetType'] = "GracefulRestart"
                resp = _redfishobj.post(system_reboot_uri, body)

        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                    sort_keys=True))
            except Exception as excp:
                sys.stderr.write("A response error occurred, unable to access iLO Extended "
                                 "Message Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("Success!\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))


#create node class

class node:
    def __init__(self,ip,user,password,target_os):
        self.ip=ip
        self.user=user
        self.password=password
        self.target_os=target_os
        self.rest_url="https://"+ip
        self.status="undeployed"
        try:
            
            # Create a Redfish client object
            self.REDFISHOBJ = RedfishClient(base_url=self.rest_url, username=self.user, password=self.password)
            # Login with the Redfish client
            self.REDFISHOBJ.login()
        except ServerDownOrUnreachableError as excp:
            sys.stderr.write("ERROR: server not reachable or does not support RedFish.\n")
            sys.exit()

    def install(self):
        if self.status=="undeployed":
            print("mount "+self.ip+" iso "+self.target_os)
            BOOT_ON_NEXT_SERVER_RESET = False
            mount_virtual_media_iso(self.REDFISHOBJ, self.target_os, 'CD', BOOT_ON_NEXT_SERVER_RESET)
            time.sleep(5)
            change_temporary_boot_order(self.REDFISHOBJ, 'Usb')
            time.sleep(5)
            print("resetting "+self.ip)
            reboot_server(self.REDFISHOBJ)
            self.status="deploying"

    def check_status(self):
        return self.status
    

if __name__ == '__main__':
    #set environment parameters
    CONFIG_FILE="/config/nodes_config"
    http_server_root="http://10.106.99.99/iso/"
    config_f=open(CONFIG_FILE,'r')
    lines=config_f.readlines()
    DISABLE_RESOURCE_DIR = False
    nodes=[]
    for line in lines:
        words=line.split(" ")
        nodes.append(node(words[0],words[1],words[2],http_server_root+words[3]))


    for node in nodes:
        node.install()
