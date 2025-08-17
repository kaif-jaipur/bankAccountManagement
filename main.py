import json,random,string
from pathlib import Path
class Bank:
    database='data.json'
    data=[]

    try:
        if Path(database).exists:
            with open(database) as fs:
                data=json.loads(fs.read())
        else:
            print("no such file exist")
    except Exception as err:
        print(f"An exception accured as{err}")

    @classmethod
    def __Update(cls):
        with open(cls.database,'w')as fs:
            fs.write(json.dumps(cls.data))    

    @classmethod
    def __accoungenrete(cls):
        alpha=random.choices(string.ascii_letters,k=3)
        num=random.choices(string.digits,k=3)
        spchar=random.choices("!@#%^&*",k=1)
        id=alpha+num+spchar
        random.shuffle(id)
        return "".join(id)

    def depositMony(self):
        accnumber=input("tell your account number :- ")
        pin=int(input("please tell your pin as well"))

        userdata = [i for i in Bank.data if i['accountNo.']==accnumber and i['pin']==pin]
        print(f"{userdata}mk2003")
        if userdata == []:
            print("Sorry no data found !")
        else:
            amount=int(input("how much amount do you want to deposite "))
            if amount>10000 or amount<=0:
                print("Sorry this amount is too much you can deposite below 10000 and above 0")
            else:
                print(userdata)
                userdata[0]['balance'] += amount
                Bank.__Update()
                print("amount deposit succesfully")

    def withdrawMony(self):
        accnumber=input("tell your account number :- ")
        pin=int(input("please tell your pin as well"))

        userdata = [i for i in Bank.data if i['accountNo.']==accnumber and i['pin']==pin]
        print(f"{userdata}mk2003")
        if userdata == []:
            print("Sorry no data found !")
        else:
            amount=int(input("how much amount do you want to withdrawl "))
            if amount > userdata[0]['balance'] or amount>=0:
                print("Sorry you can't withdrawl please try again !")
            else:
                print(userdata)
                userdata[0]['balance'] -= amount
                Bank.__Update()
                print("amount withdrawn succesfully")

    def deletegData(self):
        accnumber=input("Enter your account number :- ")
        pin=int(input("please tell your pin as well"))

        userdata=[i for i in Bank.data if i['accountNo.'] == accnumber and i['pin'] == pin]
        if userdata == []:
            print("No data found")
        else:
            index=Bank.data.index(userdata[0])
            Bank.data.pop(index)
            print ("Account deleted succesfully")

            Bank.__Update()


    def details(self):
        accnumber=input("Enter your account number :- ")
        pin=int(input("please tell your pin as well"))

        userdata=[i for i in Bank.data if i['accountNo.'] == accnumber and i['pin'] == pin]
        if userdata == []:
            print("No data found")
        else:
            print("your details are :- \n\n")
            for i in userdata[0]:
                print(f"{i} :- {userdata[0][i]}")

    def updatingData(self):
        accnumber=input("Enter your account number :- ")
        pin=int(input("please tell your pin as well"))

        userdata=[i for i in Bank.data if i['accountNo.'] == accnumber and i['pin'] == pin]
        if userdata == []:
            print("No data found")
        else:
            print("you can't change the age,accoun Number, balance")

            print("Fill the details for change or leave it empty if no change ")

            newdata={
                "name":input("Enter new name or prese enter to skip :- "),
                "email":input("Enter new email or prese enter to skip :- "),
                "pin":int(input("Enter new pin or prese enter to skip :- "))
            }
            if newdata["name"] == "":
                newdata["name"]=userdata[0]['name']
            if newdata["email"] == "":
                newdata["email"]=userdata[0]['email']
            if newdata["pin"] == "":
                newdata["pin"]=userdata[0]['pin']
            newdata["age"]=userdata[0]['age']
            newdata["accountNo."]=userdata[0]['accountNo.']
            newdata["balance"]=userdata[0]['balance']

            if type(newdata["pin"])==str:
                newdata["pin"]=int(newdata["pin"])
            
            for i in newdata:
                if newdata[i]== userdata[0][i]:
                    continue
                else:
                    userdata[0][i]=newdata[i]
            Bank.__Update()
            print("data updated succesfully")
            

    def createAccount(self):
        info={
            "name":input("Tell your name :- "),
            "age":int(input("Tell your age :- ")),
            "email":input("Tell your email :- "),
            "pin":int(input("Tell your pin :- ")),
            "accountNo.":Bank.__accoungenrete(),
            "balance":0
        }
        if info['age']<18 or len(str(info["pin"])) !=4:
            print("Sorry you can't create your account")
        else :
            print("account has been created successsfully")
            for i in info:
                print(f"{i}:{info[i]}")
            print("plrase notedown your account number")

            Bank.data.append(info)
            Bank.__Update()


user=Bank()
print("press 1 for creating an account :- ")
print("press 2 for Deposit the mony in account :- ")
print("press 3 for Withdrawing mony from  account")
print("press 4 for Details  :- ")
print("press 5 for Updating Details :-  ")
print("press 6 for Deleting your account :-  ")

cheack=int (input("tell your response :- "))
if cheack==1:
    user.createAccount()
elif cheack==2:
    user.depositMony()
elif cheack==3:
    user.withdrawMony()
elif cheack==4:
    user.details()
elif cheack==5:
    user.updatingData()
elif cheack==6:
    user.deletegData()
