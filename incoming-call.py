    import socket
    import subprocess
    import os

    # Replace with your Asterisk Manager credentials
    username = 'admin'
    password = 'pass'
    asterisk_server_ip = '127.0.0.1'
    NODE = 'NODE#'

    def generate_audio_message(digits):
        # Path to the Asterisk audio files
        audio_path = '/var/lib/asterisk/sounds/'

        # List of audio file paths
        audio_files = [audio_path + 'rpt/node.gsm'] + [audio_path + 'digits/{}.gsm'.format(digit) for digit in digits] + [audio_path + 'rpt/connected.gsm']

        # Run the Asterisk command to concatenate audio files
        try:
            with open('/tmp/incoming-call.gsm', 'wb') as outfile:
                subprocess.run(['cat'] + audio_files, stdout=outfile, check=True)
            print("Audio file generated: /tmp/incoming-call.gsm")
        except subprocess.CalledProcessError as e:
            print("Error generating audio file: {}".format(e))



    def connect_to_asterisk_manager(username, password, server_ip, server_port=5038):
        try:
            # Connect to the Asterisk Manager Interface
            connection = socket.create_connection((server_ip, server_port))
            connection.setblocking(True)  # Set the socket to blocking mode

            # Read the initial connection response
            response = connection.recv(4096).decode('utf-8')

            if "Asterisk Call Manager" in response:
                # Send login command
                login_command = "Action: Login\r\nUsername: {}\r\nSecret: {}\r\n\r\n".format(username, password)
                connection.sendall(login_command.encode('utf-8'))

                # Read the login response
                login_response = connection.recv(4096).decode('utf-8')

                if "Authentication accepted" in login_response:
                    return connection

        except Exception as e:
            print("Error connecting to Asterisk Manager Interface: {}".format(e))
            return None

    def monitor_messages(connection):
        try:
            while True:
                # Read and print the response
                response = connection.recv(4096).decode('utf-8')
                if not response:
                    # If the response is empty, the connection may have been closed
                    break

                # Check if the response contains the specified pattern
                if "Event: Newchannel" in response and "State: Ring" in response:
                    # Extract and print the CallerIDNum from the matching event
                    caller_id_num = response.split('\n')[4].split(': ')[1].strip()

                    print("Newchannel State: Ring - CallerIDNum: {}".format(caller_id_num))

                    # Call the function to generate audio message based on CallerIDNum
                    digits = list(caller_id_num)
                    print("Digits before audio generation:", digits)
                    generate_audio_message(digits)
                    print("Generated audio")

                    # Run the Asterisk command using os.system
                    asterisk_command = "asterisk -rx 'rpt localplay {} /tmp/incoming-call'".format(NODE)
                    os.system(asterisk_command)
                    print("Asterisk command executed: {}".format(asterisk_command.strip()))
                    
        except KeyboardInterrupt:
            print("Monitoring interrupted by user.")
        except Exception as e:
            print("Error monitoring Asterisk Manager Interface: {}".format(e))

    def send_command(command):
        try:
            # Run the command using subprocess
            subprocess.run(command, shell=True)
            print("Command executed: {}".format(command.strip()))
        except Exception as e:
            print("Error executing command: {}".format(e))

    def perform_task(connection, message):
        if "Event: Newchannel" in message and "State: Ring" in message:
            # Extract the CallerIDNum from the matching event
            caller_id_num = message.split('\n')[4].split(': ')[1]
            print("Newchannel State: Ring - CallerIDNum: {}".format(caller_id_num))

            # Generate the audio message based on the CallerIDNum
            digits = list(caller_id_num)
            print("Digits before audio generation:", digits)
            generate_audio_message(digits)

            # Run the Asterisk command
            asterisk_command = "asterisk -rx 'rpt localplay $NODE1 /tmp/incoming-call'"
            send_command(connection, asterisk_command)


    def main():
        connection = connect_to_asterisk_manager(username, password, asterisk_server_ip)

        if connection:
            print("Connected to Asterisk Manager Interface.")

            # Start monitoring messages
            monitor_messages(connection)

            # The script will keep running until interrupted by the user
            connection.close()
            print("Disconnected.")


    if __name__ == "__main__":
        main()
