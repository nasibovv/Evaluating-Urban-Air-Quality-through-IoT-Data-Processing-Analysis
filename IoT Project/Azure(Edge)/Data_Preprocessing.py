import paho.mqtt.client as mqtt
import json
from datetime import datetime
import pika
import time

time.sleep(15)
print("Ready")

# RabbitMQ configuration
rabbitmq_host = "192.168.0.100"
rabbitmq_port = 5672
rabbitmq_queue = "pm25_averaged_data"
rabbitmq_credentials = pika.PlainCredentials('admin', 'admin')

broker_address = "192.168.0.102"
channel_name = "pm25_filtered_data"

# Store readings with timestamps for 24 hours
pm25_data_24hrs = []


def on_message(client, userdata, message):
    global pm25_data_24hrs
    try:
        payload = json.loads(message.payload)
        pm25_value = payload.get("Value")
        timestamp = payload.get("Timestamp")

        # Handle missing data
        if pm25_value is None or timestamp is None:
            print("Error: Missing PM2.5 value or Timestamp in the data")
            return

        # (a) Print the PM2.5 data
        timestamp_dt = datetime.fromtimestamp(timestamp / 1000)
        timestamp_last = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
        print(f"Received PM2.5 data: Timestamp: {timestamp_last}, Value:{pm25_value}")

        # (b) Filter out outliers
        if pm25_value > 50:
            print(f"Outlier detected: Timestamp: {timestamp_last}, Value:{pm25_value}")
            return

        pm25_data_24hrs.append((timestamp, pm25_value))

        # (c) Calculate average every 24 hours
        current_time = datetime.utcfromtimestamp(timestamp / 1000)
        first_data_time = datetime.utcfromtimestamp(pm25_data_24hrs[0][0] / 1000)

        # Check if more than 24 hours have passed or if the day has changed
        if current_time.date() > first_data_time.date():
            prev_date = first_data_time.date()
            valid_data = [val for ts, val in pm25_data_24hrs if
                          datetime.utcfromtimestamp(ts / 1000).date() == prev_date]

            # Calculate average based on actual count of valid readings
            avg_value = sum(valid_data) / len(valid_data)
            print(f"-------------------------------------------------- ")
            print(f"Daily Average - Timestamp: {prev_date}, Value: {avg_value}")
            print(f"-------------------------------------------------- ")

            # (d) Transfer result to RabbitMQ
            transfer_to_rabbitmq(first_data_time, avg_value)

            # Retain data for the current day and remove processed data
            pm25_data_24hrs = [(ts, val) for ts, val in pm25_data_24hrs if
                               datetime.utcfromtimestamp(ts / 1000).date() == current_time.date()]

    except Exception as e:
        print(f"Error processing message: {e}")


def transfer_to_rabbitmq(timestamp_dt, avg_value):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(rabbitmq_host, rabbitmq_port, '/', rabbitmq_credentials))
    channel = connection.channel()

    channel.queue_declare(queue=rabbitmq_queue, durable=True)
    timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
    body = json.dumps({"Timestamp": timestamp_str, "Value": avg_value})
    channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=body)

    print(f"-------------------------------------------------- ")
    print(f"Sent to RabbitMQ: {body}")
    print(f"-------------------------------------------------- ")

    connection.close()


client = mqtt.Client(protocol=mqtt.MQTTv311)
client.on_message = on_message
client.connect(broker_address)
client.subscribe(channel_name)
client.loop_forever()

# Keep the script running
try:
    while True:
        pass
except KeyboardInterrupt:
    pass

# Disconnect from MQTT
client.disconnect()
