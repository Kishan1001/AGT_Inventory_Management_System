# ## this code will remove all Adudit logs havin ,, Reason = Excel upload (initial)
# ## this code will remove all Adudit logs havin ,, Reason = Excel upload (initial)
#
#
# from pymongo import MongoClient
#
# client = MongoClient("mongodb+srv://agt_inventory_manager:agt_inventory_pass@cluster0.xuaj2a3.mongodb.net/AGT?retryWrites=true&w=majority&appName=Cluster0")
# db = client["AGT"]
# col = db["inventory_history"]
#
# result = col.delete_many({"Reason": "Excel upload (initial)"})
# print(f"Deleted: {result.deleted_count}")
#
