f = open("temperatures.csv")
big_str = f.read()

line_list = big_str.split("\n")

cities_list = []
temp_list = []

for line in line_list:
    value_list = line.split(",")
    city = value_list[0]
    cities_list.append(city)
    
    date = value_list[1]
    temp = float(value_list[2])
    temp_list.append(temp)
    
print('cities: ', cities_list)
print('temperatures: ', temp_list)
