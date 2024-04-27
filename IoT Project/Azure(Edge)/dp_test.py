import requests
import json
import paho.mqtt.client as mqtt
from datetime import datetime

print(f"Data Collection and Injection Process has started: ")
print(f"-------------------------------------------------- ")

url = "https://newcastle.urbanobservatory.ac.uk/api/v1.1/sensors/PER_AIRMON_MONITOR1135100/data/json/?starttime=20230601&endtime=20230831"
resp = requests.get(url)


if resp.status_code == 200:
    raw_data_dict = resp.json()
    pm25_data = raw_data_dict['sensors'][0]['data']['PM2.5']

    client = mqtt.Client()
    client.connect("192.168.0.102", 1883)

    for entry in pm25_data:
        timestamp = entry['Timestamp']
        value = entry['Value']

        timestamp_dt = datetime.fromtimestamp(timestamp / 1000)
        timestamp_last = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')

        if value > 50:
            print(f"Outlier - Timestamp: {timestamp_last}, Value: {value}")

        else:
            data = {'Timestamp': timestamp, 'Value': value}
            msg = json.dumps(data)

            print(msg)
            client.publish("pm25_filtered_data", msg)
            print(f"Sent PM2.5 data - Timestamp: {timestamp_last}, Value: {value}")



    client.disconnect()

    print(f"-------------------------------------------------- ")
    print(f"Data Collection and Injection Process has successfully finished! ")

else:
    print(f"Failed to retrieve data. Status code: {resp.status_code}")
