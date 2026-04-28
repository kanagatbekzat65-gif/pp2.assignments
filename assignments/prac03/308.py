class Account:
    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if amount > self.balance:
            return 
        else:
            self.balance -= amount
            return self.balance


B, W = map(int, input().split())

acc = Account("", B)

result = acc.withdraw(W)
print(result)