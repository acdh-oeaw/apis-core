def calculate_age(row, age_field):
    try:
        year = row['year']
    except ValueError:
        year = None
    try:
        age = int(str(row[age_field])[:4])
    except ValueError:
        age = None
    if year and age:
        return year-age
    else:
        return 0
