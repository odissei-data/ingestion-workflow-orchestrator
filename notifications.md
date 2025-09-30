Notifications
=============

When workflows fail notifications should be sent (to a Slack channel) in order for the person(s) 
responsible for the service to check the logs and fix the problems. 


# Configure Slack

There is a Slack workplace created for the messages about the Odissei Ingest (workflows) with the name `odissei-ingest`.
In this workspace there is a `prefect-notifications` channel that will be used for sending 
the notifications from the prefect workflow on failures. 
Using the Slack Api page a ‘Webhook App' application was created . 
With this application there is a 'Webhooks Features' option that allows to create new webhooks. The URL for this newly created webhook is then used for the configuration of Prefect, described in the next section. 

The 'sample’ URL looks like this: 
```
curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/<unique string here>
```
You can test this on the commandline, the message should appear in that Slack channel. 

# Configure Prefect

Create a ‘Slack Webhook Block’ in the Prefect UI. That webhook URL from Slack is pasted into the the URL field of that block. The Prefect UI will give sample code to be placed inside your flow code in order to notify. This has been used in the code at the point where the 'bucket' with the failure information (failed dataset PIDs) is created. 
The simplest way to test if it works is to force an error by using wrong API key. Then check the logs, the Slack channel and the 'bucket'. 
