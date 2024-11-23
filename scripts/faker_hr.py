from faker import Faker
import random

fake = Faker()
for _ in range(10):
    with open(f"data/employee_{random.randint(1, 100)}.txt", "w") as f:
        f.write(f"Name: {fake.name()}\n")
        f.write(f"Position: {fake.job()}\n")
        f.write(f"Performance: {random.choice(['Excellent', 'Good', 'Average', 'Poor'])}\n")

