# AWSAutoScalingWithOpsView
Python Script for AWS Autoscaling integration with OpsView

### How it works.

Setup the script as a cron job which runs every 5 mins in machine which has both internet access as well access to OpsView server. The script will check for autoscaling events that happened in the last 30 mins and add/remove nodes accordingly. The reason I did not build as PI based system which can be called through SNS by Autoscaling is the way OpsView reload is built. If 5 requests are invoked at the same time OpsView reload would happen in 5 threads which will just kill OpsView server performance.

In the current script reload happens only once when all the nodes have been added/deleted.

### How to run

Set it up as a cron job on your machine. The command is simple

**python <full_path>/opsview_add.py**
