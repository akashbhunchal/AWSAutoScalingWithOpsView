import requests
import json
from boto.regioninfo import *
from boto.ec2.connection import EC2Connection
from boto.ec2.instanceinfo import InstanceInfo
from boto.ec2.autoscale  import AutoScaleConnection
from properties import *
import time
import datetime
import urllib
import urllib2
import sys
import json as jS

ec2_aws_region = RegionInfo(name=metadata["aws_region"], endpoint=metadata["aws_region_endpoint_ec2"])
ec2_conn = EC2Connection(metadata["access_key"],metadata["secret_key"], region=ec2_aws_region)

autoscale_aws_region = RegionInfo(name=metadata["aws_region"], endpoint=metadata["aws_region_endpoint_autoscaling"])
autoscale_conn = AutoScaleConnection(metadata["access_key"],metadata["secret_key"], region=autoscale_aws_region)

reload_counter=0
# First find the terminated instances
terminated_instances = []
for group in metadata['autoscaling_group_list']:
	activities = autoscale_conn.get_all_activities(max_records=metadata["number_of_activities"], autoscale_group=group['as_group_name'])
	for activity in activities:
		instance_id = activity.__dict__.get("description").split(":")[1].strip()
		if len(instance_id) > 10:
			break
		activity_type = activity.__dict__.get("description").split(" ")
		start_time = activity.__dict__.get("start_time")
		diff = datetime.datetime.utcnow() - start_time
		if diff.seconds <= 1800 and 'Terminating' in activity_type : # We are looking at instances added in last 30 mins only
			terminated_instances.append(instance_id)

instances = []
for group in metadata['autoscaling_group_list']:
	activities = autoscale_conn.get_all_activities(max_records=metadata["number_of_activities"], autoscale_group=group['as_group_name'])
	for activity in activities:
		instance_id = activity.__dict__.get("description").split(":")[1].strip()
		if len(instance_id) > 10:
			break
		activity_type = activity.__dict__.get("description").split(" ")
		start_time = activity.__dict__.get("start_time")
		diff = datetime.datetime.utcnow() - start_time
		if diff.seconds <= 1800 and 'Launching' in activity_type : # We are looking at instances added in last one hour only
			reload_counter+=1
			network_interface = ec2_conn.get_all_network_interfaces(filters={"attachment.instance-id":instance_id})
			if len(network_interface) > 0:			
				ip_address = network_interface[0].private_ip_address
				obj = {"instance_id":instance_id, "ip_address":ip_address, "group_name":group['as_group_name'], "hostgroup":group['hostgroup'], 'hosttemplates': group['hosttemplates']}
				instances.append(obj)

# Now logging into opsview

ops_cookies = urllib2.HTTPCookieProcessor()
ops_opener = urllib2.build_opener(ops_cookies)
ops = ops_opener.open(
    urllib2.Request(metadata['opsview_url'] + "rest/login",
    urllib.urlencode(dict({
    'username': metadata['opsview_username'],
    'password': metadata['opsview_password'],
    })))
)
response_text = ops.read()
response = eval(response_text)
if not response:
	print("Cannot evaluate %s" % response_text)
	sys.exit()

if "token" in response:
	print("OPSView authentication succeeded")
	print("Token: %s" % response["token"])
	ops_token = response["token"]
else:
	print("OPSView authentication FAILED")
	sys.exit(1)

# Now adding host to Nagios

for instance in instances:

	host = jS.dumps({
                "name": instance["ip_address"],
                "ip": instance["ip_address"],
				"other_addresses": instance["instance_id"],
				"notification_options" : "u,d,r",
                "hostgroup": instance['hostgroup'],
                "hosttemplates":instance['hosttemplates'],
	           "check_period":{"ref":"/rest/config/timeperiod/1","name":"24x7"},
    	       "notification_period":{"ref":"/rest/config/timeperiod/1","name":"24x7"},
    	       "check_command":{"ref":"/rest/config/hostcheckcommand/15","name":"ping"},
    	       "check_attempts":"2",
    	       "check_interval":"5",
    	       "notification_interval":"30",
	})

	url = metadata['opsview_url'] + "rest/config/host"
	headers = {
            "Content-Type": "application/json",
            "X-Opsview-Username": metadata['opsview_username'],
            "X-Opsview-Token": ops_token,
        }
	request = urllib2.Request(url, host, headers)
	try:
		ops = ops_opener.open(request)
	except urllib2.URLError, e:
		print("Could not add host. %s: %s" % (e.code, e.read()))

# Now removing terminated hosts

for instance in terminated_instances:
	url = metadata['opsview_url'] + "rest/config/host" + "?json_filter={\"other_addresses\":\""+instance+"\"}"

	headers = {
            "Content-Type": "application/json",
            "X-Opsview-Username": metadata['opsview_username'],
            "X-Opsview-Token": ops_token,
    }
	request = urllib2.Request(url,headers=headers)
	try:
		ops = ops_opener.open(request)
	except urllib2.URLError, e:
		print("Could not add host. %s: %s" % (e.code, e.read()))

	output = jS.loads(ops.read())
	if len(output['list']) == 1:
		reload_counter+=1
		url = metadata['opsview_url'] + "rest/config/host/" + output['list'][0]['id']
		headers = {
            "Content-Type": "application/json",
            "X-Opsview-Username": metadata['opsview_username'],
            "X-Opsview-Token": ops_token,
    	}
		request = urllib2.Request(url,headers=headers)
		request.get_method = lambda: 'DELETE'
		try:
			ops = ops_opener.open(request)
		except urllib2.URLError, e:
			print("Could not delete host. %s: %s" % (e.code, e.read()))



# Now reloading OpsView
if reload_counter > 0:
	url = metadata['opsview_url'] + "rest/reload"
	headers = {
            "Content-Type": "application/json",
            "X-Opsview-Username": metadata['opsview_username'],
            "X-Opsview-Token": ops_token,
	}
	host = jS.dumps({})
	request = urllib2.Request(url, host, headers)
	try:
		ops = ops_opener.open(request)
	except urllib2.URLError, e:
		print("Could not add host. %s: %s" % (e.code, e.read()))

	print "Result OpsView Realod:"
	print ops.read()
		
