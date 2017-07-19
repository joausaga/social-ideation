import appcivist_client
import json

client = appcivist_client.appcivist_api()
client.base_url = "http://localhost:9000"
# client.session_key = appcivist_client.doUpdateSessionkey("http://localhost:9000/api/user/login", "carmen@example.com", "spellhivm")
client.session_key = "f823d17cb7f746b21422d62dae4a206bb0dab949-pa.u.exp=1498750554175&pa.p.id=password&pa.u.id=carmen%40example.com"

print client.session_key

# revisar los controllers a ver que lo que haces
# results = client.get_all_feedback_comments(1)
# # print (results)
# for r in results:
# 	print(r["contributionId"])

# new_proposal = {"status": "PUBLISHED", "title" : "MARCE'S PROPOSAL", "text" : "marce's proposal", "type": "PROPOSAL", "campaigns": [1]}
# new_discussion = {"status": "PUBLISHED", "title" : "MARCE'S DISCUSSION", "text" : "marce's discussion", "type": "DISCUSSION"}
# new_comment = {"status": "PUBLISHED", "title" : "MARCE'S COMMENT", "text" : "marce's comment", "type": "COMMENT"}
# result = client.create_proposal(213 , new_comment)
# print(result)


result = client.get_proposal_details(1, 84)
for k in result.keys():
	print k + " - " + str(result[k])
	# print k


# result = client.get_feedbacks_contribution(1,22)
# for r in result:
# 	for k in r.keys():
# 		print k + " ---------> " + str(r[k])
		# print k

#e1998630-4079-11e5-a151-feff819cdc9f