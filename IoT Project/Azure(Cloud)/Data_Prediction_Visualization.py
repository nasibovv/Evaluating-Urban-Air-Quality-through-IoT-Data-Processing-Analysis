import pika
import matplotlib.pyplot as plt
import json
import pandas as pd
import time
from ml_engine import MLPredictor


class PM25Collector:

    def __init__(self):
        self.pm25_data = []

    def collect(self):
        credentials = pika.PlainCredentials('admin', 'admin')
        connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.0.100', credentials=credentials, socket_timeout=20))
        channel = connection.channel()
        channel.queue_declare(queue='pm25_averaged_data', durable=True)

        channel.basic_consume(queue='pm25_averaged_data', on_message_callback=self.callback, auto_ack=True)

        print('Waiting for PM2.5 averaged data. To exit, press Ctrl+C')
        start_time = time.time()

        try:
            while time.time() - start_time < 10:
                connection.process_data_events()
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            connection.close()

    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf8'))
            timestamp = message.get('Timestamp')
            value = message.get('Value')

            if value is not None:
                self.pm25_data.append((timestamp, float(value)))
                print(f"Received PM2.5 Data: {timestamp}, {value}")
            else:
                print(f"Error: 'Value' field not found in the message or not a valid number")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON message: {str(e)}")
        except ValueError as e:
            print(f"Error converting 'Value' to float: {str(e)}")


class PM25Visualizer:

    @staticmethod
    def plot_data(pm25_data):
        timestamps, values = zip(*pm25_data)
        plt.plot(timestamps, values, color="#FF3B1D", marker=".", linestyle="-")
        plt.xlabel('Timestamp')
        plt.ylabel('PM2.5 Value')
        plt.title('Averaged Daily PM2.5 Data')
        plt.xticks(rotation=90)
        plt.show()

    @staticmethod
    def plot_predicted(predictor, predicted_data):
        if predicted_data is not None:
            fig = predictor.plot_result(predicted_data)
            plt.show()


if __name__ == '__main__':
    collector = PM25Collector()
    collector.collect()

    if collector.pm25_data:
        PM25Visualizer.plot_data(collector.pm25_data)

        data_df = pd.DataFrame(collector.pm25_data, columns=["Timestamp", "Value"])

        predictor = MLPredictor(data_df)
        predictor.train()
        predicted_data = predictor.predict()

        PM25Visualizer.plot_predicted(predictor, predicted_data)
