# Data lists

x_data_raw = [1.23, 4.56, -7.89, 2.34, 5.67, -5.73, 2.51, 9.832]
y_data_raw = [-3.45, -6.78, 9.01, -2.34, 7.89, -1.23, 4.56, -6.91]
z_data_raw = [2.34, -5.67, 8.90, -1.23, 6.78, -3.45, 7.89, -2.56]
x_rot_data_raw = [0.12, -0.34, 0.56, -1.78, 0.90, -2.11, 3.22, -3.33]
y_rot_data_raw = [-0.45, 2.67, -0.89, 0.12, -5.34, 3.56, -0.78, 0.90]
z_rot_data_raw = [1.23, -2.45, 3.67, -4.89, 0.12, -0.34, 0.56, -0.78]

# Remove values between -1 and 1

x_data = [x for x in x_data_raw if abs(x) >= 1]
y_data = [y for y in y_data_raw if abs(y) >= 1]
z_data = [z for z in z_data_raw if abs(z) >= 1]
x_rot_data = [xr for xr in x_rot_data_raw if abs(xr) >= 1]
y_rot_data = [yr for yr in y_rot_data_raw if abs(yr) >= 1]
z_rot_data = [zr for zr in z_rot_data_raw if abs(zr) >= 1]


def psuedorandom():

    avg_last_data = (x_data[-1] + y_data[-1] + z_data[-1] + x_rot_data[-1] + y_rot_data[-1] + z_rot_data[-1]) / 6

    frac = abs(avg_last_data) % 1
    index = int(frac * 10)
    return [index % 2, index]

result = psuedorandom()


# Make sure the dominant motion gives its dimension
y_neg_data = [y for y in y_data if y < 0]
y_pos_data = [y for y in y_data if y > 0]
z_pos_data = [z for z in z_data if z > 0]
z_neg_data = [z for z in z_data if z < 0]


#FIX: DIVIDE BY ZERO ERROR IF NO DATA POINTS
def determine_motion():
    x_avg = sum(abs(x) for x in x_data) / len(x_data)
    y_neg_avg = sum(abs(y) for y in y_neg_data) / len(y_neg_data) if y_neg_data else 0
    y_pos_avg = sum(abs(y) for y in y_pos_data) / len(y_pos_data) if y_pos_data else 0
    z_neg_avg = sum(abs(z) for z in z_neg_data) / len(z_neg_data) if z_neg_data else 0
    z_pos_avg = sum(abs(z) for z in z_pos_data) / len(z_pos_data) if z_pos_data else 0
    xr_avg = sum(abs(xr) for xr in x_rot_data) / len(x_rot_data)
    yr_avg = sum(abs(yr) for yr in y_rot_data) / len(y_rot_data)
    zr_avg = sum(abs(zr) for zr in z_rot_data) / len(z_rot_data)

    averages = [x_avg, y_neg_avg, y_pos_avg, z_neg_avg, z_pos_avg, xr_avg, yr_avg, zr_avg]

    max_avg = max(averages)
    print("Averages:", averages)
    return averages.index(max_avg)

dominant_motion = determine_motion()
print(dominant_motion)


# Determine the dimension based on the result

def dimension():
    if dominant_motion == 0:
        return "environmental"
    elif dominant_motion == 1:
        return "emotional"
    elif dominant_motion == 2:
        return "physical"
    elif dominant_motion == 3:
        return "financial"
    elif dominant_motion == 4:
        return 'spiritual'
    elif dominant_motion == 5:
        return 'intelectual'
    elif dominant_motion == 6:
        return 'social'
    elif dominant_motion == 7:
        return 'occupational'
print(dimension())


dimension()

print("Pseudorandom Index:", result)


