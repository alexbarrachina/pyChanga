
class Inventory:
    def __init__(self, initial_items):
        self.myItems = initial_items
        
    def addItem(self, item):
        # your code here
        self.myItems.append(item)
    
    def sellItem(self, item):
        # your code here
        self.myItems.remove(item)
        
    def retireItem(self):
        # your code here
        self.myItems.pop()

    def getList(self):
        # your code here
        return self.myItems
        
    def findItem(self,item):
        # your code here
        isinlist = False
        if item in self.myItems:
            isinlist = True
        return isinlist

# 1/ Write a class that manages an inventory of items with the following funcions:
# __init__ -> pass a list of initial items
# addItem -> add new items to a list (at the end of the list)
# sellItem -> remove a specific item from the list
# retireItem -> remove the older item (the fist)
# findItem -> find if an item is in the list or not

inv1 = Inventory(["cavall", "gos", "gat"])
inv1.addItem("flauta")
print(inv1.getList())
                 