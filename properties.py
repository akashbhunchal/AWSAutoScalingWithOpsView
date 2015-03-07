metadata={
	"opsview_url":"http://<opsview_ip>/",
	"opsview_username":"<opsview username>",
	"opsview_password":"<opsview password>",
	"access_key":"<access_key>",
	"secret_key":"<secret key>",
	"aws_region":"ap-southeast-1",
	"aws_region_endpoint_ec2":"ec2.ap-southeast-1.amazonaws.com",
	"aws_region_endpoint_autoscaling":"autoscaling.ap-southeast-1.amazonaws.com",
	"autoscaling_group_list":[{'as_group_name':'<autoscaling group name>',
							   'hostgroup':{"ref":'/rest/config/hostgroup/3', "name":'akash_temp_as'},
							   'hosttemplates':[{"ref":"/rest/config/hosttemplate/66","name":"akash_temp_template"}],
							   },
							   #.....
							   # Add more such mappings
							  ],
	"number_of_activities":100,# Number of activities that this script will fetch which happened in the last 30 mins. Increase this value if you expect the number of activities to be higher.
}



